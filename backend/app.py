# backend/app.py
from flask import Flask, redirect, request, session, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import json
import boto3
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return "Raven AI backend is running!"

# Security: Use environment variable for secret key (NO FALLBACK)
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is not set! Create a .env file with SECRET_KEY.")

app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_HTTPONLY=True
)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # only for local dev

# Enable CORS for frontend origins (from env or default)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
CORS(app, supports_credentials=True, origins=[FRONTEND_URL, "http://localhost:3000"])

# DynamoDB setup (from environment variables)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DYNAMO_TABLE_USER_CREDS = os.environ.get("DYNAMO_TABLE_USER_CREDS", "UserCredentials")
DYNAMO_TABLE_USER_PROFILES = os.environ.get("DYNAMO_TABLE_USER_PROFILES", "UserProfiles")

try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    user_creds_table = dynamodb.Table(DYNAMO_TABLE_USER_CREDS)
    user_profiles_table = dynamodb.Table(DYNAMO_TABLE_USER_PROFILES)
    print("✅ DynamoDB connection initialized")
except Exception as e:
    print(f"❌ Failed to initialize DynamoDB: {e}")
    print("⚠️ Make sure AWS credentials are configured!")
    print("   Run: aws configure")
    # Don't exit, let the app start but show errors on requests

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:5000/oauth2callback")

# ============= HELPER FUNCTIONS =============

def get_user_id_from_session():
    """Get user ID from session (email address)"""
    return session.get('user_email', 'test_user')

def save_credentials_to_dynamodb(user_id, creds):
    """Save OAuth credentials to DynamoDB"""
    try:
        expiry_str = creds.expiry.isoformat() if creds.expiry else None
        
        user_creds_table.put_item(Item={
            'userId': user_id,
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': expiry_str,
            'updatedAt': datetime.now().isoformat()
        })
        print(f"✅ Credentials saved to DynamoDB for user: {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False

def load_credentials_from_dynamodb(user_id):
    """Load OAuth credentials from DynamoDB"""
    try:
        response = user_creds_table.get_item(Key={'userId': user_id})
        
        if 'Item' not in response:
            print(f"⚠️ No credentials found for user: {user_id}")
            return None
        
        item = response['Item']
        
        # Convert expiry string back to datetime
        expiry = datetime.fromisoformat(item['expiry']) if item.get('expiry') else None
        
        creds = Credentials(
            token=item['access_token'],
            refresh_token=item['refresh_token'],
            token_uri=item['token_uri'],
            client_id=item['client_id'],
            client_secret=item['client_secret'],
            scopes=item['scopes']
        )
        creds.expiry = expiry
        
        print(f"✅ Credentials loaded from DynamoDB for user: {user_id}")
        return creds
        
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None

def refresh_credentials_if_needed(creds, user_id):
    """Check if credentials are expired and refresh them"""
    try:
        # Check if token is expired or about to expire (within 5 minutes)
        if creds.expired or (creds.expiry and creds.expiry < datetime.utcnow() + timedelta(minutes=5)):
            print(f"🔄 Token expired or expiring soon, refreshing for user: {user_id}")
            creds.refresh(Request())
            save_credentials_to_dynamodb(user_id, creds)
            print(f"✅ Token refreshed successfully")
        else:
            print(f"✅ Token still valid")
        
        return creds
    except Exception as e:
        print(f"❌ Error refreshing credentials: {e}")
        return None

# ============= ROUTES =============

# Step 1: Login redirect
@app.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type='offline',  # ✅ CRITICAL: Get refresh token
        include_granted_scopes='true'
    )
    return redirect(auth_url)

# Step 2: OAuth2 callback
@app.route("/oauth2callback")
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    
    # Get user email to use as userId
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    user_email = profile['emailAddress']
    
    # Save credentials to DynamoDB
    save_credentials_to_dynamodb(user_email, creds)
    
    # Store user email in session
    session['user_email'] = user_email
    session['authenticated'] = True
    
    print(f"✅ User {user_email} authenticated and credentials saved")
    
    return redirect("http://localhost:5173")  # Redirect to frontend

# Step 3: Fetch emails from DynamoDB (not Gmail API)

# Replace your /emails route with this fixed version

