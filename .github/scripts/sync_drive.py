"""
Sync Vibe Coding content from Google Drive → vibecoding/lectureN/

Drive folder structure:
  VIBECODING_FOLDER_ID/
    ├── 01-title/
    │     ├── index.html        → vibecoding/lecture1/index.html  (auth guard injected)
    │     ├── subtitles.vtt     → vibecoding/lecture1/subtitles.vtt
    │     └── video.mp4         → NOT downloaded; <video> replaced with Drive iframe
    └── ...

Secrets required:
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, VIBECODING_FOLDER_ID
"""

import io, json, os, re

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
    scopes=["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/youtube.upload"],
)
credentials.refresh(google.auth.transport.requests.Request())
service = build("drive", "v3", credentials=credentials, cache_discovery=False)
folder_id = os.environ["VIBECODING_FOLDER_ID"]

SD = dict(supportsAllDrives=True, includeItemsFromAllDrives=True)

# ── Auth guard ────────────────────────────────────────────────────────────────
AUTH_GUARD = (
    "<script>(function(){"
    "if(!JSON.parse(localStorage.getItem('aischool_user')||'null')){"
    "window.location.href='../../login.html';"
    "}})();</script>"
)


def list_folders(parent_id):
    resp = service.files().list(
        q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id,name)", orderBy="name", **SD
    ).execute()
    return resp.get("files", [])


def list_files(parent_id):
    resp = service.files().list(
        q=f"'{parent_id}' in parents and trashed=false",
        fields="files(id,name,mimeType)", **SD
    ).execute()
    return resp.get("files", [])


def download_bytes(file_id):
    req = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()


NAV_CSS = (
    "<style id='vc-nav-css'>"
    "#vc-nav{position:sticky;top:0;z-index:200;height:52px;display:flex;align-items:center;"
    "justify-content:space-between;padding:0 24px;"
    "background:rgba(0,0,0,0.92);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);"
    "border-bottom:1px solid rgba(124,255,178,0.14);}"
    "#vc-nav a{font-size:14px;font-weight:500;color:#888;text-decoration:none;transition:color .15s;}"
    "#vc-nav a:hover{color:#fff;}"
    "#vc-nav-right{display:flex;align-items:center;gap:10px;}"
    "#vc-nav-user{font-size:13px;color:#888;}"
    "#vc-logout{font-size:13px;font-weight:600;color:#666;background:rgba(255,255,255,0.04);"
    "border:1px solid rgba(124,255,178,0.14);border-radius:8px;padding:4px 12px;"
    "cursor:pointer;font-family:inherit;}"
    "</style>"
)

NAV_HTML = (
    "<nav id='vc-nav'>"
    "<a href='../'>← 返回課程選單</a>"
    "<div id='vc-nav-right'>"
    "<span id='vc-nav-user'></span>"
    "<button id='vc-logout' onclick=\"localStorage.removeItem('aischool_user');"
    "window.location.href='../../login.html';\">登出</button>"
    "</div></nav>"
    "<script>(function(){var u=JSON.parse(localStorage.getItem('aischool_user')||'null');"
    "if(u&&u.name)document.getElementById('vc-nav-user').textContent=u.name;})();</script>"
)


def inject_auth(html):
    if "aischool_user" in html:
        return html
    patched = re.sub(r"(<body[^>]*>)", r"\1\n" + AUTH_GUARD, html, count=1, flags=re.IGNORECASE)
    return patched if patched != html else AUTH_GUARD + "\n" + html


def inject_nav(html):
    """Inject sticky nav bar (← 返回課程選單 + logout) into each lecture page."""
    if "vc-nav" in html:
        return html  # already injected
    # Inject CSS into <head>
    html = re.sub(r"(</head>)", NAV_CSS + r"\1", html, count=1, flags=re.IGNORECASE)
    # Inject nav HTML right after <body> (after auth guard if present)
    html = re.sub(r"(</script>\n?)(<div|<header|<main|<section|<div)", r"\1" + NAV_HTML + r"\2", html, count=1)
    if "vc-nav" not in html:
        # fallback: inject after <body>
        html = re.sub(r"(<body[^>]*>)", r"\1\n" + NAV_HTML, html, count=1, flags=re.IGNORECASE)
    return html


