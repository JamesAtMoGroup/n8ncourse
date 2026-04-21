"""
Auto-sync all courses from Google Drive → repo

Drive root structure:
  COURSES_ROOT_FOLDER_ID/
    ├── Vibe Coding/          ← one subfolder = one course
    │     ├── CH0-1-title/    ← lecture subfolder
    │     │     ├── index.html
    │     │     ├── subtitles.vtt
    │     │     ├── assets/
    │     │     ├── video.mp4    (skipped; replaced with Drive iframe)
    │     │     └── youtube.txt  (preferred; replaced with YouTube iframe)
    │     └── ...
    └── n8n/
          └── ...

New course detected → auto-creates repo dir + index.html + root courses.json entry.
New lecture detected → downloads HTML/VTT/assets, injects auth guard + nav, commits.

Skip logic: sync_manifest.json tracks processed Drive folder IDs.

Secrets required:
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN,
  COURSES_ROOT_FOLDER_ID
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

SD   = dict(supportsAllDrives=True, includeItemsFromAllDrives=True)
ROOT = os.environ["COURSES_ROOT_FOLDER_ID"]
TODAY = datetime.date.today().isoformat()

# ── Manifest ──────────────────────────────────────────────────────────────────
MANIFEST_PATH = "sync_manifest.json"

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}

def save_manifest(m):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=2)

# ── Auth guard ────────────────────────────────────────────────────────────────
AUTH_GUARD = (
    "<script>(function(){"
    "if(!JSON.parse(localStorage.getItem('aischool_user')||'null')){"
    "window.location.href='../../login.html';"
    "}})();</script>"
)

# ── Nav bar (uses var(--border) to adapt to each course's design tokens) ──────
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

# ── Course homepage template (auto-generated for new courses) ─────────────────
def course_homepage(title, description):
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI School | {title}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0a0a0a; --bg-2: #111; --glass: rgba(255,255,255,0.04);
      --glass-hover: rgba(255,255,255,0.07); --border: rgba(255,255,255,0.08);
      --border-hover: rgba(255,255,255,0.16); --accent: #7cffb2;
      --text-1: #ffffff; --text-2: #c8c4b0; --text-3: #8a859e;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text-1); min-height: 100vh; }}
    nav {{
      position: sticky; top: 0; z-index: 100; height: 60px;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 40px; background: rgba(10,10,10,0.8);
      backdrop-filter: blur(20px); border-bottom: 1px solid var(--border);
    }}
    .nav-back {{ font-size: 14px; font-weight: 500; color: var(--text-2); text-decoration: none; }}
    .nav-back:hover {{ color: var(--text-1); }}
    .nav-right {{ display: flex; align-items: center; gap: 12px; }}
    .nav-user {{ font-size: 13px; color: var(--text-2); background: var(--glass); border: 1px solid var(--border); border-radius: 999px; padding: 5px 14px; }}
    .btn-logout {{ font-family: inherit; font-size: 13px; font-weight: 600; color: var(--text-3); background: var(--glass); border: 1px solid var(--border); border-radius: 8px; padding: 5px 14px; cursor: pointer; }}
    .btn-logout:hover {{ color: var(--text-2); border-color: var(--border-hover); }}
    .hero {{ padding: 60px 40px 40px; max-width: 960px; margin: 0 auto; }}
    .hero h1 {{ font-size: 40px; font-weight: 800; letter-spacing: -1px; margin-bottom: 12px; }}
    .hero p {{ font-size: 16px; color: var(--text-2); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 16px; max-width: 960px; margin: 0 auto; padding: 0 40px 80px; }}
    .card {{ background: var(--glass); border: 1px solid var(--border); border-radius: 16px; padding: 24px; cursor: pointer; text-decoration: none; color: inherit; transition: background .15s, border-color .15s; display: block; }}
    .card:hover {{ background: var(--glass-hover); border-color: var(--border-hover); }}
    .card-num {{ font-size: 11px; font-weight: 700; letter-spacing: .08em; color: var(--accent); text-transform: uppercase; margin-bottom: 10px; }}
    .card-title {{ font-size: 16px; font-weight: 600; line-height: 1.4; }}
    .card-locked {{ opacity: .4; cursor: default; pointer-events: none; }}
    #loading {{ padding: 80px 40px; color: var(--text-3); text-align: center; }}
  </style>
</head>
<body>
<script>(function(){{if(!JSON.parse(localStorage.getItem('aischool_user')||'null')){{window.location.href='../login.html';}}}})()</script>
<nav>
  <a href="../" class="nav-back">← 返回課程選單</a>
  <div class="nav-right">
    <span class="nav-user" id="navUser"></span>
    <button class="btn-logout" onclick="localStorage.removeItem('aischool_user');window.location.href='../login.html';">登出</button>
  </div>
</nav>
<div class="hero">
  <h1>{title}</h1>
  <p>{description}</p>
</div>
<div id="loading">載入課程中…</div>
<div class="grid" id="grid" style="display:none"></div>
<script>
(function(){{
  var u = JSON.parse(localStorage.getItem('aischool_user')||'null');
  if(u && u.name) document.getElementById('navUser').textContent = u.name;
  fetch('./courses.json').then(r=>r.json()).then(function(list){{
    document.getElementById('loading').style.display='none';
    var grid = document.getElementById('grid');
    grid.style.display='grid';
    list.forEach(function(c){{
      var locked = c.status !== 'open';
      var a = document.createElement('a');
      a.className = 'card' + (locked ? ' card-locked' : '');
      a.href = locked ? '#' : c.url;
      a.innerHTML = '<div class="card-num">LECTURE ' + c.day + '</div><div class="card-title">' + c.title + '</div>';
      grid.appendChild(a);
    }});
  }});
}})();
</script>
</body>
</html>"""


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
    if "id='vc-nav'" in html or 'id="vc-nav"' in html:
        return html
    # Always insert before </head> — never replace </style></head> as a pair
    html = re.sub(r"(</head>)", NAV_CSS + r"\1", html, count=1, flags=re.IGNORECASE)
    html = re.sub(r"(</script>\n?)(<div|<header|<main|<section)", r"\1" + NAV_HTML + r"\2", html, count=1)
    if "id='vc-nav'" not in html and 'id="vc-nav"' not in html:
        html = re.sub(r"(<body[^>]*>)", r"\1\n" + NAV_HTML, html, count=1, flags=re.IGNORECASE)
    # Remove orphaned </div> immediately after injected nav block
    html = re.sub(r"(id='vc-nav'[^<]*(?:<[^>]+>[^<]*)*</nav>[^<]*<script>[^<]*</script>)\s*</div>", r"\1", html, count=1)
    # Any sticky element with top:0 conflicts with vc-nav (52px tall) — push it below
    html = re.sub(r"(position\s*:\s*sticky\s*;[^}]*top\s*:\s*)0(px)?(\s*;[^}]*z-index\s*:\s*(?!2\d\d))", r"\g<1>52px\3", html)
    return html


