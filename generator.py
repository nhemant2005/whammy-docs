"""DeepSeek streaming client — generates documentation sections via SSE."""
import json
import os
import re
from pathlib import Path
from typing import AsyncIterator

import httpx
from dotenv import load_dotenv

load_dotenv()

_DEEPSEEK_BASE = "https://api.deepseek.com/v1"
_MODEL = "deepseek-chat"

# ---------------------------------------------------------------------------
# Section configuration
# ---------------------------------------------------------------------------

_SECTION_CONFIGS = {
    "readme": {
        "title": "README",
        "system": (
            "You are a technical writer. Generate a clear, well-structured README.md "
            "in Markdown for the project described below. Include: project overview, "
            "features, installation, usage, and configuration. Be concise."
        ),
        "file_keys": ["readme", "getting_started"],
        "use_tree": True,
    },
    "api_reference": {
        "title": "API Reference",
        "system": (
            "You are a technical writer. Generate comprehensive API reference documentation "
            "in Markdown for the source files below. Document every public function, class, "
            "and endpoint: parameters, return types, and a one-line description. Be precise."
        ),
        "file_keys": ["api_reference"],
        "use_tree": False,
    },
    "architecture": {
        "title": "Architecture",
        "system": (
            "You are a software architect. Generate an architecture overview document "
            "in Markdown that explains the high-level design, key components, data flow, "
            "and technology choices for the project described below."
        ),
        "file_keys": ["readme"],
        "use_tree": True,
    },
    "getting_started": {
        "title": "Getting Started",
        "system": (
            "You are a technical writer. Generate a Getting Started guide in Markdown. "
            "Cover prerequisites, installation, environment setup, and running the project "
            "for the first time. Use numbered steps. Be beginner-friendly."
        ),
        "file_keys": ["getting_started"],
        "use_tree": False,
    },
    "deployment": {
        "title": "Deployment",
        "system": (
            "You are a DevOps engineer. Generate a deployment guide in Markdown. "
            "Cover building, containerisation, CI/CD, and production environment setup "
            "based on the configuration files below."
        ),
        "file_keys": ["deployment"],
        "use_tree": False,
    },
}

_QUICK_SECTIONS = ["readme", "api_reference"]
_COMPREHENSIVE_SECTIONS = [
    "readme",
    "api_reference",
    "architecture",
    "getting_started",
    "deployment",
]

# ---------------------------------------------------------------------------
# Skeleton extraction
# ---------------------------------------------------------------------------

_5KB = 5 * 1024
_20KB = 20 * 1024


def _skeleton(text: str, path: str) -> str:
    """Return a size-appropriate representation of file content."""
    size = len(text.encode("utf-8"))
    if size < _5KB:
        return text
    if size > _20KB:
        return "\n".join(text.splitlines()[:30])
    return _extract_signatures(text, path)


def _extract_signatures(text: str, path: str) -> str:
    """Extract function/class signatures from medium-sized files."""
    suffix = Path(path).suffix.lower()
    lines = text.splitlines()

    if suffix == ".py":
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                result.append(line)
                # Include docstring on the next line if present
                if i + 1 < len(lines):
                    nxt = lines[i + 1].strip()
                    if nxt.startswith('"""') or nxt.startswith("'''"):
                        result.append(lines[i + 1])
            i += 1
        return "\n".join(result) if result else "\n".join(lines[:50])

    # For all other languages: non-indented lines (likely declarations)
    sig_pattern = re.compile(
        r"^\s*(function|class|def |interface |struct |fn |func |public |private |protected |export )",
    )
    result = [l for l in lines if sig_pattern.match(l)]
    return "\n".join(result) if result else "\n".join(lines[:50])


# ---------------------------------------------------------------------------
# File reading helpers
# ---------------------------------------------------------------------------


def _read_files(session_dir: Path, rel_paths: list[str]) -> str:
    """Read files verbatim (used by legacy stream_readme)."""
    chunks = []
    for rel in rel_paths:
        path = session_dir / rel
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
                chunks.append(f"### {rel}\n```\n{text}\n```")
            except (UnicodeDecodeError, PermissionError):
                pass
    return "\n\n".join(chunks)


def _read_files_with_skeleton(session_dir: Path, rel_paths: list[str]) -> str:
    """Read files with size-appropriate skeleton extraction."""
    chunks = []
    for rel in rel_paths:
        path = session_dir / rel
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
                content = _skeleton(text, rel)
                chunks.append(f"### {rel}\n```\n{content}\n```")
            except (UnicodeDecodeError, PermissionError):
                pass
    return "\n\n".join(chunks)


