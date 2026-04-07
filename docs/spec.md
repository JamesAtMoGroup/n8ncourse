# AI School Platform — 完整規格

## 概述
統一課程入口平台。使用者透過 Email 驗證登入後，可瀏覽所有課程系列，點擊進入各課程的詳細頁面。

## Agent 架構
- Platform Director：監督全局，唯一對外溝通角色
- Structure Agent：repo 結構、檔案搬移、連結修正
- Frontend Agent：login.html + root index.html
- Integration Agent：Kolable API 串接 + n8ncourse 接口
- QA Agent：執行所有 checklist，全通過才放行
- Deploy Agent：Zeabur 上線

## 頁面結構
```
repo-root/
├── login.html              ← 平台登入頁
├── index.html              ← 課程系列選擇頁
├── courses.json            ← 課程系列清單
├── admin.html              ← 管理入口
└── n8ncourse/
    ├── index.html          ← n8n 課程首頁
    ├── courses.json        ← lecture 清單
    ├── lecture1/
    ├── lecture2/
    ├── lecture3/
    └── knowledge.json
```

## 登入機制
- 使用者輸入 Email
- 呼叫 POST https://crmnotetool.zeabur.app/api/member/search
- Body: { "email": "...", "brandKey": "aischool" }
- 成功 → 存 localStorage key: `aischool_user` → redirect index.html
- 失敗 → 顯示錯誤提示
- Session: localStorage（不使用 Supabase）

## 品牌 Design Tokens（新頁面專用）
- --bg: #000000
- --bg-2: #111111
- --bg-3: #1a1a1a
- --accent: #7cffb2
- --accent-dim: rgba(124,255,178,0.1)
- --accent-glow: rgba(124,255,178,0.25)
- --text-1: #ffffff
- --text-2: #a0a0a0
- --border: rgba(255,255,255,0.08)
- Font: Noto Sans TC

## 課程系列 courses.json 格式（root）
```json
[
  {
    "id": "n8ncourse",
    "title": "n8n AI 自動化課程",
    "description": "從零打造 AI Agent，不需寫程式",
    "thumbnail": null,
    "lectureTotal": 29,
    "lectureOpen": 3,
    "status": "active",
    "url": "./n8ncourse/"
  }
]
```

## 規則（Forbidden）
- ❌ 不使用 Supabase
- ❌ 不改動 n8ncourse 現有頁面樣式
- ❌ Hero 區塊不加 meta tag badges
- ❌ 不加上一堂/下一堂 inter-lecture 導航
- ✅ n8ncourse/ 內的 lecture 「返回主頁」回 n8ncourse/index.html
- ✅ n8ncourse/index.html 頂部有「← 返回課程選單」回 ../index.html
