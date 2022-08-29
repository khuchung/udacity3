import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime, timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def main(msg: func.ServiceBusMessage):
    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('Python ServiceBus queue trigger processed message: %s', notification_id)

    POSTGRES_URL = os.environ['POSTGRES_URL']
    POSTGRES_USER = os.environ['POSTGRES_USER']
    POSTGRES_PW = os.environ['POSTGRES_PW']
    POSTGRES_DB = os.environ['POSTGRES_DB']
    api_key = os.environ['SENDGRID_API_KEY']
    from_email = os.environ['ADMIN_EMAIL_ADDRESS']
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode=require".format(POSTGRES_URL, POSTGRES_USER, POSTGRES_DB, POSTGRES_PW)
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT subject, message FROM notification WHERE id = %s;" % (notification_id, ))
        notification = cursor.fetchone()
        email_subject = notification[0]
        email_body = notification[1]

        cursor.execute("SELECT email FROM attendee;")
        attendees = cursor.fetchall()
        total_attendees = cursor.rowcount
        for attendee in attendees:
            send_email(api_key, from_email, attendee[0], email_subject, email_body)

        cursor.execute("UPDATE notification SET status = '%s', completed_date = '%s' WHERE id = %s;" % (f'Notified {total_attendees} attendees', datetime.now(timezone.utc), notification_id))
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        if conn:
            cursor.close()
            conn.close()

def send_email(api_key, from_email, to_email, subject, body):
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body)
    sg = SendGridAPIClient(api_key)
    sg.send(message)
