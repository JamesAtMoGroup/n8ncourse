"""
Run this ONCE locally to get your Google OAuth2 refresh token.

Usage:
  export GOOGLE_CLIENT_ID="your-client-id"
  export GOOGLE_CLIENT_SECRET="your-client-secret"
  python3 .github/scripts/get_token.py
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_CONFIG = {
    "installed": {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
    }
}

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
auth_url, _ = flow.authorization_url(prompt="consent")

print("\n1. 複製以下 URL 貼到瀏覽器：")
print("─" * 60)
print(auth_url)
print("─" * 60)
print("\n2. 登入 Google 帳號並允許權限")
print("3. 複製頁面上顯示的授權碼，貼到下方")

code = input("\n授權碼：").strip()
flow.fetch_token(code=code)
creds = flow.credentials

print("\n✅ 成功！複製以下 Refresh Token → 存為 GitHub Secret: GOOGLE_REFRESH_TOKEN")
print("─" * 60)
print(creds.refresh_token)
print("─" * 60)
