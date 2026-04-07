# Platform Skills & Tech Stack

## 技術棧
- **Frontend**: 純 HTML / CSS / Vanilla JS（無 framework）
- **Auth**: Kolable GraphQL API via crmnotetool.zeabur.app
- **Session**: localStorage（key: aischool_user）
- **Font**: Google Fonts — Noto Sans TC
- **Deploy**: Zeabur（靜態 HTML）
- **Repo**: GitHub JamesAtMoGroup/n8ncourse

## Kolable API
- Auth token: POST https://api.kolable.app/api/v1/auth/token
- Member search: POST https://crmnotetool.zeabur.app/api/member/search
  - Body: { email, brandKey: "aischool" }
  - Success: { success: true, data: { id, name, email } }
  - Fail: { success: false, message: "..." }
- GraphQL Read: https://rhdb.kolable.com/v1/graphql
- GraphQL Write: https://phdb.kolable.com/v1/graphql

## Design System
- Brand: AI School (app_id: aischool)
- Primary accent: #7cffb2 (mint green)
- Background: #000000
- Logo: /assets/aischool-logo.webp (scattered mint green dots)

## 現有課程
- n8ncourse: 29 講，3 open，部署於 n8ncourse.zeabur.app
