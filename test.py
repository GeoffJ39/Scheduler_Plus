from __future__ import print_function

import datetime
import os.path
import argparse
from event_temp import event_temp
import pandas as pd
import numpy as np
from math import isnan

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def process_csv():
    schedule = pd.read_csv('schedule.csv')
    schedule.fillna(0)
    print(schedule)
    return schedule

def process_events(schedule):
    events_arr = schedule.to_numpy()
    for i in events_arr:
        if isnan(i[-1]):
            continue
        else:
            for j in range(0, int(i[-1])-1):
                print(np.array([i]))
                events_arr = np.append(events_arr,np.array([i]), axis=0)
    events_arr = events_arr[:, :4]
    print(events_arr)
    return events_arr

def schedule_events(events_array):
    
    pass

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        print('here')
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        #print out all the calendarIDs
        # calendar_list=service.calendarList().list().execute()
        # for calendar in calendar_list['items']:
        #     print(f"calendar ID: {calendar['id']}")

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        eod = (datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0) + datetime.timedelta(days=1)).isoformat() + 'Z'
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,timeMax=eod,
                                              singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        #read from csv
        needs_scheduling = process_csv()
        #function to schedule all events in csv
        processed_events = process_events(needs_scheduling)
        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the events in the day
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

        new_event = event_temp
        new_event
        event = service.events().insert(calendarId='primary', body=new_event).execute()
        print('Event created: %s' % (event.get('htmlLink')))

    except HttpError as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-rb", "--rebalance", type=bool, default=False)
    parser.add_argument("-wt", "--work_type", default='balanced', const='balanced', nargs='?', choices=['balanced','grind','chill'])
    args = parser.parse_args()
    config = vars(args)
    print(config)
    main()