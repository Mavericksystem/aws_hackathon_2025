# backend/scripts/get_gmail_token.py
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

here = os.path.dirname(os.path.abspath(__file__))
client_secrets_path = os.path.join(here, '..', 'client_secret.json')  # backend/client_secret.json

print(f"Using client secrets from: {client_secrets_path}")
print(f"File exists: {os.path.exists(client_secrets_path)}")

flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)

# Print what redirect URI will be used
print(f"\n⚠️ Make sure this redirect URI is registered in Google Cloud Console:")
print(f"http://localhost:8888/")

# Run local server with explicit redirect_uri_trailing_slash=True
creds = flow.run_local_server(
    port=8888,
    redirect_uri_trailing_slash=True,  # Ensures it uses http://localhost:8888/ not http://localhost:8888
    open_browser=True
)

print("\n✅ Authentication successful!")
print("Access Token:", creds.token)
print("\nYou can now use this token for API requests.")
