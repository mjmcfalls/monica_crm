import logging
import requests
import re
import json
import pandas as pd
from datetime import datetime, timedelta
# import pytz
# from pytz import timezone


envfile = '.env'
contactsStub = "contacts"
reminderStub = "reminders"
followups = []
events = []

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

def main():
    contacts = []
    reminders = []

    with open(envfile, "r") as ifile:
        envDict = json.load(ifile)

    cDatetime = datetime.now()
    
    contactsUri = "{}{}".format(envDict['url'],contactsStub)
    remindersUri = "{}{}".format(envDict['url'],reminderStub)
    payload={}
    headers = {'Authorization': "Bearer {}".format(envDict['token'])}
    
    contacts = getRemoteData(url=contactsUri, headers=headers, payload=payload)
    reminders = getRemoteData(url=remindersUri, headers=headers, payload=payload)

    for contact in contacts: 
        if 'stay_in_touch_trigger_date' in contact:

            if contact['stay_in_touch_trigger_date']:
                targetDate = datetime.strptime(contact['stay_in_touch_trigger_date'], '%Y-%m-%dT%H:%M:%SZ')
                days = targetDate.date() - cDatetime.date()
                if days <= timedelta(days=envDict['contactDays']) and days > timedelta(days=0):
                    # followups.append(contact)
                    followups.append({'date':contact['stay_in_touch_trigger_date'].split('T')[0], 'event':"contact", 'firstname':contact["first_name"], 'lastname':contact["last_name"], 'days':days.days})
                    logging.info("{} {} - Next Contact: {}".format(contact["first_name"],contact["last_name"],contact['stay_in_touch_trigger_date'].split('T')[0]))

    # logging.info(followups)
    # for item in followups:
        # logging.info("{} {} - Next Contact: {}".format(item["first_name"],item["last_name"],item['stay_in_touch_trigger_date'].split('T')[0]))
    for item in reminders:
        initial_date = datetime.strptime(item['initial_date'], '%Y-%m-%dT%H:%M:%SZ').replace(year=cDatetime.year)
        # logging.info("{}".format(initial_date.date() - cDatetime.date()))
        days = initial_date.date() - cDatetime.date()
        if days <= timedelta(days=envDict['reminderDays']) and days > timedelta(days=0):
            # logging.info("{}".format(days.days))
            if re.search(r'birthday', item['title'], re.I):
                event = "birthday"
            else:
                event = item['title']
            followups.append({'date':initial_date.strftime('%Y-%m-%d'), 'event': event, 'firstname':item['contact']["first_name"], 'lastname':item['contact']["last_name"], 'days':days.days})
            # logging.info("{} {} - {}: {} days on {}-{}".format(item['contact']["first_name"],item['contact']["last_name"],item['title'],days.days,initial_date.month,initial_date.day))
        # else:
            # logging.info("{} {} - {}: {} days on {}-{}".format(item['contact']["first_name"],item['contact']["last_name"],item['title'],days.days,initial_date.month,initial_date.day))

    
    df = pd.DataFrame(followups, columns=['date', 'event', 'firstname', 'lastname', 'days'])
    print(df.head())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,handlers=[logging.StreamHandler()], format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",)
    main()