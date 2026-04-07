"""
Run this ONCE locally to get your Google OAuth2 refresh token.
The refresh token is permanent — store it as GOOGLE_REFRESH_TOKEN in GitHub Secrets.

Usage:
  pip install google-auth-oauthlib
  export GOOGLE_CLIENT_ID="your-client-id"
  export GOOGLE_CLIENT_SECRET="your-client-secret"
  python .github/scripts/get_token.py
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_CONFIG = {
    "installed": {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
    }
}

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
creds = flow.run_local_server(port=0)

print("\n✅ Copy this refresh token → GitHub Secret: GOOGLE_REFRESH_TOKEN")
print("─" * 60)
print(creds.refresh_token)
print("─" * 60)
