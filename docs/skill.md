# Platform Skills & Tech Stack

## 技術棧
- **Frontend**: 純 HTML / CSS / Vanilla JS（無 framework）
- **Auth**: Kolable GraphQL API via crm-note-tool.deploy.ai-go.app
- **Session**: localStorage（key: aischool_user）
- **Font**: Google Fonts — Noto Sans TC
- **Deploy**: AI GO Hosted App（靜態 HTML，slug `n8ncourse`）；推 main 不會自動部署
- **Repo**: GitHub JamesAtMoGroup/n8ncourse

## Kolable API
- Auth token: POST https://api.kolable.app/api/v1/auth/token
- Course login: POST https://crm-note-tool.deploy.ai-go.app/api/course-login
  - Body: { email }
  - Success: { success: true }（不回姓名，localStorage 的 name 存 email 的 @ 前段）
  - Fail: { success: false }
  - 429: 嘗試次數過多
- GraphQL Read: https://rhdb.kolable.com/v1/graphql
- GraphQL Write: https://phdb.kolable.com/v1/graphql

## Design System
- Brand: AI School (app_id: aischool)
- Primary accent: #7cffb2 (mint green)
- Background: #000000
- Logo: /assets/aischool-logo.webp (scattered mint green dots)

## 現有課程
- n8ncourse: 29 講，3 open，部署於 n8ncourse.deploy.ai-go.app
