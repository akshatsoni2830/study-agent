from __future__ import annotations

import sys
from datetime import datetime
from typing import List, Tuple

from .auth import get_drive_service
from .config import get_defaults
from .drive_client import (
    MIME_GOOGLE_DOC,
    MIME_GOOGLE_SLIDES,
    MIME_PDF,
    MIME_PPTX,
    MIME_PPT,
    collect_files_recursively,
    download_pdf,
    export_google_doc_as_text,
    export_google_slides_as_text,
    export_google_slides_as_pdf,
    extract_pptx_text,
    get_folder_name,
    list_subfolders,
)
from .gemini_client import GeminiClient
from .summarizer import merge_file_summaries
from .utils import extract_folder_id, ensure_dir, print_progress, slugify


def _input(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def interactive_folder_navigation(service, root_folder_id: str) -> str:
    """
    Let the user navigate through folders starting from root_folder_id.
    Simple downward-only navigation; user chooses 'here' to select current folder.
    Return the selected folder ID.
    """
    current_id = root_folder_id
    while True:
        try:
            current_name = get_folder_name(service, current_id)
        except Exception:
            current_name = current_id
        print_progress(f"In folder: {current_name}")

        subs = list_subfolders(service, current_id)
        if not subs:
            print_progress("No subfolders. Type 'here' to summarize this folder, or 'exit' to quit.")
        else:
            print("Subfolders:")
            for i, f in enumerate(subs, start=1):
                print(f"  {i}. {f.get('name')}")
            print("Type a number to open a subfolder, 'here' to summarize current folder, or 'exit' to quit.")

        choice = _input("> ").strip().lower()
        if choice == "exit":
            raise SystemExit(0)
        if choice == "here":
            return current_id
        if subs:
            try:
                idx = int(choice)
                if 1 <= idx <= len(subs):
                    current_id = subs[idx - 1]["id"]
                    continue
            except Exception:
                pass
        print_progress("Invalid choice. Please try again.")


def main() -> int:
    defaults = get_defaults()
    output_dir = defaults["output_dir"]
    ensure_dir(output_dir)

    print_progress("Authorizing with Google Drive...")
    service = get_drive_service()

    # Determine root folder from env or prompt
    env_root_id = (defaults.get("root_study_folder_id") or "").strip()
    env_root_url = (defaults.get("root_study_folder_url") or "").strip()
    root_folder_id = ""
    if env_root_id:
        root_folder_id = env_root_id
    elif env_root_url:
        try:
            root_folder_id = extract_folder_id(env_root_url)
        except Exception as e:
            print_progress(f"Failed to parse ROOT_STUDY_FOLDER_URL: {e}")
    while not root_folder_id:
        raw = _input("Enter ROOT Study Folder ID or URL: ")
        try:
            root_folder_id = extract_folder_id(raw)
        except Exception as e:
            print_progress(f"Could not parse: {e}")

    # Subject and semester inputs
    subject_name = _input("Enter Subject Name: ").strip()
    while not subject_name:
        subject_name = _input("Subject Name is required. Enter Subject Name: ").strip()
    semester = _input("Enter Semester (e.g., Sem 3) [optional]: ").strip()

    # Navigate to target folder
    target_folder_id = interactive_folder_navigation(service, root_folder_id)

    # Collect and summarize
    print_progress("Collecting files recursively...")
    try:
        files = collect_files_recursively(service, target_folder_id)
    except Exception as e:
        print_progress(f"Failed to list files: {e}")
        return 1
    if not files:
        print_progress("No supported files found in the selected folder.")
        return 0

    print_progress(f"Found {len(files)} files. Summarizing with Gemini...")
    gemini = GeminiClient()
    summaries: List[Tuple[str, str]] = []
    for idx, f in enumerate(files, start=1):
        name = f.get("name", f.get("id", "file"))
        mime = f.get("mimeType", "")
        fid = f.get("id")
        print_progress(f"[{idx}/{len(files)}] {name}")
        if not fid:
            continue
        try:
            if mime == MIME_PDF:
                pdf_bytes = download_pdf(service, fid)
                summary = gemini.summarize_pdf_bytes(pdf_bytes, name)
            elif mime == MIME_GOOGLE_DOC:
                text = export_google_doc_as_text(service, fid)
                if not text.strip():
                    continue
                summary = gemini.summarize_plain_text(text, name)
            elif mime == MIME_GOOGLE_SLIDES:
                # Prefer text export for concise summaries; fallback to PDF if needed
                text = export_google_slides_as_text(service, fid)
                if text and text.strip():
                    summary = gemini.summarize_plain_text(text, name)
                else:
                    pdf_bytes = export_google_slides_as_pdf(service, fid)
                    summary = gemini.summarize_pdf_bytes(pdf_bytes, name)
            elif mime == MIME_PPTX:
                text = extract_pptx_text(service, fid)
                if not text.strip():
                    continue
                summary = gemini.summarize_plain_text(text, name)
            elif mime == MIME_PPT:
                print_progress("  Skipping legacy .ppt file. Please convert to Google Slides or .pptx for best results.")
                continue
            else:
                continue
            summaries.append((name, summary))
        except Exception as e:
            print_progress(f"  Error: {e}")
            continue

    if not summaries:
        print_progress("No summaries produced.")
        return 0

    merged = merge_file_summaries(subject_name, summaries, semester=semester or None)
    subject_slug = slugify(subject_name)
    folder_name = get_folder_name(service, target_folder_id)
    folder_slug = slugify(folder_name)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Build per-subject[/semester]/folder/timestamp directory
    run_dir = output_dir / subject_slug
    if semester:
        run_dir = run_dir / slugify(semester)
    run_dir = run_dir / folder_slug / ts
    ensure_dir(run_dir)
    out_path = run_dir / "summary.md"
    out_path.write_text(merged, encoding="utf-8")
    print_progress(f"Done. Summary saved to: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