def replace_video_with_iframe(html, mp4_file_id, vtt_filename=None):
    """Replace <video src="*.mp4"...> block with a Drive embed iframe."""
    drive_url = f"https://drive.google.com/file/d/{mp4_file_id}/preview"

    iframe = (
        f'<iframe src="{drive_url}" '
        f'width="100%" style="aspect-ratio:16/9;border:none;border-radius:8px;" '
        f'allow="autoplay" allowfullscreen></iframe>'
    )

    # Replace <video ...> ... </video> block
    html = re.sub(
        r'<video[^>]*src="[^"]*\.mp4"[^>]*>.*?</video>',
        iframe,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # Also replace standalone <video src="*.mp4" .../> self-closing
    html = re.sub(
        r'<video[^>]*src="[^"]*\.mp4"[^>]*/?>',
        iframe,
        html,
        flags=re.IGNORECASE,
    )
    return html


# ── Main ──────────────────────────────────────────────────────────────────────
folders = list_folders(folder_id)
print(f"Found {len(folders)} lecture folder(s)")

courses = []

for idx, folder in enumerate(folders, start=1):
    files = list_files(folder["id"])
    if not files:
        print(f"  [{folder['name']}] Empty — skipping")
        continue

    html_file    = next((f for f in files if f["mimeType"] == "text/html"), None)
    mp4_file     = next((f for f in files if f["mimeType"] == "video/mp4"), None)
    vtt_file     = next((f for f in files if f["mimeType"] == "text/vtt"
                         or f["name"].endswith(".vtt")), None)
    youtube_file = next((f for f in files if f["name"] == "youtube.txt"), None)

    if not html_file:
        print(f"  [{folder['name']}] No HTML — skipping")
        continue

    out_dir = f"vibecoding/lecture{idx}"
    os.makedirs(out_dir, exist_ok=True)

    # ── HTML ──
    html = download_bytes(html_file["id"]).decode("utf-8")
    html = inject_auth(html)
    html = inject_nav(html)

    if youtube_file:
        # Prefer YouTube embed over Drive mp4
        yt_id = download_bytes(youtube_file["id"]).decode("utf-8").strip()
        yt_iframe = (
            f'<iframe src="https://www.youtube.com/embed/{yt_id}" '
            f'width="100%" style="aspect-ratio:16/9;border:none;border-radius:8px;" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            f'allowfullscreen></iframe>'
        )
        # Replace <video src="*.mp4"> block with YouTube iframe
        html = re.sub(
            r'<video[^>]*src="[^"]*\.mp4"[^>]*>.*?</video>',
            yt_iframe, html, flags=re.IGNORECASE | re.DOTALL,
        )
        html = re.sub(
            r'<video[^>]*src="[^"]*\.mp4"[^>]*/?>',
            yt_iframe, html, flags=re.IGNORECASE,
        )
        video_note = f"youtube:{yt_id}"
    elif mp4_file:
        html = replace_video_with_iframe(html, mp4_file["id"])
        video_note = "drive iframe"
    else:
        video_note = "no video"

    with open(f"{out_dir}/index.html", "w", encoding="utf-8") as fh:
        fh.write(html)

    # ── VTT ──
    if vtt_file:
        vtt_bytes = download_bytes(vtt_file["id"])
        with open(f"{out_dir}/subtitles.vtt", "wb") as fh:
            fh.write(vtt_bytes)
        video_note += " + vtt"

    # ── Assets subfolder ──
    assets_folder = next((f for f in files if f["mimeType"] == "application/vnd.google-apps.folder"
                          and f["name"] == "assets"), None)
    if assets_folder:
        assets_dir = f"{out_dir}/assets"
        os.makedirs(assets_dir, exist_ok=True)
        asset_files = list_files(assets_folder["id"])
        for af in asset_files:
            asset_bytes = download_bytes(af["id"])
            with open(f"{assets_dir}/{af['name']}", "wb") as fh:
                fh.write(asset_bytes)
        video_note += f" + {len(asset_files)} assets"

    print(f"  [{idx}] {folder['name'][:40]} → lecture{idx}/ ({video_note})")

    display_title = re.sub(r"^\w+-\w+-", "", folder["name"]).strip()
    courses.append({"day": idx, "title": display_title, "status": "open", "url": f"./lecture{idx}/"})

with open("vibecoding/courses.json", "w", encoding="utf-8") as fh:
    json.dump(courses, fh, ensure_ascii=False, indent=2)
print(f"\nWritten vibecoding/courses.json ({len(courses)} entries)")
