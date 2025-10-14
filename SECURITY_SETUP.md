# 🔐 Security Setup Guide

## ✅ Completed Security Improvements

### 1. Credentials Masked
- ✅ `client_secret.json` - OAuth credentials masked with `xxxxxxxxx`
- ✅ `.env` file created with masked values
- ✅ `app.py` updated to use environment variables

### 2. Files Created
- ✅ `.gitignore` - Prevents committing sensitive files
- ✅ `.env.example` - Template for environment variables
- ✅ `.env` - Actual environment file (NOT committed to git)

### 3. Code Updated
- ✅ `app.py` now uses `python-dotenv` to load environment variables
- ✅ Removed hardcoded secret key fallback
- ✅ All sensitive values now read from environment

---

## 🚨 IMPORTANT: Next Steps

### Step 1: Generate New Credentials

**Your old credentials were exposed in the code. You MUST rotate them:**

1. **Google OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Delete the old OAuth 2.0 Client ID
   - Create a new OAuth 2.0 Client ID
   - Download the new `client_secret.json`
   - Place it in `backend/client_secret.json`

2. **Generate Flask Secret Key:**
   ```python
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copy the output

### Step 2: Update Your .env File

Edit `backend/.env` and replace the `xxxxxxxxx` values with your real credentials:

```bash
# Generate a new secret key
SECRET_KEY=your-generated-secret-key-from-step-1

# Copy from your NEW client_secret.json
GOOGLE_CLIENT_ID=your-new-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-new-client-secret

# Rest should be correct
REDIRECT_URI=http://localhost:5000/oauth2callback
DYNAMO_TABLE_RAW_EMAILS=RawEmails
DYNAMO_TABLE_USER_CREDS=UserCredentials
DYNAMO_TABLE_USER_PROFILES=UserProfiles
AWS_REGION=us-east-1
FRONTEND_URL=http://localhost:5173
```

### Step 3: Verify Setup

```powershell
cd backend
python app.py
```

You should see:
```
✅ DynamoDB connection initialized
 * Running on http://127.0.0.1:5000
```

If you see an error about `SECRET_KEY`, your `.env` file isn't loaded correctly.

---

## 📝 For New Team Members

When someone clones this repo:

1. Copy `.env.example` to `.env`:
   ```powershell
   cp backend/.env.example backend/.env
   ```

2. Get credentials from team lead and update `.env`

3. Install dependencies:
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```

4. Run the app:
   ```powershell
   python app.py
   ```

---

## 🔒 Security Best Practices

### ✅ DO:
- Keep `.env` file LOCAL only (never commit)
- Use `.env.example` as a template
- Rotate credentials if exposed
- Use AWS Secrets Manager for production
- Enable 2FA on Google Cloud Console

### ❌ DON'T:
- Commit `client_secret.json` to git
- Share credentials via email/Slack
- Use the same credentials for dev and production
- Hardcode secrets in code files

---

## 🚀 Production Deployment

For production, use AWS Secrets Manager instead of `.env` files:

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Use in app.py
secrets = get_secret('raven-ai/prod/credentials')
app.secret_key = secrets['SECRET_KEY']
```

---

## 📞 Need Help?

If you encounter issues:
1. Check that `.env` file exists in `backend/` folder
2. Verify all values are filled (no `xxxxxxxxx` remaining)
3. Ensure `python-dotenv` is installed
4. Check AWS credentials: `aws configure list`
