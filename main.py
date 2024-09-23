import os
from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
from google.cloud import firestore
from google.cloud import pubsub_v1
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Set Google Application Credentials from .env
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Initialize FastAPI
app = FastAPI()

# Firestore and Pub/Sub setup
db = firestore.Client()
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('your-project-id', 'email-queue')

class EmailRequest(BaseModel):
    email: str
    body: str
    schedule_time: str

@app.post("/send-email/")
async def send_email(
    email: str = Form(...),
    body: str = Form(...),
    attachment: UploadFile = None,
    schedule_time: str = Form(...)
):
    # Parse the schedule_time into a datetime object
    schedule_datetime = datetime.strptime(schedule_time, '%Y-%m-%d %H:%M:%S')

    # Store the email data in Firestore
    doc_ref = db.collection('emails').document()
    email_data = {
        'email': email,
        'body': body,
        'attachment_url': None,
        'schedule_time': schedule_datetime,
        'status': 'pending'
    }

    # Handle file attachment (if present)
    if attachment:
        attachment_data = await attachment.read()
        attachment_url = f"gs://your-bucket-name/{attachment.filename}"
        # Upload the file to a storage bucket here (upload logic not shown)
        email_data['attachment_url'] = attachment_url

    doc_ref.set(email_data)

    # Publish to Pub/Sub
    pubsub_message = {
        'email': email,
        'body': body,
        'schedule_time': schedule_time
    }
    publisher.publish(topic_path, data=json.dumps(pubsub_message).encode('utf-8'))

    return {"message": "Email scheduled successfully!"}

@app.get("/process-scheduled-emails/")
async def process_scheduled_emails():
    now = datetime.utcnow()

    # Query Firestore for emails to send
    emails_ref = db.collection('emails').where('schedule_time', '<=', now).where('status', '==', 'pending')
    emails = emails_ref.stream()

    for email in emails:
        email_data = email.to_dict()
        publisher.publish(topic_path, data=json.dumps(email_data).encode('utf-8'))

        # Mark email as sent in Firestore
        email.reference.update({'status': 'sent'})

    return {"message": "Scheduled emails processed."}

@app.post("/pubsub-handler/")
async def pubsub_handler(message: dict):
    # Parse message data
    email_data = json.loads(message['data'])
    
    # Logic to send the email (use an email provider like SendGrid or Gmail here)
    
    return {"message": "Email processed."}