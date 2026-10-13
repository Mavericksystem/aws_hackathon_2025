# Raven AI — Email Management Assistant

Raven AI is an AWS hackathon project that connects to Gmail and uses AWS-backed workflows to help organize email and support user-defined actions.

## Demo

[![Watch the Raven AI demo](https://img.youtube.com/vi/l48lhiu8cbc/hqdefault.jpg)](https://www.youtube.com/watch?v=l48lhiu8cbc)

## Stack

- **Frontend:** React, Vite
- **Backend:** Python, Flask
- **Email:** Gmail API, Google OAuth 2.0
- **AWS:** Lambda, DynamoDB

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
# Activate the virtual environment, then:
pip install -r requirements.txt
```

Create `.env` from `.env.example` and configure your own values. Add your Google OAuth client configuration at the path expected by the application. Do not commit `.env`, OAuth client-secret files, or tokens.

```bash
python app.py
```

### Frontend

```bash
cd aws
npm install
npm run dev
```

Configure the frontend API URL to match your backend environment.

## Security

- Keep credentials out of source control.
- Rotate any credentials that may have been exposed previously.
- Do not use Flask debug mode or insecure OAuth transport in production.
- Review `SECURITY_SETUP.md` and `GITHUB_CHECKLIST.md` before publishing or deploying.

## Project structure

- `aws/` — React frontend
- `backend/` — Flask API and AWS Lambda code
- `SECURITY_SETUP.md` — credential setup and security guidance
