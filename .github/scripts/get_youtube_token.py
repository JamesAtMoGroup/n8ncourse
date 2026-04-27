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

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/youtube.upload",
]

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
auth_url, _ = flow.authorization_url(prompt="consent")
print("\n複製這個 URL 到瀏覽器：\n")
print(auth_url)
code = input("\n授權碼：").strip()
flow.fetch_token(code=code)
print("\n✅ New Refresh Token:")
print(flow.credentials.refresh_token)
