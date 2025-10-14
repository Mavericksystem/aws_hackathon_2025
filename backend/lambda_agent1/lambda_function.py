import os
import json
import requests
import boto3
import base64
import re
from urllib.parse import unquote, urlparse, parse_qs
from html.parser import HTMLParser
from datetime import datetime, timedelta

# === CONFIG ===
DYNAMO_TABLE_RAW_EMAILS = "RawEmails"
DYNAMO_TABLE_USER_CREDS = "UserCredentials"

dynamodb = boto3.resource("dynamodb")
raw_emails_table = dynamodb.Table(DYNAMO_TABLE_RAW_EMAILS)
user_creds_table = dynamodb.Table(DYNAMO_TABLE_USER_CREDS)

# ============= OAUTH FUNCTIONS =============

def get_access_token(user_id):
    """
    Get valid access token from DynamoDB
    Automatically refreshes if expired
    """
    try:
        response = user_creds_table.get_item(Key={'userId': user_id})
        
        if 'Item' not in response:
            print(f"❌ No credentials found for user: {user_id}")
            return None
        
        item = response['Item']
        access_token = item['access_token']
        refresh_token = item['refresh_token']
        expiry_str = item.get('expiry')
        
        # Check if token is expired
        if expiry_str:
            expiry = datetime.fromisoformat(expiry_str)
            if expiry < datetime.utcnow() + timedelta(minutes=5):
                print(f"🔄 Token expired, refreshing for user: {user_id}")
                access_token = refresh_access_token(user_id, item)
        
        return access_token
    
    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        return None

def refresh_access_token(user_id, creds_item):
    """Refresh OAuth token using refresh_token"""
    try:
        refresh_token = creds_item['refresh_token']
        client_id = creds_item['client_id']
        client_secret = creds_item['client_secret']
        token_uri = creds_item['token_uri']
        
        # Make refresh request
        response = requests.post(token_uri, data={
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        })
        
        if response.status_code == 200:
            token_data = response.json()
            new_access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            
            # Calculate new expiry
            new_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Update DynamoDB
            user_creds_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET access_token = :token, expiry = :expiry, updatedAt = :time',
                ExpressionAttributeValues={
                    ':token': new_access_token,
                    ':expiry': new_expiry.isoformat(),
                    ':time': datetime.now().isoformat()
                }
            )
            
            print(f"✅ Token refreshed successfully for user: {user_id}")
            return new_access_token
        else:
            print(f"❌ Token refresh failed: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error refreshing token: {e}")
        return None

# ============= JOB EXTRACTION FUNCTIONS =============

def clean_redirect_url(url: str) -> str:
    """Decode redirect URLs"""
    if "eightfold.ai/vsimp" in url:
        try:
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            if "n" in query:
                return unquote(query["n"][0])
        except Exception as e:
            print(f"⚠️ Redirect decode failed: {e}")
    return url

def extract_job_url(body):
    """Extract job URL from email"""
    patterns = [
        r'https?://[^\s<>]+/vsimp[^\s<>]*',
        r'https?://[^\s<>]+/jobs?/[^\s<>]+',
        r'https?://[^\s<>]+/careers?/[^\s<>]+',
        r'https?://greenhouse\.io/[^\s<>]+',
        r'https?://lever\.co/[^\s<>]+',
        r'https?://linkedin\.com/jobs/view/[^\s<>]+',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            url = match.group(0).rstrip('.,;)>\'\"').split('>')[0]
            return url
    return None

def extract_job_id_from_url(url):
    """Extract position ID from URL"""
    match = re.search(r'[?&]pid=(\d+)', url)
    if match:
        return match.group(1)
    
    match = re.search(r'/positions?/(\d+)', url)
    if match:
        return match.group(1)
    
    return None

def clean_html(text):
    """Remove HTML tags from text"""
    if not text:
        return ""
    
    class HTMLStripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = []
        def handle_data(self, data):
            self.text.append(data)
        def get_text(self):
            return '\n'.join(self.text)
    
    stripper = HTMLStripper()
    try:
        stripper.feed(text)
        return stripper.get_text().strip()
    except:
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()

def extract_position_from_response(data):
    """Extract position details from API response"""
    if 'description' in data or 'job_description' in data:
        position_data = data
    elif 'position' in data:
        position_data = data['position']
    elif 'job' in data:
        position_data = data['job']
    elif 'positions' in data and isinstance(data['positions'], list) and len(data['positions']) > 0:
        position_data = data['positions'][0]
    elif 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
        position_data = data['data'][0]
    elif 'data' in data and isinstance(data['data'], dict):
        position_data = data['data']
    else:
        position_data = data
    
    job_info = {
        'description': (
            position_data.get('description') or
            position_data.get('job_description') or
            position_data.get('jobDescription') or
            position_data.get('details') or
            position_data.get('content') or
            position_data.get('summary') or
            ''
        ),
        'title': (
            position_data.get('title') or
            position_data.get('name') or
            position_data.get('job_title') or
            position_data.get('position_title') or
            position_data.get('jobTitle') or
            ''
        ),
        'location': (
            position_data.get('location') or
            position_data.get('city') or
            position_data.get('locations') or
            position_data.get('office_location') or
            ''
        ),
        'company': (
            position_data.get('company') or
            position_data.get('organization') or
            position_data.get('employer') or
            'Unknown Company'
        ),
        'requirements': (
            position_data.get('requirements') or
            position_data.get('qualifications') or
            position_data.get('minimum_qualifications') or
            position_data.get('required_skills') or
            ''
        ),
        'salary': (
            position_data.get('salary') or
            position_data.get('compensation') or
            position_data.get('pay_range') or
            ''
        ),
        'experience': (
            position_data.get('experience') or
            position_data.get('years_of_experience') or
            position_data.get('experience_level') or
            ''
        ),
    }
    
    if job_info['description']:
        job_info['description'] = clean_html(job_info['description'])
    if job_info['requirements']:
        job_info['requirements'] = clean_html(str(job_info['requirements']))
    
    return job_info

def get_eightfold_job_data(job_url):
    """Try multiple Eightfold API endpoints to get job data"""
    try:
        position_id = extract_job_id_from_url(job_url)
        if not position_id:
            print("⚠️ Could not extract position ID from URL")
            return None
        
        print(f"🔑 Position ID: {position_id}")
        
        parsed_url = urlparse(job_url)
        base_domain = parsed_url.netloc
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': job_url,
            'Origin': f"https://{base_domain}",
        }
        
        api_patterns = [
            f"https://{base_domain}/api/v2/core/positions/{position_id}",
            f"https://{base_domain}/api/apply/v2/jobs/{position_id}",
            f"https://{base_domain}/api/v2/positions/{position_id}",
            f"https://{base_domain}/api/jobs/{position_id}",
        ]
        
        for api_url in api_patterns:
            try:
                print(f"🌐 Trying: {api_url}")
                response = requests.get(api_url, headers=headers, timeout=12)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ API SUCCESS: {api_url}")
                    
                    position_data = extract_position_from_response(data)
                    
                    if position_data and position_data.get('description') and len(position_data['description']) > 100:
                        print(f"📄 Description length: {len(position_data['description'])} chars")
                        return position_data
                        
            except Exception as e:
                print(f"⚠️ Request failed: {e}")
                continue
        
        print("❌ All API endpoints failed")
        return None
        
    except Exception as e:
        print(f"❌ Error in get_eightfold_job_data: {str(e)}")
        return None

