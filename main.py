import io
import json
import os
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates

from scanner import scan
from generator import stream_readme, stream_all_sections, stream_one_section

_QUICK_SECTION_KEYS = ["readme", "api_reference"]
_COMPREHENSIVE_SECTION_KEYS = [
    "readme", "api_reference", "architecture", "getting_started", "deployment"
]
_SECTION_TITLES = {
    "readme": "README",
    "api_reference": "API Reference",
    "architecture": "Architecture",
    "getting_started": "Getting Started",
    "deployment": "Deployment",
}
_MKDOCS_NAV_TITLES = {
    "readme": "README",
    "api_reference": "API Reference",
    "architecture": "Architecture",
    "getting_started": "Getting Started",
    "deployment": "Deployment",
}

app = FastAPI(title="WhammyDocs")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

_50MB = 50 * 1024 * 1024


def _tmp_dir() -> Path:
    return Path(os.environ.get("WHAMMY_TMP_DIR", tempfile.gettempdir()))


def _error(request: Request, message: str):
    return templates.TemplateResponse(request, "upload.html", {"error": message})


@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse(request, "upload.html")


@app.post("/upload")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    mode: str = Form("comprehensive"),
):
    if not file.filename.endswith(".zip"):
        return _error(request, "Only .zip files are accepted.")

    content = await file.read()

    if len(content) > _50MB:
        return _error(request, "File must be under 50 MB.")

    session_id = str(uuid.uuid4())
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        import io
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            zf.extractall(session_dir)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, Exception) as exc:
        session_dir.rmdir()
        return _error(request, f"Could not read zip file: {exc}")

    project_name = Path(file.filename).stem
    (session_dir / "session.json").write_text(
        json.dumps({"session_id": session_id, "mode": mode, "project_name": project_name})
    )

    scan(session_dir)

    return RedirectResponse(url=f"/preview/{session_id}", status_code=303)


@app.post("/upload-sample")
async def upload_sample():
    sample_dir = Path(__file__).parent / "samples" / "todo-app"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sample_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(sample_dir).as_posix())
    buf.seek(0)

    session_id = str(uuid.uuid4())
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(buf) as zf:
        zf.extractall(session_dir)

    (session_dir / "session.json").write_text(
        json.dumps({"session_id": session_id, "mode": "comprehensive", "project_name": "todo-app"})
    )

    scan(session_dir)

    return RedirectResponse(url=f"/preview/{session_id}", status_code=303)


@app.get("/generate/{session_id}", response_class=HTMLResponse)
async def generate_page(request: Request, session_id: str):
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    if not session_dir.exists():
        return HTMLResponse("Session not found", status_code=404)
    session_data = json.loads((session_dir / "session.json").read_text())
    mode = session_data.get("mode", "comprehensive")
    return templates.TemplateResponse(
        request, "generate.html", {"session_id": session_id, "mode": mode}
    )


@app.get("/stream/{session_id}")
async def stream(session_id: str):
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    if not session_dir.exists():
        return HTMLResponse("Session not found", status_code=404)

    async def event_generator():
        async for event_type, data in stream_all_sections(session_dir):
            if event_type == "message":
                yield f"data: {json.dumps(data)}\n\n"
            else:
                yield f"event: {event_type}\ndata: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/preview/{session_id}", response_class=HTMLResponse)
async def preview_page(request: Request, session_id: str):
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    if not session_dir.exists():
        return HTMLResponse("Session not found", status_code=404)

    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    mode = session.get("mode", "comprehensive")
    section_keys = _QUICK_SECTION_KEYS if mode == "quick" else _COMPREHENSIVE_SECTION_KEYS

    docs_dir = session_dir / "docs"
    generating = not docs_dir.exists() or not any(docs_dir.glob("*.md"))

    sections = []
    for key in section_keys:
        content = ""
        if not generating:
            doc_file = docs_dir / f"{key}.md"
            if doc_file.exists():
                content = doc_file.read_text(encoding="utf-8")
        sections.append({
            "key": key,
            "id": f"section-{key.replace('_', '-')}",
            "title": _SECTION_TITLES[key],
            "content": content,
        })

    return templates.TemplateResponse(
        request, "preview.html", {
            "session_id": session_id,
            "sections": sections,
            "mode": mode,
            "generating": generating,
        }
    )


class _EditRequest(BaseModel):
    session_id: str
    section: str
    content: str


@app.post("/edit")
async def edit_section(body: _EditRequest):
    session_dir = _tmp_dir() / f"whammy-{body.session_id}"
    if not session_dir.exists():
        return HTMLResponse("Session not found", status_code=404)

    doc_file = session_dir / "docs" / f"{body.section}.md"
    doc_file.write_text(body.content, encoding="utf-8")

    session_path = session_dir / "session.json"
    session = json.loads(session_path.read_text(encoding="utf-8"))
    edited = session.get("edited", {})
    edited[body.section] = True
    session["edited"] = edited
    session_path.write_text(json.dumps(session), encoding="utf-8")

    return Response(status_code=200)


@app.get("/regenerate/{session_id}/{section_key}")
async def regenerate_section(session_id: str, section_key: str, feedback: str = Query(default="")):
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    if not session_dir.exists():
        return HTMLResponse("Session not found", status_code=404)

    async def event_generator():
        async for event_type, data in stream_one_section(session_dir, section_key, feedback=feedback):
            if event_type == "message":
                yield f"data: {json.dumps(data)}\n\n"
            else:
                yield f"event: {event_type}\ndata: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/download/{session_id}")
async def download(session_id: str):
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    if not session_dir.exists():
        return HTMLResponse("Session not found", status_code=404)

    docs_dir = session_dir / "docs"
    site_dir = session_dir / "site"

    session = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    project_name = session.get("project_name", "project")

    # Guard: no docs generated yet
    generated_docs = list(docs_dir.glob("*.md")) if docs_dir.exists() else []
    if not generated_docs:
        return HTMLResponse("No documentation generated yet. Complete generation first.", status_code=400)

    # Copy readme.md → index.md so MkDocs produces a root index.html
    readme = docs_dir / "readme.md"
    index_md = docs_dir / "index.md"
    if readme.exists():
        index_md.write_text(readme.read_text(encoding="utf-8"), encoding="utf-8")

    # Build nav: home page first, then remaining sections
    nav_entries = ["  - Home: index.md"]
    for key in _COMPREHENSIVE_SECTION_KEYS:
        if key == "readme":
            continue
        doc_file = docs_dir / f"{key}.md"
        if doc_file.exists():
            nav_entries.append(f"  - {_MKDOCS_NAV_TITLES[key]}: {key}.md")

    mkdocs_yml = session_dir / "mkdocs.yml"
    mkdocs_yml.write_text(
        "site_name: Project Documentation\n"
        "theme:\n  name: material\n"
        f"docs_dir: {docs_dir.as_posix()}\n"
        f"site_dir: {site_dir.as_posix()}\n"
        "nav:\n" + "\n".join(nav_entries) + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--config-file", str(mkdocs_yml)],
        capture_output=True,
        check=False,
    )

    # Zip site/ + docs/*.md
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if site_dir.exists():
            for f in site_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f"site/{f.relative_to(site_dir).as_posix()}")
        for f in docs_dir.glob("*.md"):
            zf.write(f, f"docs/{f.name}")
    buf.seek(0)

    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=Documentation-{project_name}.zip"},
    )
