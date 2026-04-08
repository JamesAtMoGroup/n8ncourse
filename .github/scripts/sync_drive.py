"""
Sync course content from Google Drive → repo

Handles both courses:
  - vibecoding  (VIBECODING_FOLDER_ID)  → vibecoding/lectureN/
  - n8ncourse   (N8NCOURSE_FOLDER_ID)   → n8ncourse/lectureN/

Drive folder structure per lecture:
  <folder>/
    ├── index.html    → downloaded, auth guard + nav injected
    ├── subtitles.vtt → downloaded
    ├── assets/       → entire subfolder downloaded
    ├── video.mp4     → NOT downloaded; <video> replaced with Drive iframe
    └── youtube.txt   → YouTube ID; used for YouTube iframe (preferred over Drive)

Skip logic:
  sync_manifest.json tracks processed Drive folder IDs.
  Already-processed folders are skipped on subsequent runs.
  Delete a folder ID from the manifest to force re-sync.

Secrets required:
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN,
  VIBECODING_FOLDER_ID, N8NCOURSE_FOLDER_ID
"""

import io, json, os, re, datetime

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
    scopes=["https://www.googleapis.com/auth/drive"],
)
credentials.refresh(google.auth.transport.requests.Request())
service = build("drive", "v3", credentials=credentials, cache_discovery=False)

SD = dict(supportsAllDrives=True, includeItemsFromAllDrives=True)

# ── Course config ─────────────────────────────────────────────────────────────
COURSES = [
    {
        "id": "vibecoding",
        "folder_id": os.environ.get("VIBECODING_FOLDER_ID", ""),
        "out_dir": "vibecoding",
    },
    {
        "id": "n8ncourse",
        "folder_id": os.environ.get("N8NCOURSE_FOLDER_ID", ""),
        "out_dir": "n8ncourse",
    },
]

# ── Manifest ──────────────────────────────────────────────────────────────────
MANIFEST_PATH = "sync_manifest.json"

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}

def save_manifest(manifest):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

# ── Auth guard ────────────────────────────────────────────────────────────────
AUTH_GUARD = (
    "<script>(function(){"
    "if(!JSON.parse(localStorage.getItem('aischool_user')||'null')){"
    "window.location.href='../../login.html';"
    "}})();</script>"
)

# ── Nav bar ───────────────────────────────────────────────────────────────────
# Uses var(--border) so it adapts to each course's design tokens automatically
NAV_CSS = (
    "<style id='vc-nav-css'>"
    "#vc-nav{position:sticky;top:0;z-index:200;height:52px;display:flex;align-items:center;"
    "justify-content:space-between;padding:0 24px;"
    "background:rgba(0,0,0,0.92);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);"
    "border-bottom:1px solid var(--border,rgba(255,255,255,0.1));}"
    "#vc-nav a{font-size:14px;font-weight:500;color:#888;text-decoration:none;transition:color .15s;}"
    "#vc-nav a:hover{color:#fff;}"
    "#vc-nav-right{display:flex;align-items:center;gap:10px;}"
    "#vc-nav-user{font-size:13px;color:#888;}"
    "#vc-logout{font-size:13px;font-weight:600;color:#666;background:rgba(255,255,255,0.04);"
    "border:1px solid var(--border,rgba(255,255,255,0.1));border-radius:8px;padding:4px 12px;"
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


# ── Drive helpers ─────────────────────────────────────────────────────────────
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


# ── HTML injectors ────────────────────────────────────────────────────────────
def inject_auth(html):
    if "aischool_user" in html:
        return html
    patched = re.sub(r"(<body[^>]*>)", r"\1\n" + AUTH_GUARD, html, count=1, flags=re.IGNORECASE)
    return patched if patched != html else AUTH_GUARD + "\n" + html


def inject_nav(html):
    """Inject sticky nav bar (← 返回課程選單 + logout) into each lecture page."""
    if "vc-nav" in html:
        return html  # already injected — idempotent
    # Inject CSS before </head> — never replace </style></head> as a pair
    html = re.sub(r"(</head>)", NAV_CSS + r"\1", html, count=1, flags=re.IGNORECASE)
    # Inject nav HTML after auth guard </script>
    html = re.sub(r"(</script>\n?)(<div|<header|<main|<section)", r"\1" + NAV_HTML + r"\2", html, count=1)
    if "vc-nav" not in html:
        # fallback: right after <body>
        html = re.sub(r"(<body[^>]*>)", r"\1\n" + NAV_HTML, html, count=1, flags=re.IGNORECASE)
    return html


def replace_video_with_iframe(html, mp4_file_id):
    """Replace <video src="*.mp4"> block with a Drive embed iframe."""
    drive_url = f"https://drive.google.com/file/d/{mp4_file_id}/preview"
    iframe = (
        f'<iframe src="{drive_url}" '
        f'width="100%" style="aspect-ratio:16/9;border:none;border-radius:8px;" '
        f'allow="autoplay" allowfullscreen></iframe>'
    )
    html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*>.*?</video>', iframe, html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*/?>',          iframe, html, flags=re.IGNORECASE)
    return html


# ── Main ──────────────────────────────────────────────────────────────────────
manifest = load_manifest()
today = datetime.date.today().isoformat()
any_changes = False

