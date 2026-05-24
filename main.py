import json
import os
import tempfile
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from scanner import scan

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
