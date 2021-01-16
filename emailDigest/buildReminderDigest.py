import logging
import requests
import re
import json
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email


def getRemoteData(url, headers, payload):
    tempData = []
    response = requests.request("GET", url, headers=headers, data=payload)
    # logging.info("Response Status: {}".format(response.status_code))

    tempData.extend(response.json()['data'])
    nextUrl = response.json()['links']['next']

    while nextUrl:
        response = requests.request("GET", nextUrl, headers=headers, data=payload)
        logging.info("Response Status: {}".format(response.status_code))
        tempData.extend(response.json()['data'])
        nextUrl = response.json()['links']['next']
    
    return tempData

def lambda_handler():
    envfile = '.env'
    contactsStub = "contacts"
    reminderStub = "reminders"
    followups = []
    events = []
    contacts = []
    reminders = []

    with open(envfile, "r") as ifile:
        envDict = json.load(ifile)

    cDatetime = datetime.now()

    header = "<p><b>Contact and Event Reminders for {}</b><br/>From Monica CRM - <a href='{}'>{}</a></p><table><tr style='background-color:#ECECEC'><th align=\"center\">Date</th><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td><th align=\"center\">Event</th><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td><th align=\"center\">Person</th><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td><th align=\"center\">Days Until</th></tr>".format(cDatetime.strftime("%Y-%m-%d"), envDict['appurl'], envDict['appurl'])

    contactsUri = "{}{}".format(envDict['url'],contactsStub)
    remindersUri = "{}{}".format(envDict['url'],reminderStub)
    payload={}
    headers = {'Authorization': "Bearer {}".format(envDict['token'])}
    # header 
    contacts = getRemoteData(url=contactsUri, headers=headers, payload=payload)
    reminders = getRemoteData(url=remindersUri, headers=headers, payload=payload)
    # Process stay in touch dates
    for contact in contacts: 
        if 'stay_in_touch_trigger_date' in contact:
            if contact['stay_in_touch_trigger_date']:
                # logging.info("{} - {} {}".format(contact['stay_in_touch_trigger_date'], contact["first_name"], contact["last_name"]))
                targetDate = datetime.strptime(contact['stay_in_touch_trigger_date'], '%Y-%m-%dT%H:%M:%SZ')
                days = targetDate.date() - cDatetime.date()
                if days <= timedelta(days=envDict['contactDays']) and days >= timedelta(days=0):
                    # followups.append(contact)
                    followups.append({'date':contact['stay_in_touch_trigger_date'].split('T')[0], 'event':"contact", 'firstname':contact["first_name"], 'lastname':contact["last_name"], 'days':days.days})
                    logging.info("{} {} - Next Contact: {}".format(contact["first_name"],contact["last_name"],contact['stay_in_touch_trigger_date'].split('T')[0]))

    # Process reminders (birthdays, etc)
    for item in reminders:
        initial_date = datetime.strptime(item['initial_date'], '%Y-%m-%dT%H:%M:%SZ').replace(year=cDatetime.year)
        # logging.info("{}".format(initial_date.date() - cDatetime.date()))
        days = initial_date.date() - cDatetime.date()
        if days <= timedelta(days=envDict['reminderDays']) and days >= timedelta(days=0):
            # logging.info("{}".format(days.days))
            if re.search(r'birthday', item['title'], re.I):
                event = "birthday"
            else:
                event = item['title']
            followups.append({'date':initial_date.strftime('%Y-%m-%d'), 'event': event, 'firstname':item['contact']["first_name"], 'lastname':item['contact']["last_name"], 'days':days.days})

    # Create HTML rows from events
    events = sorted(followups, key = lambda i: i['date'])
    for row in events:
        # print(row)
        if row['days'] <= envDict['cardReminderDays'] and not re.search(r'contact', row['event'], re.I):
            htmlrow = "<tr style='background-color:#D1FEAA'><td>{}</td><td></td><td>{}</td><td></td><td>{}</td><td></td><td align='center'>{}</td></tr>".format(row['date'], row['event'].capitalize(), "{} {}".format(row['firstname'], row['lastname']), row['days'])
        else:
            htmlrow = "<tr><td>{}</td><td></td><td>{}</td><td></td><td>{}</td><td></td><td align='center'>{}</td></tr>".format(row['date'], row['event'].capitalize(), "{} {}".format(row['firstname'], row['lastname']), row['days'])

        header = header + htmlrow
    header = header + "</table>"
    # f = open("/app/test.html", "w")
    # f.write(''.join(header))
    # f.close()
    # print(''.join(header))
    msg = EmailMessage()
    msg['From'] = envDict["MAIL_FROM_ADDRESS"]
    msg['To'] = envDict["receiver_email"]
    msg['Subject'] = "{} - {}".format(envDict["mail_subject"], cDatetime.strftime("%Y-%m-%d"))
    # message = "{}".format(''.join(header))
    # print(type(header))
    # print(header)
    msg.set_content(MIMEText(header, 'html'))


    try:
        # Attempt to send email for prod
        smtpObj = smtplib.SMTP(envDict['MAIL_HOST'], envDict['MAIL_PORT'])
        smtpObj.starttls()
        smtpObj.login(envDict["MAIL_USERNAME"], envDict['MAIL_PASSWORD'])
        smtpObj.send_message(msg)
        logging.info("Successfully sent email")
        results =  {"Success": 200}

    except Exception as e:
        logging.info("Exception: {}".format(e))
        results = {"Internal Server Error": 500}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()], format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",)
    lambda_handler()