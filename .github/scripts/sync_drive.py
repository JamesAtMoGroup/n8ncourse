"""
Sync Vibe Coding HTML files from Google Drive → vibecoding/lectureN/index.html

Drive folder structure:
  VIBECODING_FOLDER_ID/
    ├── 01-some-title/   → vibecoding/lecture1/index.html
    ├── 02-another/      → vibecoding/lecture2/index.html
    └── ...

Folders are sorted alphabetically — prefix with 01-, 02-, ... to control order.
Each subfolder should contain one index.html (or any .html file).
Auth guard is injected after <body> if not already present.

Secrets required (GitHub → Settings → Secrets):
  GOOGLE_CLIENT_ID      OAuth2 client ID
  GOOGLE_CLIENT_SECRET  OAuth2 client secret
  GOOGLE_REFRESH_TOKEN  OAuth2 refresh token (run get_token.py once to obtain)
  VIBECODING_FOLDER_ID  Google Drive folder ID
"""

import io
import json
import os
import re

import google.oauth2.credentials
import google.auth.transport.requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ── Auth ──────────────────────────────────────────────────────────────────────
credentials = google.oauth2.credentials.Credentials(
    token=None,
    refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/drive.readonly"],
)
credentials.refresh(google.auth.transport.requests.Request())

service = build("drive", "v3", credentials=credentials, cache_discovery=False)
folder_id = os.environ["VIBECODING_FOLDER_ID"]

# ── Auth guard injected into every page ───────────────────────────────────────
AUTH_GUARD = (
    "<script>"
    "(function(){"
    "if(!JSON.parse(localStorage.getItem('aischool_user')||'null')){"
    "window.location.href='../../login.html';"
    "}"
    "})();"
    "</script>"
)


def list_folders(parent_id):
    q = (
        f"'{parent_id}' in parents"
        " and mimeType='application/vnd.google-apps.folder'"
        " and trashed=false"
    )
    resp = service.files().list(q=q, fields="files(id,name)", orderBy="name").execute()
    return resp.get("files", [])


def list_html_files(parent_id):
    q = f"'{parent_id}' in parents and mimeType='text/html' and trashed=false"
    resp = service.files().list(q=q, fields="files(id,name)").execute()
    return resp.get("files", [])


def download_file(file_id):
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue().decode("utf-8")


def inject_auth(html):
    if "aischool_user" in html:
        return html  # already has auth guard
    patched = re.sub(r"(<body[^>]*>)", r"\1\n" + AUTH_GUARD, html, count=1, flags=re.IGNORECASE)
    return patched if patched != html else AUTH_GUARD + "\n" + html


# ── Main ──────────────────────────────────────────────────────────────────────
folders = list_folders(folder_id)
print(f"Found {len(folders)} lecture folder(s)")

courses = []

for idx, folder in enumerate(folders, start=1):
    html_files = list_html_files(folder["id"])
    if not html_files:
        print(f"  [{folder['name']}] No HTML files — skipping")
        continue

    target = next((f for f in html_files if f["name"].lower() == "index.html"), html_files[0])
    content = inject_auth(download_file(target["id"]))

    out_dir = f"vibecoding/lecture{idx}"
    out_path = f"{out_dir}/index.html"
    os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"  [{idx}] {folder['name']} → {out_path}")

    display_title = re.sub(r"^\d+[-_\s]*", "", folder["name"]).strip()
    courses.append({"day": idx, "title": display_title, "status": "open", "url": f"./lecture{idx}/"})

# Write vibecoding/courses.json
with open("vibecoding/courses.json", "w", encoding="utf-8") as fh:
    json.dump(courses, fh, ensure_ascii=False, indent=2)
print(f"Written vibecoding/courses.json ({len(courses)} entries)")
