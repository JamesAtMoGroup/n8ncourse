# Platform Build Progress

## 狀態：✅ Phase 1–4 完成（2026-04-07）

## Phase 1 — Repo 結構重組
- [x] 建立 n8ncourse/ 子目錄
- [x] 搬移 index.html → n8ncourse/index.html
- [x] 搬移 courses.json → n8ncourse/courses.json
- [x] 搬移 lecture1/ lecture2/ lecture3/ → n8ncourse/
- [x] 搬移 knowledge.json → n8ncourse/
- [x] 更新所有 lecture 頁「← 返回主頁」連結（../../login.html）
- [x] n8ncourse/index.html 加「← 返回課程選單」（→ ../）

## Phase 2 — 新頁面建立
- [x] login.html（Email 輸入 + Kolable API 驗證，localStorage session）
- [x] index.html（課程系列入口 + 卡片 grid，auth guard）
- [x] root courses.json（課程系列資料，1 entry: n8ncourse）
- [x] assets/aischool-logo.webp（logo 複製完成）

## Phase 3 — QA
- [x] Checklist A：結構完整性（14/14 PASS）
- [x] Checklist B：登入流程（15/15 PASS）
- [x] Checklist C：UI / 設計（7/7 PASS）
- [x] Checklist D：courses.json 一致性（D-41 warn 已修正，相對路徑統一）

## Phase 4 — Deploy
- [x] git push origin main
- [x] ~/Projects/n8ncourse 同步
- [x] ~/Desktop/Claude/projects/n8ncourse 同步

## 待確認 / 下一步
- [ ] 確認 crmnotetool.zeabur.app CORS 支援新 Zeabur domain（登入測試後確認）
- [ ] 課程封面圖上傳功能（admin.html 第二階段）
- [ ] 未來新課程系列加入 root courses.json

## 更新紀錄
- 2026-04-07: 規格確認，開始執行，全部完成