@app.route("/emails")
def get_emails():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated", "login_url": "/login"}), 401
    
    user_id = get_user_id_from_session()
    
    try:
        # Query DynamoDB RawEmails table
        raw_emails_table = dynamodb.Table('RawEmails')
        
        response = raw_emails_table.query(
            KeyConditionExpression=Key('userId').eq(user_id),
            ScanIndexForward=False,  # Latest first
            Limit=30
        )
        
        emails = []
        for item in response.get('Items', []):
            try:
                # Safely get all fields with defaults
                agent_analysis = item.get('agentAnalysis', '')
                
                email_data = {
                    "id": item.get('emailId', ''),
                    "subject": item.get('subject', 'No Subject'),
                    "from": item.get('from', 'Unknown'),
                    "body": item.get('body', ''),
                    "bodyHtml": item.get('bodyHtml', ''),
                    "jobTitle": item.get('jobTitle', ''),
                    # "jobCompany": item.get('jobCompany', ''),
                    "jobLocation": item.get('jobLocation', ''),
                    "jobUrl": item.get('jobUrl', ''),
                    "jobPageContent": item.get('jobPageContent', ''),
                    "processed": item.get('processed', False),
                    "processedAt": item.get('processedAt', ''),
                    "agentAnalysis": agent_analysis if isinstance(agent_analysis, str) else '',
                    "matchScore": 0,
                    "llmSuggestion": ""
                }
                
                # Extract recommendation from text if available
                if agent_analysis and isinstance(agent_analysis, str) and len(agent_analysis) > 0:
                    analysis_lower = agent_analysis.lower()
                    if 'not a good match' in analysis_lower or "wouldn't recommend" in analysis_lower or "no, i wouldn" in analysis_lower:
                        email_data['llmSuggestion'] = 'NOT_RECOMMENDED'
                        email_data['matchScore'] = 30
                    elif 'strong match' in analysis_lower or 'highly recommend' in analysis_lower:
                        email_data['llmSuggestion'] = 'HIGHLY_RECOMMENDED'
                        email_data['matchScore'] = 85
                    elif 'good match' in analysis_lower or 'recommend applying' in analysis_lower:
                        email_data['llmSuggestion'] = 'RECOMMENDED'
                        email_data['matchScore'] = 70
                    else:
                        email_data['llmSuggestion'] = 'REVIEW'
                        email_data['matchScore'] = 50
                
                emails.append(email_data)
                
            except Exception as item_error:
                print(f"⚠️ Error processing item: {item_error}")
                continue
        
        print(f"✅ Fetched {len(emails)} emails from DynamoDB for user: {user_id}")
        return jsonify(emails)
    
    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# NEW: Trigger Lambda to fetch new emails from Gmail
@app.route("/fetch-new-emails", methods=["POST"])
def trigger_email_fetch():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = get_user_id_from_session()
    
    try:
        # Invoke EmailFetcher Lambda
        lambda_client = boto3.client('lambda', region_name='us-east-1')  # Change region
        
        payload = {
            'userId': user_id
        }
        
        response = lambda_client.invoke(
            FunctionName='Agent1_EmailFetcher',  # Change to your Lambda name
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        print(f"✅ Lambda invoked for user: {user_id}")
        return jsonify({
            "message": "Email fetch triggered",
            "status": "processing",
            "userId": user_id
        })
    
    except Exception as e:
        print(f"❌ Error invoking Lambda: {e}")
        return jsonify({"error": str(e)}), 500

# Save desired role to DynamoDB UserProfiles
@app.route("/user/desiredRole", methods=["POST"])
def save_desired_role():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.json or {}
    desired_role = (data.get("desiredRole") or "").strip()
    
    if not desired_role:
        return jsonify({"error": "No role provided"}), 400
    
    user_id = get_user_id_from_session()
    
    try:
        # Create or update user profile in DynamoDB
        user_profiles_table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET desiredRole = :role, updatedAt = :time',
            ExpressionAttributeValues={
                ':role': desired_role,
                ':time': datetime.now().isoformat()
            }
        )
        
        print(f"✅ Desired role saved for user {user_id}: {desired_role}")
        return jsonify({"message": "Desired role saved", "desiredRole": desired_role})
    
    except Exception as e:
        print(f"❌ Error saving desired role: {e}")
        return jsonify({"error": str(e)}), 500

# Get user profile
@app.route("/user/profile")
def get_user_profile():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = get_user_id_from_session()
    
    try:
        response = user_profiles_table.get_item(Key={'userId': user_id})
        
        if 'Item' in response:
            return jsonify(response['Item'])
        else:
            # Return default profile
            return jsonify({
                "userId": user_id,
                "desiredRole": "",
                "email": user_id
            })
    
    except Exception as e:
        print(f"❌ Error fetching profile: {e}")
        return jsonify({"error": str(e)}), 500

# Check authentication status
@app.route("/auth/status")
def auth_status():
    return jsonify({
        "authenticated": session.get('authenticated', False),
        "userEmail": session.get('user_email')
    })

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)