# ============= MAIN LAMBDA HANDLER =============

def lambda_handler(event, context):
    """
    Fetch emails from Gmail and store in DynamoDB
    Event should contain: { "userId": "user@gmail.com" }
    """
    try:
        # Get userId from event
        user_id = event.get('userId', 'test_user')
        print(f"🚀 Starting email fetch for user: {user_id}")
        
        # Get valid access token
        access_token = get_access_token(user_id)
        if not access_token:
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Failed to get access token"})
            }
        
        # Fetch unread emails from Gmail
        resp = requests.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=5&q=is:unread",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        resp.raise_for_status()
        messages = resp.json().get("messages", [])

        if not messages:
            print("📭 No new emails")
            return {"statusCode": 200, "body": json.dumps("No new emails.")}

        emails_processed = 0
        
        for message in messages:
            msg_id = message["id"]
            
            # Check if already processed
            existing = raw_emails_table.get_item(Key={'userId': user_id, 'emailId': msg_id})
            if 'Item' in existing:
                print(f"⏭️ Email {msg_id} already processed, skipping")
                continue
            
            # Get email details
            msg_resp = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            msg_resp.raise_for_status()
            msg_data = msg_resp.json()

            # Extract email metadata
            headers_list = msg_data.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "(No Subject)")
            sender = next((h["value"] for h in headers_list if h["name"] == "From"), "(Unknown)")

            # Extract email body
            def extract_plain(payload):
                if "body" in payload and payload["body"].get("data"):
                    if payload.get("mimeType") == "text/plain":
                        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
                if "parts" in payload:
                    for part in payload["parts"]:
                        content = extract_plain(part)
                        if content:
                            return content
                return ""

            body = extract_plain(msg_data.get("payload", {})) or msg_data.get("snippet", "")

            # Extract and clean job URL
            job_url = extract_job_url(body)
            if job_url:
                print(f"🔗 Raw URL: {job_url}")
                job_url = clean_redirect_url(job_url)
                print(f"✅ Cleaned URL: {job_url}")

            # Get job data from API
            job_data = None
            if job_url and 'eightfold.ai' in job_url:
                job_data = get_eightfold_job_data(job_url)

            # Save to DynamoDB
            item = {
                "userId": user_id,
                "emailId": msg_id,
                "subject": subject,
                "from": sender,
                "body": body,
                "processed": False,
                "createdAt": datetime.now().isoformat()
            }
            
            if job_url:
                item["jobUrl"] = job_url
            
            if job_data:
                item["jobPageContent"] = job_data.get('description', '')
                item["jobTitle"] = job_data.get('title', '')
                item["jobLocation"] = job_data.get('location', '')
                item["jobCompany"] = job_data.get('company', '')
                if job_data.get('requirements'):
                    item["jobRequirements"] = str(job_data['requirements'])

            raw_emails_table.put_item(Item=item)
            print(f"✅ Email {msg_id} saved to DynamoDB")
            emails_processed += 1

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Processed {emails_processed} new emails",
                "userId": user_id
            })
        }

    except Exception as e:
        print(f"❌ Lambda error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}