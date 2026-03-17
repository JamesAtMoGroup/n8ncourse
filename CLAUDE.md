# n8ncourse — Project Notes for Claude

## Repo Structure Convention

All course day pages live inside this repo, **not** in separate repos.

```
n8ncourse/
├── index.html          ← main landing page + 每日知識庫
├── admin.html          ← CMS for 每日知識庫 (GitHub token required)
├── knowledge.json      ← 每日知識庫 content (managed via admin.html)
├── day1/
│   └── index.html      ← Day 1 course content
├── day2/
│   └── index.html      ← Day 2 (add when ready)
├── day3/
│   └── index.html      ← Day 3 (add when ready)
└── audio/              ← audio files uploaded via admin.html
```

**When creating a new day's course page**, always place it at `dayN/index.html` inside this repo — never create a separate GitHub repo for it.

Live site: https://jamesatmogroup.github.io/n8ncourse/
Day 1 URL: https://jamesatmogroup.github.io/n8ncourse/day1/

## Design System

- Color palette matches n8n.io
- `--bg: #0e0918`, `--bg-2: #1a1624`
- `--accent: #ee4f27`, `--accent-2: #fd8925`
- `--text-1: #ffffff`, `--text-2: #c8c4b0`, `--text-3: #8a859e`
- Logo: **X Learn** (X in gradient box, "Learn" in accent color)
- Font: Inter

## Nav tabs (index.html)

- 我的主頁 — course landing with hero stats (enrolled count, 21天, 0程式碼)
- 每日知識庫 — daily newsletter feed with date + tag filters
