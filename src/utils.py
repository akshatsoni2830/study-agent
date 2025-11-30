from __future__ import annotations

import os
import re
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\-\s_]+", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value or "subject"


def print_progress(msg: str) -> None:
    print(f"[Study Agent] {msg}")


def extract_folder_id(input_str: str) -> str:
    """
    Accept either a plain folder ID or a full Google Drive URL.
    Examples:
    - '1Un2ZAmsO1aoVPOt674jn0-DGsH2vB9g_'
    - 'https://drive.google.com/drive/folders/1Un2ZAmsO1aoVPOt674jn0-DGsH2vB9g_?usp=sharing'
    - 'https://drive.google.com/drive/u/0/mobile/folders/1Un2ZAmsO1aoVPOt674jn0-DGsH2vB9g_?usp=sharing'
    Return the folder ID or raise ValueError if not found.
    """
    s = input_str.strip()
    if not s:
        raise ValueError("Empty input")
    if "http" not in s:
        return s
    m = re.search(r"/folders/([a-zA-Z0-9_-]+)", s)
    if m:
        return m.group(1)
    # Fallback to ?id= param if present
    m2 = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", s)
    if m2:
        return m2.group(1)
    raise ValueError("Could not extract folder ID from URL")
