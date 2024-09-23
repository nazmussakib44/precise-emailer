# Precise Emailer
A serverless precise scheduling system for your emails using Google cloud firestore, scheduler &amp; pub/sub. 

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
## API Documentation

Visit project home url /docs e.g. http://127.0.0.1:8000/docs and you will find swagger UI to test all the available API's

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

## How to setup Cloud Scheduler (Not implemented)
- Go to Cloud Scheduler dashboard (As you already enabled the service)
- Create cron job. 
- Select your timezone. 
- Set occurence every 5 minutes (Recommended for accuracy. You may change based on your needs). 
- Select job target to our endpint ('/process-scheduled-emails/')
- And you are done with Cloud Scheduler.

## How to setup Cloud Pub/Sub (Not implemented)
- Go to Cloud Pub/Sub dashboard (As you already enabled the service)
- Create a topic.  
- Set retry timer 10 minutes (Recommended). 
- Set execution target to our endpoint ('/pubsub-handler/') to send the email. 

## How to setup SendGrid (Not implemented)
- In progress. 



Now you are ready to go...