def replace_video_with_iframe(html, mp4_file_id):
    drive_url = f"https://drive.google.com/file/d/{mp4_file_id}/preview"
    iframe = (f'<iframe src="{drive_url}" width="100%" '
              f'style="aspect-ratio:16/9;border:none;border-radius:8px;" '
              f'allow="autoplay" allowfullscreen></iframe>')
    html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*>.*?</video>', iframe, html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*/?>',          iframe, html, flags=re.IGNORECASE)
    return html


def folder_name_to_id(name):
    """Convert Drive folder name to a slug for repo directory name."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


# ── Main ──────────────────────────────────────────────────────────────────────
manifest = load_manifest()
course_manifest = manifest.setdefault("_courses", {})  # Drive folder ID → repo course ID

# Load root courses.json
root_courses_path = "courses.json"
with open(root_courses_path, encoding="utf-8") as fh:
    root_courses = json.load(fh)

any_changes = False
course_folders = list_folders(ROOT)
print(f"Found {len(course_folders)} course folder(s) under root\n")

for course_folder in course_folders:
    cf_id   = course_folder["id"]
    cf_name = course_folder["name"]

    # ── Resolve course_id ─────────────────────────────────────────────────────
    if cf_id in course_manifest:
        course_id = course_manifest[cf_id]
    else:
        # New course — derive ID from folder name, register in manifest
        course_id = folder_name_to_id(cf_name)
        course_manifest[cf_id] = course_id
        print(f"[NEW COURSE] {cf_name} → course_id: {course_id}")

        # Create course directory and homepage
        os.makedirs(course_id, exist_ok=True)
        homepage_path = f"{course_id}/index.html"
        if not os.path.exists(homepage_path):
            with open(homepage_path, "w", encoding="utf-8") as fh:
                fh.write(course_homepage(cf_name, ""))
            print(f"  Created {homepage_path}")

        # Add to root courses.json if not present
        if not any(c.get("id") == course_id for c in root_courses):
            root_courses.append({
                "id": course_id,
                "title": cf_name,
                "description": "",
                "thumbnail": None,
                "lectureTotal": 0,
                "lectureOpen": 0,
                "status": "active",
                "url": f"./{course_id}/"
            })
        any_changes = True

    print(f"[{course_id}] ({cf_name})")

    # ── Process lectures ───────────────────────────────────────────────────────
    lecture_manifest = manifest.setdefault(course_id, {})
    lecture_folders  = list_folders(cf_id)
    courses_list     = []

    IGNORE_FOLDERS = {"vibe-coding-intake"}
    lecture_folders = [f for f in lecture_folders if f["name"] not in IGNORE_FOLDERS]

    for idx, folder in enumerate(lecture_folders, start=1):
        chapter_match = re.match(r"^(CH\d+-\d+)-", folder["name"])
        chapter = chapter_match.group(1) if chapter_match else f"LECTURE {idx}"
        display_title = re.sub(r"^CH\d+-\d+-", "", folder["name"]).strip()
        courses_list.append({"day": idx, "chapter": chapter, "title": display_title, "status": "open", "url": f"./lecture{idx}/"})

        if folder["id"] in lecture_manifest:
            print(f"  [{idx}] {folder['name'][:40]} — already synced, skipping")
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

        lecture_dir = f"{course_id}/lecture{idx}"
        os.makedirs(lecture_dir, exist_ok=True)

        # HTML
        html = download_bytes(html_file["id"]).decode("utf-8")
        html = inject_auth(html)
        html = inject_nav(html)

        video_note = "no video"
        if youtube_file:
            yt_id = download_bytes(youtube_file["id"]).decode("utf-8").strip()
            yt_iframe = (f'<iframe src="https://www.youtube.com/embed/{yt_id}" width="100%" '
                         f'style="aspect-ratio:16/9;border:none;border-radius:8px;" '
                         f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                         f'allowfullscreen></iframe>')
            html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*>.*?</video>', yt_iframe, html, flags=re.IGNORECASE|re.DOTALL)
            html = re.sub(r'<video[^>]*src="[^"]*\.mp4"[^>]*/?>',          yt_iframe, html, flags=re.IGNORECASE)
            video_note = f"youtube:{yt_id}"
        elif mp4_file:
            html = replace_video_with_iframe(html, mp4_file["id"])
            video_note = "drive iframe"

        with open(f"{lecture_dir}/index.html", "w", encoding="utf-8") as fh:
            fh.write(html)

        # VTT
        if vtt_file:
            with open(f"{lecture_dir}/subtitles.vtt", "wb") as fh:
                fh.write(download_bytes(vtt_file["id"]))
            video_note += " + vtt"

        # Assets subfolder
        assets_folder = next((f for f in files if f["mimeType"] == "application/vnd.google-apps.folder"
                               and f["name"] == "assets"), None)
        if assets_folder:
            assets_dir = f"{lecture_dir}/assets"
            os.makedirs(assets_dir, exist_ok=True)
            asset_files = list_files(assets_folder["id"])
            for af in asset_files:
                with open(f"{assets_dir}/{af['name']}", "wb") as fh:
                    fh.write(download_bytes(af["id"]))
            video_note += f" + {len(asset_files)} assets"

        print(f"  [{idx}] {folder['name'][:40]} → lecture{idx}/ ({video_note})")
        lecture_manifest[folder["id"]] = {"lecture": idx, "synced_at": TODAY}
        any_changes = True

    # Write <course_id>/courses.json
    os.makedirs(course_id, exist_ok=True)
    with open(f"{course_id}/courses.json", "w", encoding="utf-8") as fh:
        json.dump(courses_list, fh, ensure_ascii=False, indent=2)

    # Update root courses.json lecture count
    for c in root_courses:
        if c.get("id") == course_id:
            c["lectureTotal"] = len(courses_list)
            c["lectureOpen"]  = len(courses_list)

    print(f"  → {len(courses_list)} lectures total\n")

# Save root courses.json and manifest
with open(root_courses_path, "w", encoding="utf-8") as fh:
    json.dump(root_courses, fh, ensure_ascii=False, indent=2)

save_manifest(manifest)
print(f"Done. Manifest: {sum(len(v) for k,v in manifest.items() if k != '_courses')} lectures tracked across {len(course_folders)} courses.")
if not any_changes:
    print("No new content found.")