for course in COURSES:
    course_id  = course["id"]
    folder_id  = course["folder_id"]
    out_dir    = course["out_dir"]

    if not folder_id:
        print(f"\n[{course_id}] No folder ID configured — skipping")
        continue

    course_manifest = manifest.setdefault(course_id, {})
    folders = list_folders(folder_id)
    print(f"\n[{course_id}] Found {len(folders)} lecture folder(s)")

    courses_list = []  # for <out_dir>/courses.json

    for idx, folder in enumerate(folders, start=1):
        # ── Skip already-processed folders ────────────────────────────────────
        if folder["id"] in course_manifest:
            print(f"  [{idx}] {folder['name'][:40]} — already synced, skipping")
            # Still need title for courses.json rebuild
            display_title = re.sub(r"^\w+-\w+-", "", folder["name"]).strip()
            courses_list.append({"day": idx, "title": display_title, "status": "open", "url": f"./lecture{idx}/"})
            continue

        files = list_files(folder["id"])
        if not files:
            print(f"  [{idx}] {folder['name'][:40]} — empty, skipping")
            continue

        html_file    = next((f for f in files if f["mimeType"] == "text/html"), None)
        mp4_file     = next((f for f in files if f["mimeType"] == "video/mp4"), None)
        vtt_file     = next((f for f in files if f["mimeType"] == "text/vtt" or f["name"].endswith(".vtt")), None)
        youtube_file = next((f for f in files if f["name"] == "youtube.txt"), None)

        if not html_file:
            print(f"  [{idx}] {folder['name'][:40]} — no HTML, skipping")
            continue

        lecture_dir = f"{out_dir}/lecture{idx}"
        os.makedirs(lecture_dir, exist_ok=True)

        # ── HTML ──────────────────────────────────────────────────────────────
        html = download_bytes(html_file["id"]).decode("utf-8")
        html = inject_auth(html)
        html = inject_nav(html)

        video_note = "no video"
        if youtube_file:
            yt_id = download_bytes(youtube_file["id"]).decode("utf-8").strip()
            yt_iframe = (
                f'<iframe src="https://www.youtube.com/embed/{yt_id}" '
                f'width="100%" style="aspect-ratio:16/9;border:none;border-radius:8px;" '
                f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                f'allowfullscreen></iframe>'
            )
            html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*>.*?</video>', yt_iframe, html, flags=re.IGNORECASE|re.DOTALL)
            html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*/?>',          yt_iframe, html, flags=re.IGNORECASE)
            video_note = f"youtube:{yt_id}"
        elif mp4_file:
            html = replace_video_with_iframe(html, mp4_file["id"])
            video_note = "drive iframe"

        with open(f"{lecture_dir}/index.html", "w", encoding="utf-8") as fh:
            fh.write(html)

        # ── VTT ───────────────────────────────────────────────────────────────
        if vtt_file:
            vtt_bytes = download_bytes(vtt_file["id"])
            with open(f"{lecture_dir}/subtitles.vtt", "wb") as fh:
                fh.write(vtt_bytes)
            video_note += " + vtt"

        # ── Assets subfolder ──────────────────────────────────────────────────
        assets_folder = next((f for f in files if f["mimeType"] == "application/vnd.google-apps.folder"
                              and f["name"] == "assets"), None)
        if assets_folder:
            assets_dir = f"{lecture_dir}/assets"
            os.makedirs(assets_dir, exist_ok=True)
            asset_files = list_files(assets_folder["id"])
            for af in asset_files:
                asset_bytes = download_bytes(af["id"])
                with open(f"{assets_dir}/{af['name']}", "wb") as fh:
                    fh.write(asset_bytes)
            video_note += f" + {len(asset_files)} assets"

        print(f"  [{idx}] {folder['name'][:40]} → lecture{idx}/ ({video_note})")

        # Mark as processed in manifest
        course_manifest[folder["id"]] = {"lecture": idx, "synced_at": today}
        any_changes = True

        display_title = re.sub(r"^\w+-\w+-", "", folder["name"]).strip()
        courses_list.append({"day": idx, "title": display_title, "status": "open", "url": f"./lecture{idx}/"})

    # ── Write <out_dir>/courses.json ──────────────────────────────────────────
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/courses.json", "w", encoding="utf-8") as fh:
        json.dump(courses_list, fh, ensure_ascii=False, indent=2)
    print(f"  Written {out_dir}/courses.json ({len(courses_list)} entries)")

    # ── Update root courses.json lecture count ────────────────────────────────
    root_courses_path = "courses.json"
    if os.path.exists(root_courses_path):
        with open(root_courses_path, encoding="utf-8") as fh:
            root_courses = json.load(fh)
        for c in root_courses:
            if c.get("id") == course_id:
                c["lectureTotal"] = len(courses_list)
                c["lectureOpen"]  = len(courses_list)
        with open(root_courses_path, "w", encoding="utf-8") as fh:
            json.dump(root_courses, fh, ensure_ascii=False, indent=2)
        print(f"  Updated courses.json: {course_id} lectureTotal={len(courses_list)}")

# ── Save manifest ─────────────────────────────────────────────────────────────
save_manifest(manifest)
print(f"\nManifest saved ({sum(len(v) for v in manifest.values())} total processed folders)")
if not any_changes:
    print("No new lectures found.")
