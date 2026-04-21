# Platform Rules

## 程式規則
- 所有新頁面使用 brand tokens（#000000 bg, #7cffb2 accent）
- n8ncourse/ 內的現有頁面設計不得更動
- Session 一律使用 localStorage，key: `aischool_user`
- 不使用 Supabase
- 所有 API 呼叫走 crmnotetool.zeabur.app

## 內容規則
- Hero 區塊禁止：meta tag badges、上一堂/下一堂導航、頁尾 callout 導航
- 禁止詞：三週、本週、第N週、昨天、關於講師
- 資料夾命名：`lectureN/`（不是 dayN/），顯示標籤用 CH 格式
- Hero 區塊只保留：badge、h1 標題、subtitle

## Navbar 規則（所有章節強制統一）
- ✅ 唯一 navbar：sync 腳本注入的 `vc-nav`（← 返回課程選單 + 用戶名 + 登出）
- ❌ 禁止保留原始 HTML 的任何 navbar、header、progress bar
- ❌ 禁止任何第二條 sticky bar（`position:sticky` 且 `top:0` 的非 vc-nav 元素）
- ❌ 禁止 `body` 的 `padding-top`（原本為 progress bar 預留的空間）

## Sync 強制清除規則（每章上傳時自動執行於 sync_drive.py）
- ❌ 強制移除 `.progress-bar-wrap` 及其所有 CSS（`.progress-*`）
- ❌ 強制移除 progress bar HTML 區塊（含 `<!-- Sticky Progress Bar -->` 註解）
- ❌ 強制移除 `body` 的 `padding-top`
- ❌ 強制移除 `<body>` 後的孤立 `</div>`
- ✅ Sync commit 不加 `[skip ci]`，確保 Zeabur 自動部署

## Asset 規則（防止 Zeabur Docker image 過大）
- ✅ 圖片（png/jpg/webp/gif）：直接下載進 repo
- ✅ 影片小於 20MB（mp4/mov）：直接下載進 repo
- ❌ 影片大於 20MB：不下載，自動替換 HTML 中的 `<video><source>` 為 Drive iframe
- 目標：vibecoding/ 資料夾總大小維持 100MB 以下，確保 Zeabur 部署穩定

## Repo 規則
- 所有 lecture 頁面在對應課程子目錄（vibecoding/lectureN/、n8ncourse/lectureN/）
- 根目錄 courses.json = 課程系列清單
- 各課程 courses.json = lecture 清單
- Deploy: Zeabur only

## Agent 規則
- Platform Director 唯一對外溝通
- QA Agent 全 checklist 通過才 deploy
- 任何 checklist 失敗 → 回對應 agent 修正 → 重新驗
