from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import get_google_oauth_config, get_defaults

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _build_client_config(oauth_cfg: Dict[str, str]) -> Dict:
    return {
        "installed": {
            "client_id": oauth_cfg["client_id"],
            "client_secret": oauth_cfg["client_secret"],
            "redirect_uris": [oauth_cfg["redirect_uri"]],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _load_credentials(token_path: Path) -> Credentials | None:
    if token_path.exists():
        try:
            return Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception:
            return None
    return None


def _save_credentials(creds: Credentials, token_path: Path) -> None:
    token_path.write_text(creds.to_json(), encoding="utf-8")


def _refresh_or_login(token_path: Path) -> Credentials:
    oauth_cfg = get_google_oauth_config()
    creds = _load_credentials(token_path)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_credentials(creds, token_path)
        return creds

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(
            _build_client_config(oauth_cfg), SCOPES
        )
        # Use local server flow; will open browser for login
        creds = flow.run_local_server(prompt="consent", access_type="offline")
        _save_credentials(creds, token_path)
    return creds


def get_drive_service():
    defaults = get_defaults()
    token_path = Path(defaults["token_path"])  # type: ignore[arg-type]
    creds = _refresh_or_login(token_path)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return service
