# n8ncourse — Project Notes for Claude

## Repo Structure Convention

All lecture pages live inside this repo, **not** in separate repos.
Folders are named `lectureN/` (not `dayN/`).

```
n8ncourse/
├── index.html            ← main landing page + 每日知識庫
├── admin.html            ← CMS for 每日知識庫 (GitHub token required)
├── knowledge.json        ← 每日知識庫 content (managed via admin.html)
├── courses.json          ← course card data (status: open | wip, url)
├── lecture1/index.html   ← Lecture 1 course content
├── lecture2/index.html   ← Lecture 2 course content
├── lecture3/index.html   ← Lecture 3 (add when ready)
└── audio/                ← audio files uploaded via admin.html
```

**When creating a new lecture page**, always place it at `lectureN/index.html` — never use `dayN/` naming.

Live site: https://jamesatmogroup.github.io/n8ncourse/
Lecture 1: https://jamesatmogroup.github.io/n8ncourse/lecture1/
Lecture 2: https://jamesatmogroup.github.io/n8ncourse/lecture2/

---

## Design System

### Color tokens (dark theme — do NOT use light/Claude.ai CSS variables)
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
--success:       #34d399
--success-bg:    rgba(52,211,153,0.1)
--success-bdr:   rgba(52,211,153,0.2)
--info:          #60a5fa
--info-bg:       rgba(96,165,250,0.1)
--info-bdr:      rgba(96,165,250,0.25)
```

### Layout
- Animated background orbs (3 orbs, fixed, blurred)
- **App shell**: `display: flex; height: 100vh; overflow: hidden`
- **Left sidebar** (272px): brand tag + section/chapter list + 整體進度 bar at bottom
- **Right main**: sticky top-bar + scrollable content area
- Top bar always includes **← 返回主頁** link back to `../`

### Typography & Components
- Font: Inter (Google Fonts)
- Logo: "X Learn" — X in gradient box, "Learn" in accent color
- Glass cards: `background: var(--glass); border: 1px solid var(--border); border-radius: 12px`
- Top glow line on cards: `linear-gradient(90deg, transparent, rgba(238,79,39,0.4), transparent)`
- Concept boxes use green top glow: `rgba(52,211,153,0.5)`
- Active sidebar items: `background: var(--glass-active); border: 1px solid rgba(238,79,39,0.2)`
- Active item icon: accent color + `box-shadow: 0 0 12px var(--accent-glow)`
- Visited/done icon: success green

### Sidebar progress (整體進度)
- Track read/viewed sections. Progress = viewed / total.
- Bar: `height: 3px; background: linear-gradient(90deg, var(--accent), var(--accent-2))`
- Persist in localStorage with key `lectureN-viewed`

---

## Content & Language Rules

### Forbidden words / phrases
- ❌ `三週` — use `接下來` or `之後`
- ❌ `昨天` — use `上一次`
- ❌ `本週` / `第 N 週` — use `第 N 階段` or `接下來`
- ❌ Any specific time units (days, weeks) that tie content to a schedule
- ❌ `關於講師` tab — do NOT include instructor bio sections
- ❌ `上一堂：Lecture N` / `下一堂：Lecture N` — no inter-lecture navigation; ← 返回主頁 is the only cross-lecture link
- ❌ Meta tag 列（`.meta-row` / `.meta-item` dot badges）— 例如「完全免費開始」「不需寫程式」「約 N 分鐘」「含理論與實作框架」「共 N 個段落」，一律不加
- ❌ 頁尾 callout 導航（「下一堂（Lecture N）：...」）— 不加任何引導至下一講的 callout
- Hero 區塊只保留：LECTURE N badge、h1 標題、subtitle 描述文字

### Naming conventions
- Folders: `lectureN/` not `dayN/`
- Display labels: "Lecture N" not "Day N"
- Section labels inside pages: "Section 01", "Section 02" etc.
- Breadcrumb/brand tag: "X Learn · Lecture N"

---

## index.html — Main Landing Page

- Card grid loaded from `courses.json`
- Card badge displays: `Lecture ${c.day}` (using the `day` number field)
- Two nav tabs: 我的主頁 / 每日知識庫
- Hero stats: 已開放課程 count, 21天, 0程式碼

### courses.json format
```json
{
  "day": 1,
  "title": "課程標題",
  "status": "open",
  "url": "./lecture1/"
}
```
Use relative URLs (e.g. `./lecture1/`) for GitHub Pages compatibility.

---

## Lecture Page Structure (lectureN/index.html)

Each lecture page is a **full standalone HTML file** with:
- Inline `<style>` (all CSS tokens above)
- Background orbs
- Left sidebar with section list + 整體進度
- Top bar with hamburger (mobile) + ← 返回主頁 + breadcrumb + progress pill
- Scrollable content area with panel hero + panel body per section
- "Next →" button at the bottom of each section (except the last)
- Responsive: sidebar slides in on mobile (hamburger toggle)
- localStorage persistence for progress

### Lecture 1 specifics
- 4 chapters with checkboxes (completion tracking)
- Final celebration screen when all checkboxes done

### Lecture 2 specifics
- 4 sections (pure reading, no checkboxes)
- Progress tracked by which sections have been visited
