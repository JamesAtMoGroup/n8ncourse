# n8ncourse — Project Notes for Claude

## Repo Structure

```
root/
├── login.html              ← platform login (Kolable API, localStorage)
├── index.html              ← course series portal (auth guard)
├── courses.json            ← course series list (NOT lecture list)
├── admin.html              ← CMS
├── assets/
│   └── aischool-logo.webp  ← brand logo (used everywhere)
├── docs/
│   └── spec.md / rule.md / skill.md / progress.md
└── n8ncourse/
    ├── index.html          ← n8n course homepage (lecture grid)
    ├── courses.json        ← lecture list (day/title/status/url)
    ├── knowledge.json
    ├── lecture1/ lecture2/ lecture3/ ...
```

**When creating a new lecture page**, always place it at `n8ncourse/lectureN/index.html`.

Live site: https://n8ncourse.zeabur.app/
n8ncourse: https://n8ncourse.zeabur.app/n8ncourse/

---

## Auth

- Login: `POST https://crmnotetool.zeabur.app/api/member/search { email, brandKey: "aischool" }`
- Session: `localStorage` key `aischool_user` = `{ email, name }`
- **NO Supabase anywhere** — lecture pages use localStorage only
- Login redirects to `./` (portal) after success
- Lecture pages redirect to `../../login.html` if not logged in
- n8ncourse/index.html redirects to `../login.html` if not logged in

---

## Brand Tokens

### Platform pages (login.html, root index.html)
```css
--bg: #000000
--accent: #7cffb2
Font: Noto Sans TC
```

### n8ncourse pages (n8ncourse/ and all lectureN/) — DO NOT CHANGE
```css
--bg:            #0e0918
--bg-2:          #1a1624
--glass:         rgba(255,255,255,0.04)
--glass-hover:   rgba(255,255,255,0.07)
--glass-active:  rgba(238,79,39,0.12)
--border:        rgba(255,255,255,0.08)
--border-hover:  rgba(255,255,255,0.16)
--accent:        #ee4f27
--accent-dim:    rgba(238,79,39,0.15)
--accent-glow:   rgba(238,79,39,0.3)
--accent-2:      #fd8925
--text-1:        #ffffff
--text-2:        #c8c4b0
--text-3:        #8a859e
Font: Inter (Google Fonts)
```

---

## Logo Rules (CRITICAL)

- **NEVER use "X Learn" logo** — it's been replaced with `aischool-logo.webp`
- **Root `index.html` nav**: `<img src="./assets/aischool-logo.webp">` 44px, no text
- **`n8ncourse/index.html` nav**: NO logo at all (removing it prevents overlap with "← 返回課程選單")
- **Lecture pages nav**: `<img class="logo-img" src="../../assets/aischool-logo.webp">` 36px, no text, links to `../`
- Page titles: `| AI School` suffix (not "X Learn")
- Footer: `© AI School` (not "X Learn")

---

## Nav Structure

### `n8ncourse/index.html` nav
```html
<nav>
  <a href="../" class="nav-back">← 返回課程選單</a>
  <div class="nav-right">
    <span class="nav-badge">n8n 自動化課程</span>
    <span class="nav-user" id="navUser"></span>
    <button class="btn-logout" onclick="logout()">登出</button>
  </div>
</nav>
```
CSS: `.nav-back { font-size:14px; font-weight:500; color:var(--text-2); }`
CSS: `.nav-right { display:flex; align-items:center; gap:12px; }` — space-between handles alignment

### Lecture pages nav (top bar)
- Logo (36px img, links to `../`) on the left
- `← 返回課程` back button also on the left
- No text next to the logo image

---

## courses.json formats

### Root `courses.json` (course series)
```json
[{
  "id": "n8ncourse",
  "title": "n8n AI 自動化課程",
  "description": "從零打造 AI Agent，不需寫程式",
  "thumbnail": null,
  "lectureTotal": 29,
  "lectureOpen": 3,
  "status": "active",
  "url": "./n8ncourse/"
}]
```
`thumbnail`: null = shows first char placeholder. Set to image path/URL to show image.

### `n8ncourse/courses.json` (lecture list)
```json
{ "day": 1, "title": "課程標題", "status": "open", "url": "./lecture1/" }
```
`status`: `"open"` = clickable card, `"wip"` = locked card. Always use relative URLs.

---

## Content Rules (all lectureN/ pages)

### Forbidden
- ❌ Meta tag badges in hero (`完全免費開始`, `不需寫程式`, `約 N 分鐘`, etc.)
- ❌ Inter-lecture nav (`上一堂/下一堂`)
- ❌ Footer callout pointing to next lecture
- ❌ `關於講師` / instructor bio sections
- ❌ Timeframe words: `三週`, `昨天`, `本週`, `第 N 週`
- ❌ "X Learn" branding anywhere

### Hero block (only these three)
1. `LECTURE N` badge
2. `<h1>` title
3. subtitle description text

### Naming
- Folders: `lectureN/` not `dayN/`
- Labels: "Lecture N" not "Day N"
- Breadcrumb: "AI School · Lecture N"

---

## Lecture Page Structure

Each `lectureN/index.html` is a full standalone HTML file:
- Inline `<style>` with all n8ncourse tokens
- Background orbs (3 orbs, fixed, blurred)
- Nav bar: logo (36px img) + back button on left
- Scrollable content with panel hero + panel body per section
- localStorage auth guard: `if(!JSON.parse(localStorage.getItem('aischool_user')||'null')) window.location.href='../../login.html'`
- localStorage progress persistence with key `lectureN-viewed`
