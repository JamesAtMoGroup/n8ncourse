#!/usr/bin/env python3
"""build_lecture_local.py — Manually create one vibecoding lecture from LOCAL render output.

Workaround for when the Drive auto-sync (sync-vibecoding.yml) can't reach the course
folders. Reuses the EXACT inject_auth / inject_nav / constants from sync_drive.py
(extracted at runtime, no Google auth) so output is identical to the automated sync.

Usage:
  build_lecture_local.py <lectureN> <chapter> "<title>" <src.html> <src.vtt> <drive_folder_id>
Example:
  build_lecture_local.py 8 CH2-1 "先別寫程式：思考不同解法，選一條最可行的路" \
    /path/CH2-1-...html /path/CH2-1-...-subtitles.vtt 1pbdKR5xOXimJJT5evq7hvF1SRGf-X_bH

Run from the n8ncourse repo root.
"""
import re, json, os, sys, datetime

lecture_n, chapter, title, src_html, src_vtt, drive_id = (
    sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
)

# ── Pull exact constants + injection funcs from the real sync script ──────────
src = open(".github/scripts/sync_drive.py", encoding="utf-8").read()
ns = {"re": re}
for name in ("AUTH_GUARD", "NAV_CSS", "NAV_HTML"):
    m = re.search(rf"^{name} = \(.*?^\)", src, re.M | re.S)
    exec(m.group(0), ns)
for fn in ("inject_auth", "inject_nav"):
    m = re.search(rf"^def {fn}\(.*?(?=^def |^# ──)", src, re.M | re.S)
    exec(m.group(0), ns)

# ── Build the lecture page (same transform order as sync_drive.py) ────────────
html = open(src_html, encoding="utf-8").read()

# Strip the standalone-page progress bar BEFORE inject. inject_nav's own progress
# regex is fragile and leaves an orphan (e.g. "章節 2-1"); removing the whole block
# (comment + progress-bar-wrap … up to <div class="container">) first avoids that.
html = html.replace("<!-- Sticky Progress Bar -->", "")
html = re.sub(r'<div class="progress-bar-wrap">.*?(?=<div class="container">)', "", html, flags=re.DOTALL)

html = ns["inject_auth"](html)
html = ns["inject_nav"](html)

lecture_dir = f"vibecoding/lecture{lecture_n}"
os.makedirs(lecture_dir, exist_ok=True)
with open(f"{lecture_dir}/index.html", "w", encoding="utf-8") as fh:
    fh.write(html)
with open(f"{lecture_dir}/subtitles.vtt", "wb") as fh:
    fh.write(open(src_vtt, "rb").read())

# ── Append to vibecoding/courses.json ────────────────────────────────────────
cj_path = "vibecoding/courses.json"
courses = json.load(open(cj_path, encoding="utf-8"))
if not any(c["chapter"] == chapter for c in courses):
    courses.append({"day": int(lecture_n), "chapter": chapter, "title": title,
                    "status": "open", "url": f"./lecture{lecture_n}/"})
json.dump(courses, open(cj_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ── Update sync_manifest.json so the auto-sync won't duplicate this lecture ───
mf_path = "sync_manifest.json"
mf = json.load(open(mf_path, encoding="utf-8"))
mf.setdefault("vibecoding", {})[drive_id] = {
    "lecture": int(lecture_n), "synced_at": datetime.date.today().isoformat(),
    "note": "manual (auto-sync was finding 0 course folders)",
}
json.dump(mf, open(mf_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print(f"Built {lecture_dir}/ + courses.json + manifest for {chapter} (lecture {lecture_n})")
