import os
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, Form
from pydantic import BaseModel
from google.cloud import firestore
from google.cloud import pubsub_v1
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Union
import json
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import base64

# Load environment variables from .env file
load_dotenv()

# Set Google Application Credentials from .env
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Initialize FastAPI
app = FastAPI()

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

super_admin_users_db = {
    "pr_emailer": {
        "username": "pr_emailer",
        "full_name": "Precise Emailer",
        "email": "nazmus_admin@test.com",
        "hashed_password": "$2b$12$Neu5oNZbzbEd9e1jeZCFteAO0pkJzf/MoqRFmTnKTc5FC3pa01iQG", # 6rCv5B^0!qLo encoded val b'NnJDdjVCXjAhcUxv'
        "disabled": False,
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None

class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None

class UserInDB(User):
    hashed_password: str

class EmailRequest(BaseModel):
    email: str
    body: str
    schedule_time: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Firestore and Pub/Sub setup
db = firestore.Client()
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('cloud-technology-436021', 'email-queue')

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    print(pwd_context.hash(password))
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(super_admin_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.get("/")
async def root(current_user: User = Depends(get_current_active_user)):
    return {"message": "Precise emailer running..."}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(super_admin_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/send-email/")
async def send_email(
    email: str = Form(...),
    body: str = Form(...),
    attachment: UploadFile = None,
    schedule_time: str = Form(...), # 2025-12-15 15:30:00
    # current_user: User = Depends(get_current_active_user)
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
        attachment_url = f"gs://my-bucket-name/{attachment.filename}"
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
async def process_scheduled_emails(current_user: User = Depends(get_current_active_user)):
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
async def pubsub_handler(
    message: dict, 
    # current_user: User = Depends(get_current_active_user) # unlocked to test
    ):
    # Decode the Pub/Sub message
    # pubsub_message = base64.b64decode(message["message"]["data"]).decode("utf-8") # disabled to test sendgrid
    # email_data = json.loads(message)
    email_data = message # only to test directly with swagger UI

    # Extract email details
    email = email_data.get("email")
    body = email_data.get("body")
    # attachment_url = email_data.get("attachment_url")  
    subject = email_data.get("subject", "Scheduled Email") 

    # Compose the email
    message = Mail(
        from_email="takhi44@gmail.com",  # verified sender from Sendgrid
        to_emails=email,
        subject=subject,
        plain_text_content=body
    )

    # Send the email
    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    response = sg.send(message)

    print(f"Status Code: {response}")
    print(f"Body: {response.body}")
    print(f"Headers: {response.headers}")

    return {"message": "Email sent successfully!", "status_code": response.status_code}