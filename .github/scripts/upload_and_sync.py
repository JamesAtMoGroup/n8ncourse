"""
全自動：掃描 Drive 資料夾 → 上傳 mp4 到 YouTube（Unlisted）→ 寫 youtube.txt 回 Drive → 同步 HTML 到 repo

執行方式：
  GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... GOOGLE_REFRESH_TOKEN=... \
  VIBECODING_FOLDER_ID=... python3 .github/scripts/upload_and_sync.py
"""

import io, json, os, re, tempfile

import google.oauth2.credentials
import google.auth.transport.requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaInMemoryUpload

# ── Auth ──────────────────────────────────────────────────────────────────────
credentials = google.oauth2.credentials.Credentials(
    token=None,
    refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/youtube.upload",
    ],
)
credentials.refresh(google.auth.transport.requests.Request())

drive   = build("drive",   "v3", credentials=credentials, cache_discovery=False)
youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)

folder_id = os.environ["VIBECODING_FOLDER_ID"]
SD = dict(supportsAllDrives=True, includeItemsFromAllDrives=True)

AUTH_GUARD = (
    "<script>(function(){"
    "if(!JSON.parse(localStorage.getItem('aischool_user')||'null')){"
    "window.location.href='../../login.html';"
    "}})();</script>"
)


def list_folders(parent_id):
    resp = drive.files().list(
        q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id,name)", orderBy="name", **SD
    ).execute()
    return resp.get("files", [])


def list_files(parent_id):
    resp = drive.files().list(
        q=f"'{parent_id}' in parents and trashed=false",
        fields="files(id,name,mimeType)", **SD
    ).execute()
    return resp.get("files", [])


def download_bytes(file_id):
    req = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        status, done = dl.next_chunk()
    return buf.getvalue()


def download_to_file(file_id, path):
    req = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
    with open(path, "wb") as fh:
        dl = MediaIoBaseDownload(fh, req)
        done = False
        while not done:
            status, done = dl.next_chunk()
            if status:
                print(f"    下載中 {int(status.progress()*100)}%", end="\r")
    print()


def upload_to_youtube(mp4_path, title):
    print(f"  上傳到 YouTube: {title}")
    body = {
        "snippet": {"title": title, "description": ""},
        "status": {"privacyStatus": "unlisted"},
    }
    media = MediaFileUpload(mp4_path, mimetype="video/mp4", resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"    上傳中 {int(status.progress()*100)}%", end="\r")
    print()
    return response["id"]


def write_youtube_txt(folder_id, yt_id):
    media = MediaInMemoryUpload(yt_id.encode(), mimetype="text/plain")
    drive.files().create(
        body={"name": "youtube.txt", "parents": [folder_id]},
        media_body=media,
        supportsAllDrives=True,
    ).execute()


def inject_auth(html):
    if "aischool_user" in html:
        return html
    patched = re.sub(r"(<body[^>]*>)", r"\1\n" + AUTH_GUARD, html, count=1, flags=re.IGNORECASE)
    return patched if patched != html else AUTH_GUARD + "\n" + html


def embed_youtube(html, yt_id):
    iframe = (
        f'<iframe src="https://www.youtube.com/embed/{yt_id}" '
        f'width="100%" style="aspect-ratio:16/9;border:none;border-radius:8px;" '
        f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
        f'allowfullscreen></iframe>'
    )
    html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*>.*?</video>', iframe, html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*/?>',          iframe, html, flags=re.IGNORECASE)
    return html


# ── Main ──────────────────────────────────────────────────────────────────────
folders = list_folders(folder_id)
print(f"找到 {len(folders)} 個資料夾\n")
courses = []

for idx, folder in enumerate(folders, start=1):
    print(f"[{idx}] {folder['name']}")
    files = list_files(folder["id"])

    html_file    = next((f for f in files if f["mimeType"] == "text/html"), None)
    mp4_file     = next((f for f in files if f["mimeType"] == "video/mp4"), None)
    vtt_file     = next((f for f in files if f["name"].endswith(".vtt")), None)
    youtube_file = next((f for f in files if f["name"] == "youtube.txt"), None)

    if not html_file:
        print("  ⚠️  沒有 HTML，跳過")
        continue

    out_dir = f"vibecoding/lecture{idx}"
    os.makedirs(out_dir, exist_ok=True)

    # ── YouTube upload（如果還沒有 youtube.txt）──
    yt_id = None
    if youtube_file:
        yt_id = download_bytes(youtube_file["id"]).decode().strip()
        print(f"  ✅ 已有 YouTube ID: {yt_id}")
    elif mp4_file:
        title = re.sub(r"^\w+-\w+-", "", folder["name"]).strip()
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            print(f"  ⬇️  下載 mp4...")
            download_to_file(mp4_file["id"], tmp_path)
            yt_id = upload_to_youtube(tmp_path, title)
            print(f"  ✅ YouTube ID: {yt_id}")
            write_youtube_txt(folder["id"], yt_id)
            print(f"  💾 youtube.txt 寫回 Drive")
        finally:
            os.unlink(tmp_path)

    # ── HTML ──
    html = download_bytes(html_file["id"]).decode("utf-8")
    html = inject_auth(html)
    if yt_id:
        html = embed_youtube(html, yt_id)
    with open(f"{out_dir}/index.html", "w", encoding="utf-8") as fh:
        fh.write(html)

    # ── VTT ──
    if vtt_file:
        with open(f"{out_dir}/subtitles.vtt", "wb") as fh:
            fh.write(download_bytes(vtt_file["id"]))

    display_title = re.sub(r"^\w+-\w+-", "", folder["name"]).strip()
    courses.append({"day": idx, "title": display_title, "status": "open", "url": f"./lecture{idx}/"})
    print()

with open("vibecoding/courses.json", "w", encoding="utf-8") as fh:
    json.dump(courses, fh, ensure_ascii=False, indent=2)

print(f"✅ 完成！vibecoding/courses.json 已更新（{len(courses)} 堂）")
print("\n下一步：")
print('  git add vibecoding/ && git commit -m "sync: update vibecoding" && git push')