def _build_prompt(files_content: str, tree: str, feedback: str = "") -> str:
    parts = []
    if tree:
        parts.append(f"## Directory structure\n```\n{tree}\n```")
    if files_content:
        parts.append(f"## Source files\n{files_content}")
    parts.append("Generate the documentation now.")
    if feedback:
        parts.append(f"Additional instructions: {feedback}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# DeepSeek streaming — single section
# ---------------------------------------------------------------------------


async def _stream_section(system: str, prompt: str) -> AsyncIterator[str]:
    """Yield text tokens from DeepSeek for one section."""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{_DEEPSEEK_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": True,
            },
            timeout=120.0,
        ) as response:
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass


# ---------------------------------------------------------------------------
# Multi-section pipeline (Issue 5)
# ---------------------------------------------------------------------------


async def stream_all_sections(session_dir: Path) -> AsyncIterator[tuple[str, str]]:
    """
    Yield (event_type, data) tuples for all doc sections.

    event_type values:
      "section-start"    — before each section (data = section key)
      "message"          — a markdown token (data = text)
      "section-complete" — after each section (data = section key)
      "gen-error"        — DeepSeek failure (data = error message)
      "done"             — all sections finished (data = "")
    """
    session_dir = Path(session_dir)
    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    mode = session.get("mode", "comprehensive")
    sections = _QUICK_SECTIONS if mode == "quick" else _COMPREHENSIVE_SECTIONS

    mapping = json.loads((session_dir / "mapping.json").read_text(encoding="utf-8"))
    docs_dir = session_dir / "docs"
    docs_dir.mkdir(exist_ok=True)

    for section_key in sections:
        config = _SECTION_CONFIGS[section_key]
        yield ("section-start", section_key)

        all_files: list[str] = []
        for key in config["file_keys"]:
            all_files.extend(mapping.get(key, []))
        all_files = list(dict.fromkeys(all_files))

        files_content = _read_files_with_skeleton(session_dir, all_files)
        tree = mapping.get("architecture", "") if config["use_tree"] else ""
        prompt = _build_prompt(files_content, tree)

        generated: list[str] = []
        try:
            async for token in _stream_section(config["system"], prompt):
                yield ("message", token)
                generated.append(token)
        except Exception as exc:
            yield ("gen-error", str(exc))
            continue

        content = "".join(generated)
        (docs_dir / f"{section_key}.md").write_text(content, encoding="utf-8")
        yield ("section-complete", section_key)

    yield ("done", "")


# ---------------------------------------------------------------------------
# Single-section regenerate (Issue 8)
# ---------------------------------------------------------------------------


async def stream_one_section(
    session_dir: Path, section_key: str, feedback: str = ""
) -> AsyncIterator[tuple[str, str]]:
    """
    Yield (event_type, data) tuples for one doc section regeneration.

    event_type values:
      "message"  — a markdown token (unnamed SSE event)
      "done"     — regeneration finished, file written, edited flag cleared
      "gen-error" — DeepSeek failure
    """
    session_dir = Path(session_dir)
    config = _SECTION_CONFIGS[section_key]

    mapping = json.loads((session_dir / "mapping.json").read_text(encoding="utf-8"))
    docs_dir = session_dir / "docs"
    docs_dir.mkdir(exist_ok=True)

    all_files: list[str] = []
    for key in config["file_keys"]:
        all_files.extend(mapping.get(key, []))
    all_files = list(dict.fromkeys(all_files))

    files_content = _read_files_with_skeleton(session_dir, all_files)
    tree = mapping.get("architecture", "") if config["use_tree"] else ""
    prompt = _build_prompt(files_content, tree, feedback=feedback)

    generated: list[str] = []
    try:
        async for token in _stream_section(config["system"], prompt):
            yield ("message", token)
            generated.append(token)
    except Exception as exc:
        yield ("gen-error", str(exc))
        return

    content = "".join(generated)
    (docs_dir / f"{section_key}.md").write_text(content, encoding="utf-8")

    session_path = session_dir / "session.json"
    session = json.loads(session_path.read_text(encoding="utf-8"))
    edited = session.get("edited", {})
    edited.pop(section_key, None)
    session["edited"] = edited
    session_path.write_text(json.dumps(session), encoding="utf-8")

    yield ("done", "")


# ---------------------------------------------------------------------------
# Legacy — kept for backwards compat with Issue 4 tests
# ---------------------------------------------------------------------------


async def stream_readme(session_dir: Path) -> AsyncIterator[str]:
    """Yield README markdown tokens streamed from DeepSeek."""
    session_dir = Path(session_dir)
    mapping = json.loads((session_dir / "mapping.json").read_text(encoding="utf-8"))

    readme_files = mapping.get("readme", [])
    getting_started_files = mapping.get("getting_started", [])
    source_files = list(dict.fromkeys(readme_files + getting_started_files))

    files_content = _read_files(session_dir, source_files)
    tree = mapping.get("architecture", "")

    prompt = _build_prompt(files_content, tree)
    system = _SECTION_CONFIGS["readme"]["system"]

    async for token in _stream_section(system, prompt):
        yield token
