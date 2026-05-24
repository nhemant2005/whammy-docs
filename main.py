import json
import os
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from scanner import scan
from generator import stream_readme

app = FastAPI(title="WhammyDocs")
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

    (session_dir / "session.json").write_text(
        json.dumps({"session_id": session_id, "mode": mode})
    )

    scan(session_dir)

    return RedirectResponse(url=f"/generate/{session_id}", status_code=303)


@app.get("/generate/{session_id}", response_class=HTMLResponse)
async def generate_page(request: Request, session_id: str):
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    if not session_dir.exists():
        return HTMLResponse("Session not found", status_code=404)
    return templates.TemplateResponse(
        request, "generate.html", {"session_id": session_id}
    )


@app.get("/stream/{session_id}")
async def stream(session_id: str):
    session_dir = _tmp_dir() / f"whammy-{session_id}"
    if not session_dir.exists():
        return HTMLResponse("Session not found", status_code=404)

    async def event_generator():
        async for token in stream_readme(session_dir):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
