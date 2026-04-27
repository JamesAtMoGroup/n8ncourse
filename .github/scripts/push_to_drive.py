"""
把 vibe-coding-video/out/ 的章節資料夾同步到 Google Drive。
現有同名檔案會覆蓋更新，新檔案會建立。

執行：
  GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... GOOGLE_REFRESH_TOKEN=... \
  VIBECODING_FOLDER_ID=... python3 .github/scripts/push_to_drive.py
"""

import mimetypes, os, sys

import google.oauth2.credentials
import google.auth.transport.requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ── Auth ──────────────────────────────────────────────────────────────────────
credentials = google.oauth2.credentials.Credentials(
    token=None,
    refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/drive"],
)
credentials.refresh(google.auth.transport.requests.Request())
drive = build("drive", "v3", credentials=credentials, cache_discovery=False)

ROOT_FOLDER_ID = os.environ["VIBECODING_FOLDER_ID"]
LOCAL_OUT = os.path.expanduser("~/Projects/vibe-coding-video/out")
SD = dict(supportsAllDrives=True, includeItemsFromAllDrives=True)


def list_drive_files(parent_id):
    """回傳 {name: file_id} dict"""
    resp = drive.files().list(
        q=f"'{parent_id}' in parents and trashed=false",
        fields="files(id,name,mimeType)", **SD
    ).execute()
    return {f["name"]: f for f in resp.get("files", [])}


def upload_file(local_path, filename, parent_id, existing_files):
    size_mb = os.path.getsize(local_path) / 1024 / 1024
    mime = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    media = MediaFileUpload(local_path, mimetype=mime, resumable=size_mb > 5)

    if filename in existing_files:
        file_id = existing_files[filename]["id"]
        drive.files().update(
            fileId=file_id, media_body=media, supportsAllDrives=True
        ).execute()
        print(f"    ↺ 更新  {filename} ({size_mb:.1f} MB)")
    else:
        drive.files().create(
            body={"name": filename, "parents": [parent_id]},
            media_body=media, supportsAllDrives=True
        ).execute()
        print(f"    ＋ 新增  {filename} ({size_mb:.1f} MB)")


def get_or_create_subfolder(name, parent_id, existing_files):
    if name in existing_files and existing_files[name]["mimeType"] == "application/vnd.google-apps.folder":
        return existing_files[name]["id"]
    resp = drive.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]},
        supportsAllDrives=True
    ).execute()
    return resp["id"]


# ── 取得 Drive 根目錄下的所有章節資料夾 ─────────────────────────────────────
drive_folders = list_drive_files(ROOT_FOLDER_ID)
drive_chapter_folders = {
    name: f for name, f in drive_folders.items()
    if f["mimeType"] == "application/vnd.google-apps.folder"
}

# ── 掃描本機 out/ 目錄 ──────────────────────────────────────────────────────
local_chapters = sorted([
    d for d in os.listdir(LOCAL_OUT)
    if os.path.isdir(os.path.join(LOCAL_OUT, d))
])

print(f"本機章節：{len(local_chapters)} 個\n")

for chapter in local_chapters:
    local_dir = os.path.join(LOCAL_OUT, chapter)

    # 比對 Drive 資料夾名稱：完整名稱優先，再用 "CH0-1-" 前綴
    prefix = "-".join(chapter.split("-")[:2]) + "-"  # e.g. "CH0-1-"
    matched = chapter if chapter in drive_chapter_folders else next(
        (name for name in drive_chapter_folders if name.startswith(prefix)),
        None
    )

    if matched:
        drive_folder_id = drive_chapter_folders[matched]["id"]
        print(f"[{chapter[:30]}]  →  Drive: {matched[:30]}")
    else:
        # 建立新資料夾
        resp = drive.files().create(
            body={"name": chapter, "mimeType": "application/vnd.google-apps.folder", "parents": [ROOT_FOLDER_ID]},
            supportsAllDrives=True
        ).execute()
        drive_folder_id = resp["id"]
        print(f"[{chapter[:30]}]  →  Drive: 新建資料夾")

    existing = list_drive_files(drive_folder_id)

    for filename in os.listdir(local_dir):
        full_path = os.path.join(local_dir, filename)

        if os.path.isfile(full_path):
            upload_file(full_path, filename, drive_folder_id, existing)

        elif os.path.isdir(full_path) and filename == "assets":
            # 處理 assets/ 子目錄
            assets_folder_id = get_or_create_subfolder("assets", drive_folder_id, existing)
            assets_existing = list_drive_files(assets_folder_id)
            for asset_file in os.listdir(full_path):
                asset_path = os.path.join(full_path, asset_file)
                if os.path.isfile(asset_path):
                    upload_file(asset_path, asset_file, assets_folder_id, assets_existing)

    print()

print("✅ 同步完成！")
