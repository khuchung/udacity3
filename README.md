# TechConf Registration Website

## Project Overview
The TechConf website allows attendees to register for an upcoming conference. Administrators can also view the list of attendees and notify all attendees via a personalized email message.

The application is currently working but the following pain points have triggered the need for migration to Azure:
 - The web application is not scalable to handle user load at peak
 - When the admin sends out notifications, it's currently taking a long time because it's looping through all attendees, resulting in some HTTP timeout exceptions
 - The current architecture is not cost-effective 

In this project, you are tasked to do the following:
- Migrate and deploy the pre-existing web app to an Azure App Service
- Migrate a PostgreSQL database backup to an Azure Postgres database instance
- Refactor the notification logic to an Azure Function via a service bus queue message

## Dependencies

You will need to install the following locally:
- [Postgres](https://www.postgresql.org/download/)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [Azure Function tools V3](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Ccsharp%2Cbash#install-the-azure-functions-core-tools)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)
- [Azure Tools for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-node-azure-pack)

## Project Instructions

### Part 1: Create Azure Resources and Deploy Web App
1. Create a Resource group
2. Create an Azure Postgres Database single server
   - Add a new database `techconfdb`
   - Allow all IPs to connect to database server
   - Restore the database with the backup located in the data folder
3. Create a Service Bus resource with a `notificationqueue` that will be used to communicate between the web and the function
   - Open the web folder and update the following in the `config.py` file
      - `POSTGRES_URL`
      - `POSTGRES_USER`
      - `POSTGRES_PW`
      - `POSTGRES_DB`
      - `SERVICE_BUS_CONNECTION_STRING`
4. Create App Service plan
5. Create a storage account
6. Deploy the web app

### Part 2: Create and Publish Azure Function
1. Create an Azure Function in the `function` folder that is triggered by the service bus queue created in Part 1.

      **Note**: Skeleton code has been provided in the **README** file located in the `function` folder. You will need to copy/paste this code into the `__init.py__` file in the `function` folder.
      - The Azure Function should do the following:
         - Process the message which is the `notification_id`
         - Query the database using `psycopg2` library for the given notification to retrieve the subject and message
         - Query the database to retrieve a list of attendees (**email** and **first name**)
         - Loop through each attendee and send a personalized subject message
         - After the notification, update the notification status with the total number of attendees notified
2. Publish the Azure Function

### Part 3: Refactor `routes.py`
1. Refactor the post logic in `web/app/routes.py -> notification()` using servicebus `queue_client`:
   - The notification method on POST should save the notification object and queue the notification id for the function to pick it up
2. Re-deploy the web app to publish changes

## Monthly Cost Analysis
Monthly cost analysis in a production-level environment as table below:

| Azure Resource                              | Service Tier                                                                             | Monthly Cost         |
| ------------                                | ------------                                                                             | ------------         |
| Storage account                             | Standard, General Purpose V2, 64GB                                                       | $2.38                |
| Azure Functions                             | Consumption Plan w Memory 1GB, Execution time 2000ms, 1,000,000 execution/month          | $25.60               |
| Azure Database for PostgreSQL single server | General Purpose, Gen 5, 2 vCore, $0.1752/hour x 730h, 64GB Storage, 128GB Backup storage | $148.06              |
| App Service                                 | P1V2: 1 Cores(s), 3.5 GB RAM, 250 GB Storage, $0.115                                     | $83.95               |
| Azure Service Bus                           | Standard                                                                                 | $9.81                |
=> Total: $269.8
## Architecture Explanation
This is a placeholder section where you can provide an explanation and reasoning for your architecture selection for both the Azure Web App and Azure Function.
- Azure Web App is the place where I can deploy a web application. It's a flask app that connects with PostgreSQL database where I can store and retrieve the database.
- User can registers to our web app, and it'll add to the `attendee` table in the database
- Azure function is based on serverless architecture. I use the service bus trigger here. It uses for sending the email notification to the list of attendees once it's triggered. Also, update the database to show how many attendees were notified to the database.
- When the new notification is created. I'll save the information into the database. Also, create a message to Azure service bus. It's saved into a queue. The queue triggers Azure function app.

### Drawbacks of the existing architecture
- With that architecture, the email send by the application when creating a notification. With every attendee, one email is sent. It takes a lot of time to process when there're a lot of attendees, eg: 1000. It is bad for the user experience because the browser will hang/not response for a while. It can lead to time out if it takes more than 300s. Also, user cannot create multiple notifications in a short time.

### With background job to send email by using Azure Service Bus
- When using new architecture, the web application just need to save the notification into the DB and create a message to queue. The web application returns success to user in no time.
- When the queue is created, it will trigger Azure Function. Here, it can take time to send email to all attendees. After finish, the Azure function have to update database to update the status and the completed time of the notification. So that the user can understand all the emails sent.
- Advantages: Users can create notifications without waiting for server sending email. The email will be accomplished by Azure Service Bus and Azure Functions(with `serviceBusTrigger` setup)
- Disadvantages: need to pay for extra services: Azure Function and Azure Service Bus. But the price is fair($35.41/month) and it is worth the value.
