from __future__ import annotations

import base64
import time
from typing import Any, Dict, Optional

import requests

from .config import get_gemini_config

# Try v1 first, then v1beta as a fallback (accounts/keys may differ in availability)
API_ROOTS = [
    "https://generativelanguage.googleapis.com/v1",
    "https://generativelanguage.googleapis.com/v1beta",
]

PROMPT_TEMPLATE = (
    "You are a friendly senior student explaining this document to a younger sibling in 2nd-year CSE. "
    "Explain everything in SUPER SIMPLE language. Use analogies from daily life. Keep sentences short. "
    "Keep formulas EXACTLY as in the document. Provide a Markdown summary with these sections:\n"
    "# File: {file_name}\n"
    "## Overview\n"
    "## Key Concepts (explained like to a kid)\n"
    "## Definitions (very simple)\n"
    "## Formulas (copy exactly) + one-line meaning\n"
    "## Algorithms (short steps + when to use)\n"
    "## Examples and Intuition\n"
    "## Confusing Parts (say ‘Not clear from document’ if needed)\n"
    "In the Algorithms section: for each algorithm found, list a concise bullet with the NAME and WHEN to use it, add ONE kid-friendly analogy (<=1 line), then 2–4 SHORT step bullets. If the document contains pseudocode, include a tiny fenced code block (max 8 lines) copied EXACTLY.\n"
    "Do NOT invent new facts. Only use what is in the document."
)


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        cfg = get_gemini_config()
        self.api_key = api_key or cfg["api_key"]
        self.model = model_name or cfg["model"]
        self.session = requests.Session()

    def _generate(self, contents: Dict[str, Any], max_retries: int = 3) -> str:
        payload = {"contents": [contents]}
        backoff = 2
        last_err = None
        for root in API_ROOTS:
            url = f"{root}/models/{self.model}:generateContent?key={self.api_key}"
            for attempt in range(max_retries):
                resp = self.session.post(url, json=payload, timeout=90)
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        parts = data["candidates"][0]["content"]["parts"]
                        text = "".join(p.get("text", "") for p in parts)
                        if text.strip():
                            return text
                    except Exception:
                        pass
                    raise RuntimeError(f"Gemini returned unexpected response: {data}")
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                try:
                    last_err = resp.json()
                except Exception:
                    last_err = resp.text
                # break retry loop for this root on 4xx except 429
                if resp.status_code < 500 and resp.status_code != 429:
                    break
            # try next root if available
        raise RuntimeError(f"Gemini API error: {last_err}")

    def summarize_plain_text(self, text: str, file_name: str) -> str:
        contents = {
            "role": "user",
            "parts": [
                {"text": PROMPT_TEMPLATE.format(file_name=file_name)},
                {"text": text},
            ],
        }
        return self._generate(contents)

    def summarize_pdf_bytes(self, pdf_bytes: bytes, file_name: str) -> str:
        b64 = base64.b64encode(pdf_bytes).decode("ascii")
        contents = {
            "role": "user",
            "parts": [
                {"text": PROMPT_TEMPLATE.format(file_name=file_name)},
                {
                    "inlineData": {
                        "mimeType": "application/pdf",
                        "data": b64,
                    }
                },
            ],
        }
        return self._generate(contents)
