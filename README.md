# Study Agent

A Python app that reads your Google Drive study materials (PDFs, Google Docs, Google Slides, and PPTX), summarizes each with Gemini in friendly kid-style language, and merges everything into one clean Markdown subject summary.

## What it does
- Connects to Google Drive (OAuth installed app flow)
- Recursively scans a Drive folder for PDFs, Google Docs, Google Slides, and PPTX
- Downloads PDFs, exports Google Docs/Slides to text (Slides fallback to PDF), and extracts PPTX text
- Sends each file to Gemini for a simple, friendly summary
- Merges all summaries into a single, student-friendly Markdown file saved under a versioned folder in `output/`

## Project structure
```
src/
  main.py
  config.py
  auth.py
  drive_client.py
  gemini_client.py
  summarizer.py
  utils.py
output/
requirements.txt
.env.example
README.md
```

## Prerequisites
- Python 3.9+
- A Google Cloud project with Drive API enabled
- OAuth 2.0 Client (type: Desktop App or Installed App)
- A Gemini API key (Google AI Studio / Google Cloud Vertex AI Generative Language)

## 1) Create a Google Cloud project
1. Go to https://console.cloud.google.com/
2. Create/select a project.
3. Enable billing if prompted (some features may require it).

## 2) Enable Google Drive API
1. In the Google Cloud Console, go to "APIs & Services" → "Library".
2. Search for "Google Drive API" and click "Enable".

## 3) Create OAuth credentials
1. Go to "APIs & Services" → "Credentials".
2. Click "Create Credentials" → "OAuth client ID".
3. Application type: choose "Desktop App" (or "Installed app").
4. Copy your Client ID and Client Secret.
5. (Optional) Redirect URI: Desktop/Installed apps use a local server flow. The app defaults to `http://localhost`, so you can leave `GOOGLE_REDIRECT_URI` empty. If you want to pin a port, set a value like `http://localhost:8080/` in your `.env`.

Notes:
- This app stores tokens in `token.json` at the project root. The token will auto-refresh.
- Scope requested: `https://www.googleapis.com/auth/drive.readonly`.

## 4) Get a Gemini API key
- Visit https://aistudio.google.com/ or Gemini on Google Cloud and create an API key.
- Make sure the key has access to a model available to your key (recommended default: `gemini-2.5-flash`).

## 5) Configure environment variables
1. Copy `.env.example` to `.env` and fill values:
```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
# Optional: defaults to http://localhost
GOOGLE_REDIRECT_URI=
GEMINI_API_KEY=...
# Optional
GEMINI_MODEL_NAME=gemini-2.5-flash
DEFAULT_DRIVE_FOLDER_ID=your_drive_folder_id
```

## 6) Install dependencies
```
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

### Quick Start (one command)

On Windows (PowerShell):
```
scripts\setup.ps1
scripts\run_cli.ps1
```

On macOS/Linux:
```
chmod +x scripts/*.sh
scripts/run_cli.sh
```

## 7) Run the app

There are two ways to use Study Agent now:

### A) Interactive CLI (navigate Sem → Subject → Chapter)
```
python -m src.main
```
On first run, you'll authenticate with Google. Then you'll be asked to:
- Provide a ROOT Study Folder (ID or full URL) unless it's set in `.env`.
- Enter a Subject Name and optional Semester (e.g., "Sem 3").
- Navigate down the folder tree (Sem → Subject → Chapter) using a simple menu.
- Type `here` to summarize the current folder (recursively), or `exit` to quit.

The CLI supports both raw folder IDs and full Drive URLs. You can set:
- `ROOT_STUDY_FOLDER_ID` or `ROOT_STUDY_FOLDER_URL` in `.env` to preselect the root.
The summary is saved to `output/<subject>/<semester?>/<folder>/<YYYYMMDD_HHMMSS>/summary.md`.

Note: `.env.example` is committed and safe to share. Your real `.env` (with secrets) is ignored by git.

### B) FastAPI server
Start the API server:
```
python -m src.server
```
The server listens on `http://127.0.0.1:8000`.

### Endpoints
- `GET /health` → `{ "status": "ok" }`
- `POST /summarize-folder`
  - Request JSON:
    ```json
    {
      "folderId": "<drive_folder_id>",
      "subjectName": "Data Structures",
      "semester": "Sem 3"
    }
    ```
  - Success response (200):
    ```json
    {
      "status": "ok",
      "filesProcessed": 5,
      "summary_file": "data-structures_sem-3_summary.md",
      "summary_url": "/output/data-structures_sem-3_summary.md",
      "errors": []
    }
    ```
  - Error response (e.g., 400/500): `{ "detail": "message" }`

`/output` is served as static files, so you can open the returned `summary_url` in the browser (prefix with the server origin, e.g., `http://127.0.0.1:8000/output/...`).

On first run (CLI or API), the app will open a browser for Google login to authorize Drive access and create `token.json`.

## Notes about formulas
- The prompt instructs Gemini to keep formulas EXACTLY as in the document and add one-line meanings.
- Always verify formulas manually; OCR or export issues can cause subtle changes in symbols.

## Regenerating summaries
- Re-run the app with the same or a new Drive Folder ID.
- You can delete `output/*_summary.md` files and run again; Drive files will be reprocessed.

## Troubleshooting
- If Drive auth fails, delete `token.json` and run again.
- If Gemini returns size errors for very large PDFs, try splitting the PDF or compressing it. The app uploads PDF bytes inline to the API and very large files may exceed limits.
- Ensure your network/firewall allows local server redirects during OAuth.

## Chrome Extension (Manifest v3)

This repo includes a minimal Chrome extension that runs on `drive.google.com` to trigger summarization for the currently open folder.

### Files
- `extension/manifest.json`
- `extension/background.js`
- `extension/content.js`
- `extension/styles.css`

### What it does
- Injects a floating "Summarize this folder" button on Google Drive pages
- Reads current `folderId` from the URL
- Opens a popup to enter `subject` and `semester`
- Calls the local FastAPI backend `POST /summarize-folder`
- Shows a link to the generated summary when complete

### Install the extension
1. Start the API server locally:
   ```
   python -m src.server
   ```
2. Open Chrome → `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked" and select the `extension/` folder in this project
5. Open `https://drive.google.com/drive/folders/<your_folder_id>`
6. Click the floating "Summarize this folder" button, enter details, and run

Notes:
- The extension expects the API at `http://127.0.0.1:8000`. Adjust `extension/background.js` if the server origin changes.
- CORS is enabled server-side to allow calls from the extension.

## New configuration for hierarchical navigation

Add one of the following in `.env` to start at your shared ROOT Study Folder:
```
# Prefer ID if you have it
ROOT_STUDY_FOLDER_ID=1Un2ZAmsO1aoVPOt674jn0-DGsH2vB9g_
# Or a full URL; the app extracts the ID automatically
ROOT_STUDY_FOLDER_URL=https://drive.google.com/drive/folders/1Un2ZAmsO1aoVPOt674jn0-DGsH2vB9g_?usp=sharing
```

During CLI navigation you can pick:
- Semester folder (e.g., Sem 1, Sem 2, Sem 3)
- Subject folder (e.g., DSA, COA, PSNM)
- Chapter folder(s)

Type `here` at any level to summarize that folder recursively (all PDFs and Google Docs inside, including subfolders).

The API endpoint also accepts either a raw folder ID or a full Drive folder URL in `folderId`.
