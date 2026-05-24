"""File scanner: walk a session directory and produce a section→file mapping."""
import json
from pathlib import Path, PurePosixPath

# Directories to skip entirely
_IGNORE_DIRS = {
    "node_modules", "__pycache__", ".git", "venv", "env",
    "dist", "build",
}

# File names and extensions to skip
_IGNORE_FILENAMES = {"package-lock.json", "yarn.lock", "Pipfile.lock"}
_IGNORE_EXTENSIONS = {".pyc", ".class", ".lock"}

# Section patterns (checked against forward-slash relative paths)
_API_DIRS = {"routes", "controllers", "api", "views"}
_API_STEMS = {"router", "endpoint", "handler"}

_GETTING_STARTED_NAMES = {
    "requirements.txt", "package.json", "Pipfile", "go.mod", "go.sum",
}

_DEPLOYMENT_NAMES = {"Dockerfile", "nginx.conf"}
_DEPLOYMENT_PREFIXES = {"docker-compose"}
_DEPLOYMENT_DIRS = {".github/workflows"}


def scan(session_dir: Path) -> dict:
    """
    Walk session_dir, apply ignore list, and map files to doc sections.
    Writes mapping.json inside session_dir and returns the mapping dict.
    """
    session_dir = Path(session_dir)
    source_files = _collect_files(session_dir)

    mapping: dict = {
        "api_reference": [],
        "getting_started": [],
        "deployment": [],
        "architecture": _build_tree(session_dir),
        "readme": [],
    }

    for rel in source_files:
        _classify(rel, mapping)

    (session_dir / "mapping.json").write_text(
        json.dumps(mapping, indent=2), encoding="utf-8"
    )
    return mapping


def _collect_files(root: Path) -> list[str]:
    """Return relative posix paths for all scannable files under root."""
    results = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        rel_posix = rel.as_posix()

        if _should_ignore(rel_posix, path):
            continue
        results.append(rel_posix)
    return results


def _should_ignore(rel_posix: str, path: Path) -> bool:
    parts = PurePosixPath(rel_posix).parts

    # Skip if any parent dir is in the ignore set
    for part in parts[:-1]:
        if part in _IGNORE_DIRS:
            return True

    name = parts[-1]
    if name in _IGNORE_FILENAMES:
        return True

    suffix = Path(name).suffix
    if suffix in _IGNORE_EXTENSIONS:
        return True

    # Skip binary / non-UTF-8 files
    try:
        path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return True

    return False


def _classify(rel: str, mapping: dict) -> None:
    parts = PurePosixPath(rel).parts
    name = parts[-1]
    stem = Path(name).stem.lower()

    # --- Deployment ---
    if name in _DEPLOYMENT_NAMES:
        mapping["deployment"].append(rel)
        return
    if any(name.startswith(p) for p in _DEPLOYMENT_PREFIXES):
        mapping["deployment"].append(rel)
        return
    # .github/workflows/* files
    if len(parts) >= 3 and parts[0] == ".github" and parts[1] == "workflows":
        mapping["deployment"].append(rel)
        return

    # --- Getting Started ---
    if name in _GETTING_STARTED_NAMES:
        mapping["getting_started"].append(rel)
        return
    if len(parts) == 1 and (name.startswith("README") or name.startswith("readme")):
        mapping["getting_started"].append(rel)
        return
    if name.endswith(".env.example"):
        mapping["getting_started"].append(rel)
        return

    # --- API Reference ---
    if parts[0] in _API_DIRS:
        mapping["api_reference"].append(rel)
        return
    if any(s in stem for s in _API_STEMS):
        mapping["api_reference"].append(rel)
        return

    # --- README (top-level entry points) ---
    if len(parts) == 1:
        mapping["readme"].append(rel)


def _build_tree(root: Path, prefix: str = "", _rel: str = "") -> str:
    """Return an indented directory tree string, skipping ignored dirs."""
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        return ""

    for entry in entries:
        rel_name = entry.name
        if entry.is_dir() and rel_name in _IGNORE_DIRS:
            continue
        lines.append(f"{prefix}{rel_name}{'/' if entry.is_dir() else ''}")
        if entry.is_dir():
            lines.append(_build_tree(entry, prefix + "  ", rel_name))

    return "\n".join(filter(None, lines))
