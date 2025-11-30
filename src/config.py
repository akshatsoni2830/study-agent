import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _get_env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_google_oauth_config():
    return {
        "client_id": _get_env("GOOGLE_CLIENT_ID", required=True),
        "client_secret": _get_env("GOOGLE_CLIENT_SECRET", required=True),
        # Desktop/Installed apps typically use http://localhost and dynamic port
        "redirect_uri": _get_env("GOOGLE_REDIRECT_URI", default="http://localhost"),
    }


def get_gemini_config():
    return {
        "api_key": _get_env("GEMINI_API_KEY", required=True),
        "model": _get_env("GEMINI_MODEL_NAME", default="gemini-pro"),
    }


def get_defaults():
    return {
        "default_drive_folder_id": _get_env("DEFAULT_DRIVE_FOLDER_ID", default=None),
        "root_study_folder_id": _get_env("ROOT_STUDY_FOLDER_ID", default=None),
        "root_study_folder_url": _get_env("ROOT_STUDY_FOLDER_URL", default=None),
        "output_dir": PROJECT_ROOT / "output",
        "token_path": PROJECT_ROOT / "token.json",
    }
