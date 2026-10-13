# Raven AI — Email Management Assistant

**Raven AI** is an AWS hackathon project that connects to Gmail and helps users manage email through a React interface, a Flask API, and AWS-backed workflows.

## Demo

[![Watch the Raven AI demo](https://img.youtube.com/vi/l48lhiu8cbc/maxresdefault.jpg)](https://www.youtube.com/watch?v=l48lhiu8cbc)

*Click the thumbnail to watch the demo on YouTube. GitHub README Markdown does not provide a standard inline YouTube player.*

## What it does

- Connects to Gmail using Google OAuth 2.0.
- Provides a web interface for email-related workflows.
- Uses AWS Lambda and DynamoDB for backend processing and persistence.

## Architecture

```text
React + Vite frontend
        ↓
Flask API ───── Gmail API (Google OAuth 2.0)
        ↓
AWS services: Lambda + DynamoDB
```

## Tech stack

- **Frontend:** React 19, Vite
- **Backend:** Python, Flask
- **Email integration:** Gmail API, Google OAuth 2.0
- **AWS:** Lambda, DynamoDB

## Run locally

### Prerequisites

- Python and pip
- Node.js and npm
- AWS credentials with access to the required DynamoDB resources
- A Google Cloud project with the Gmail API enabled and OAuth credentials configured

### 1. Configure the backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file from the example:

```bash
# From the repository root
cp backend/.env.example backend/.env
```

Set a strong `SECRET_KEY` and configure the values for your environment. Add your Google OAuth client configuration as `backend/client_secret.json`, where the application expects it. Configure AWS credentials locally (for example, with `aws configure`). **Do not commit real credentials, OAuth files, tokens, or `.env` files.**

Start the backend from the `backend/` directory:

```bash
python app.py
```

The Flask API runs on port `5000` by default.

### 2. Start the frontend

Open a second terminal:

```bash
cd aws
npm install
npm run dev
```

If needed, update the frontend's API URL to point to your local backend.

## Security

- Keep `.env` and `client_secret.json` local; commit only example configuration with placeholders.
- Rotate credentials that may have been exposed in the past.
- `OAUTHLIB_INSECURE_TRANSPORT` is for local development only; do not use insecure OAuth transport or Flask debug mode in production.
- Review [Security Setup](SECURITY_SETUP.md) and [GitHub Upload Checklist](GITHUB_CHECKLIST.md) before publishing or deploying.

## Project structure

- `aws/` — React + Vite frontend
- `backend/` — Flask API and Lambda code
- `SECURITY_SETUP.md` — credential setup and security guidance
- `GITHUB_CHECKLIST.md` — repository security checklist

## License

See [LICENSE](LICENSE).
