from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auth import get_drive_service
from .config import get_defaults
from .drive_client import (
    MIME_GOOGLE_DOC,
    MIME_PDF,
    download_pdf,
    export_google_doc_as_text,
    list_study_files,
)
from .gemini_client import GeminiClient
from .summarizer import merge_file_summaries
from .utils import ensure_dir, slugify, extract_folder_id


class SummarizeFolderRequest(BaseModel):
    folderId: str = Field(..., description="Google Drive folder ID")
    subjectName: str = Field(..., description="Subject name for the merged summary")
    semester: Optional[str] = Field(None, description="Optional semester label")


defaults = get_defaults()
OUTPUT_DIR: Path = defaults["output_dir"]  # type: ignore[assignment]
ensure_dir(OUTPUT_DIR)

app = FastAPI(title="Study Agent API", version="1.0.0")

# CORS: allow all origins for simplicity so Chrome extension can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve output directory so the extension can link to generated files
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/summarize-folder")
async def summarize_folder(req: SummarizeFolderRequest):
    subject_name = req.subjectName.strip()
    folder_id_raw = req.folderId.strip()
    semester = (req.semester or "").strip()

    if not subject_name:
        raise HTTPException(status_code=400, detail="subjectName is required")
    if not folder_id_raw:
        raise HTTPException(status_code=400, detail="folderId is required")
    try:
        folder_id = extract_folder_id(folder_id_raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid folderId or URL")

    try:
        service = get_drive_service()
        files = list_study_files(service, folder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drive error: {e}")

    if not files:
        return {"status": "empty", "message": "No supported files in folder", "filesProcessed": 0}

    gemini = GeminiClient()

    summaries: List[Tuple[str, str]] = []
    errors: List[str] = []

    for f in files:
        name = f.get("name", f.get("id", "file"))
        mime = f.get("mimeType", "")
        fid = f.get("id")
        if not fid:
            errors.append(f"Missing file ID for {name}")
            continue
        try:
            if mime == MIME_PDF:
                pdf_bytes = download_pdf(service, fid)
                summary = gemini.summarize_pdf_bytes(pdf_bytes, name)
            elif mime == MIME_GOOGLE_DOC:
                text = export_google_doc_as_text(service, fid)
                if not text.strip():
                    errors.append(f"Empty export for {name}")
                    continue
                summary = gemini.summarize_plain_text(text, name)
            else:
                # skip unsupported
                continue
            summaries.append((name, summary))
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue

    if not summaries:
        return {
            "status": "failed",
            "message": "No summaries produced",
            "filesProcessed": 0,
            "errors": errors,
        }

    # Build output name
    base = slugify(subject_name)
    if semester:
        base = f"{base}_{slugify(semester)}"
    out_name = f"{base}_summary.md"
    out_path = OUTPUT_DIR / out_name

    try:
        merged = merge_file_summaries(subject_name, summaries, semester=semester)
        out_path.write_text(merged, encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save summary: {e}")

    return {
        "status": "ok",
        "filesProcessed": len(summaries),
        "summary_file": out_name,
        "summary_url": f"/output/{out_name}",
        "errors": errors,
    }
