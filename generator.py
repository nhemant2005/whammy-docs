"""DeepSeek streaming client — generates README markdown via SSE."""
import json
import os
from pathlib import Path
from typing import AsyncIterator

import httpx
from dotenv import load_dotenv

load_dotenv()

_DEEPSEEK_BASE = "https://api.deepseek.com/v1"
_MODEL = "deepseek-chat"

_README_SYSTEM = (
    "You are a technical writer. Generate a clear, well-structured README.md "
    "in Markdown for the project described below. Include: project overview, "
    "features, installation, usage, and configuration. Be concise."
)


def _build_prompt(files_content: str, tree: str) -> str:
    parts = []
    if tree:
        parts.append(f"## Directory structure\n```\n{tree}\n```")
    if files_content:
        parts.append(f"## Source files\n{files_content}")
    parts.append("Generate the README.md now.")
    return "\n\n".join(parts)


def _read_files(session_dir: Path, rel_paths: list[str]) -> str:
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
                    {"role": "system", "content": _README_SYSTEM},
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
