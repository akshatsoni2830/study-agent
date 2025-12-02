from __future__ import annotations

import base64
import json
import time
from typing import Any, Dict, Optional, List

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

QUIZ_PROMPT = (
    "Based on the following text, generate a quiz with 5 multiple choice questions. "
    "Return the result strictly as a JSON list of objects, where each object has "
    "'question', 'options' (list of 4 strings), 'answer' (the correct string), and 'explanation'. "
    "Do not include any markdown formatting like ```json ... ```, just the raw JSON."
)

FLASHCARD_PROMPT = (
    "Based on the following text, generate 10 flashcards for studying. "
    "Return the result strictly as a JSON list of objects, where each object has "
    "'front' (term or question) and 'back' (definition or answer). "
    "Do not include any markdown formatting like ```json ... ```, just the raw JSON."
)

CHAT_PROMPT = (
    "You are a helpful tutor. Answer the user's question based strictly on the provided context. "
    "If the answer is not in the context, say 'I cannot answer this from the provided documents.'\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}"
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

    def _clean_json_response(self, text: str) -> Any:
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            # Find first newline
            idx = text.find("\n")
            if idx != -1:
                text = text[idx+1:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

    def generate_quiz(self, text: str) -> List[Dict[str, Any]]:
        contents = {
            "role": "user",
            "parts": [
                {"text": QUIZ_PROMPT},
                {"text": text},
            ],
        }
        resp = self._generate(contents)
        try:
            return self._clean_json_response(resp)
        except Exception:
            # Fallback or empty list
            print(f"Failed to parse quiz JSON: {resp}")
            return []

    def generate_flashcards(self, text: str) -> List[Dict[str, str]]:
        contents = {
            "role": "user",
            "parts": [
                {"text": FLASHCARD_PROMPT},
                {"text": text},
            ],
        }
        resp = self._generate(contents)
        try:
            return self._clean_json_response(resp)
        except Exception:
            print(f"Failed to parse flashcards JSON: {resp}")
            return []

    def chat_with_content(self, context_text: str, question: str) -> str:
        contents = {
            "role": "user",
            "parts": [
                {"text": CHAT_PROMPT.format(context=context_text, question=question)},
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
