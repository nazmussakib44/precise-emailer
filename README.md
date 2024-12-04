# Precise Emailer
A serverless precise scheduling system for your emails using Cloud Firestore, Scheduler &amp; Pub/Sub. 

## Features

- Schedule your emails. 
- Capable to balance heavy loads. 
- Zero failure guaranteed as the system is using google cloud services. 

## Installation

Clone this project & follow below steps

```sh
cd precise-emailer
pip install -r requirements.txt
```

To run in development

```sh
uvicorn main:app --reload
```

To run in production

```sh
uvicorn main:app
```

## Architecture

![Architecture](/images/architecture.png?raw=true "Architecture")

## API Documentation

Visit project home url /docs e.g. http://127.0.0.1:8000/docs and you will find swagger UI to test all the available API's

![Server Running](/images/swagger_ui.png?raw=true "Server Running")

## Authorization

Press authorization button in swagger ui and put superadmin username & password to authorize. (Currently disabled)

## Integration & Usage

Install the system as a micro-service inside your application following above documentation. And call the rest endpoints to send, schedule and process emails. All cloud service and Sendgrid is configured and managed inside the system to manage the loads. 

As you can see the .env file is already there just get the credentials from your google cloud console to go. 

## How to get credentials 
- Go to https://console.cloud.google.com 
- Select a project or create a new one to configure all the services. 
- Under the current project, go to APIs and services. 
- Enable firestore, scheduler & cloud pub/sub api. 
- Go to credentials and press '+ Create credential' button. 
- You may generate the credential as a "owner" role as the system support Oauth 2.0 for authentication. Or manually confirm that it is allowed access all the enabled service apis. 
- Go to keys tab and get new key as json formate. 
- Rename the file as credentials.json and place in the root folder. 

## How to setup Firestore 
- Go to Firestore dashboard (As you already enabled the service).  
- Create default database with recommended configuration. (Manual database creation is not supported yet. Submit an issue to request the feature.)
- And you are done with Firestore. 

## How to setup Cloud Scheduler 
- Go to Cloud Scheduler dashboard (As you already enabled the service)
- Create cron job. 
- Select your timezone. 
- Set occurence every 5 minutes (Recommended for accuracy. You may change based on your needs). 
- Select job target to our endpint ('/process-scheduled-emails/')
- And you are done with Cloud Scheduler.

## How to setup Cloud Pub/Sub
- Go to Cloud Pub/Sub dashboard (As you already enabled the service)
- Create a topic.  
- Create subscription. 
- Select subscription type - push 
- Set endpoint url - https://your-domain/pubsub-handler
- Set acknowledgement deadline to 10 seconds (If the response status code is not 200 ok, the pubsub will retry) 

![Pubsub Creation](/images/pubsub_sub_creation.png?raw=true "Pubsub Creation")

![Acknowledgement Deadline](/images/subs_ack.png?raw=true "Acknowledgement Deadline")

## How to setup SendGrid 
- Login to SendGrid
- Generate API key through Full Access
- Add the saved API key to projects .env file
- Go to settings, Sender Verification. 
- Add Sender to details to verify your sender email. 
- Add the verified email to projects .env file (Which will be used as from Email to deliver the emails)
- Manually trigger the pubsub handler endpoint from swagger ui to test the emails are deliverying or not. 

![SendGrid API Key](/images/sendgrid_api_key.png?raw=true "SendGrid API Key")

![SendGrid Sender Verification](/images/sendgrid_sender_verification.png?raw=true "SendGrid Sender Verification")

Now you are ready to go...

