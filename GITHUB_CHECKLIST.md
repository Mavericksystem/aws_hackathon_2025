# 🚀 GitHub Upload Checklist

## ✅ Before Pushing to GitHub - MANDATORY CHECKS

### 1. Verify No Credentials in Code
```powershell
# Run this command to search for potential credentials
cd C:\Users\moina\Downloads\aws_agent
findstr /S /I /C:"GOCSPX" /C:"ya29" /C:"AKIA" /C:"client_secret" /C:"SECRET_KEY" *.py *.js *.json *.xml
```

**Expected result:** Should ONLY find:
- References in `.env.example` (placeholders)
- Import statements like `from dotenv import load_dotenv`
- Comments in `SECURITY_SETUP.md`

### 2. Check .gitignore is Working
```powershell
git status
```

**Must NOT see:**
- ❌ `client_secret.json`
- ❌ `.env`
- ❌ `repomix-output.xml`
- ❌ `tmp_deploy/` folders
- ❌ `*.zip` files in lambda folders

**Should see:**
- ✅ `.env.example`
- ✅ `.gitignore`
- ✅ `SECURITY_SETUP.md`
- ✅ Python and JS source files

### 3. Files That Are SAFE to Commit

#### ✅ Backend:
- `app.py` (uses environment variables)
- `requirements.txt`
- `.env.example` (template only)
- `lambda_agent1/lambda_function.py` (no hardcoded tokens)

#### ✅ Frontend:
- All `aws/src/*.jsx` files
- `package.json`
- `vite.config.js`
- `tailwind.config.cjs`

#### ✅ Root:
- `.gitignore`
- `README.md`
- `SECURITY_SETUP.md`

### 4. Files That Must NEVER Be Committed

#### ❌ Credentials:
- `backend/client_secret.json`
- `backend/.env`
- Any file with `GOCSPX-`, `ya29.`, `AKIA`

#### ❌ Temporary/Build:
- `venv/`
- `node_modules/`
- `__pycache__/`
- `*.pyc`
- `*.zip` (Lambda packages)
- `repomix-output.*`

---

## 🔐 Initial Git Setup

### First Time Setup:

```powershell
cd C:\Users\moina\Downloads\aws_agent

# Initialize git (if not already done)
git init

# Add all safe files
git add .

# Check what's being added
git status

# STOP! Review the list carefully
# If you see .env or client_secret.json, DO NOT PROCEED

# Create first commit
git commit -m "Initial commit: Raven AI email manager with security best practices"

# Add remote (create repo on GitHub first)
git remote add origin https://github.com/YOUR_USERNAME/raven-ai.git

# Push to GitHub
git push -u origin main
```

---

## 🚨 If You Accidentally Committed Secrets

### Emergency Fix:

```powershell
# Remove file from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/client_secret.json" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (DANGER: only if repo is private)
git push origin --force --all

# Then immediately:
# 1. Rotate ALL credentials in Google Cloud Console
# 2. Generate new SECRET_KEY
# 3. Update your local .env
```

---

## 📋 Post-Upload Verification

After pushing to GitHub:

1. **Visit your GitHub repo**
2. **Browse files manually**
3. **Search for credentials:**
   - Go to GitHub repo
   - Press `t` to search files
   - Search for: `GOCSPX`, `ya29`, `client_secret`
   
4. **Check Security Tab:**
   - Go to Settings → Security
   - Check "Secret scanning" alerts

---

## 🎯 Quick Safety Check

Run this before EVERY commit:

```powershell
# Check for secrets
git diff --cached | findstr /I "GOCSPX ya29 AKIA secret_key"

# No output = Safe to commit
# Any output = STOP! Review the file
```

---

## ✅ You're Safe to Push When:

- [ ] `.gitignore` exists and includes sensitive files
- [ ] `client_secret.json` contains only `xxxxxxxxx`
- [ ] No `GOCSPX-` or `ya29.` tokens in any committed file
- [ ] `.env` is NOT in `git status` output
- [ ] `repomix-output.xml` is deleted or ignored
- [ ] All Lambda temp folders cleaned
- [ ] `app.py` uses `os.environ.get()` for secrets
- [ ] Team members have `.env.example` to copy

---

## 📞 Help

If unsure, run:
```powershell
git status
git diff --cached
```

Review every file being committed!
