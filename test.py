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
    return events_arr

def prio_order(events_arr):
    print(events_arr)
    work = []
    other = []
    new_events_arr = []
    for i in events_arr:
        if i[2] == ' work' and i[3] == ' y':
            work += [i]
        else: 
            other += [i]
    print(work)
    print(other)
    if len(work) >= len(other):
        diff = len(work)-len(other)
        new_events_arr = [work[0:diff]]
        for j in range(diff,len(work)):
            new_events_arr += [work[j]] + [other[j]]
    else: 
        diff = len(other)-len(work)
        for j in range(0,len(work)):
            new_events_arr += [work[j]] + [other[j]]
        new_events_arr += other[len(work):]
    print(new_events_arr)
    print(len(new_events_arr))
    for i in new_events_arr:
        print(i)
    return new_events_arr

def schedule_events(events_array, service, todays_events):
    next_day = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    start_time = next_day + datetime.timedelta(hours=config['starttime'])
    event_cnt = 0
    today_cnt = 0
    while event_cnt != len(events_array):
        if todays_events == [] or today_cnt == len(todays_events):
            schedule_helper(event_cnt, events_array, start_time, service)
            start_time = start_time + datetime.timedelta(hours=events_array[event_cnt][1])
            event_cnt += 1
        elif (start_time + datetime.timedelta(hours=events_array[event_cnt][1])).time() <= todays_events[today_cnt][0]:
            schedule_helper(event_cnt, events_array, start_time, service)
            start_time = start_time + datetime.timedelta(hours=events_array[event_cnt][1])
            event_cnt += 1
        else: 
            start_time = start_time.replace(hour=todays_events[today_cnt][1].hour, minute=todays_events[today_cnt][1].minute)
            today_cnt += 1

def schedule_helper(event_cnt, events_array, start_time, service):
    new_event = event_temp
    new_event['summary'] = events_array[event_cnt][0]
    new_event['start']['dateTime'] = str(start_time.isoformat())
    new_event['end']['dateTime'] = str((start_time + datetime.timedelta(hours=events_array[event_cnt][1])).isoformat())
    new_event['description'] = '@scheduler'
    event = service.events().insert(calendarId='primary', body=new_event).execute()
    service.events().update(calendarId='primary', eventId=event['id'], body={'description': '@scheduler'})
    print('Event created: %s' % (event.get('htmlLink')))

def clear_scheduler(to_del, service):
    for i in to_del:
        service.events().delete(calendarId='primary', eventId=i[0]).execute()

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
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
        now = (datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0) + datetime.timedelta(days=1)).isoformat() + 'Z'
        eod = (datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0) + datetime.timedelta(days=2)).isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,timeMax=eod,
                                              singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        #read from csv
        
        if not events:
            print('No upcoming events found.')
            return

        # record all preexisting events in the day
        todays_events = []
        #find all event ids and creator ids to clear out any preexisting scheduler created events
        to_del = []
        for event in events:
            start = datetime.datetime.fromisoformat(event['start']['dateTime'])
            end = datetime.datetime.fromisoformat(event['end']['dateTime'])
            if 'description' in event and config['delete']:
                to_del += [[event['id'], event['description']]]
            else:
                todays_events += [[start.time(), end.time()]]
        if config['delete']:
            clear_scheduler(to_del, service)
        needs_scheduling = process_csv()
        #function to preprocess events list to be scheduled
        processed_events = process_events(needs_scheduling)
        prio = prio_order(processed_events)
        #function to schedule all events
        #schedule_events(processed_events, service, todays_events)


    except HttpError as error:

        print('An error occurred: %s' % error)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-rb", "--rebalance", type=bool, default=False)
    parser.add_argument("-wt", "--work_type", default='balanced', const='balanced', nargs='?', choices=['balanced','grind','chill'])
    parser.add_argument("-s", "--starttime", type=int, default=9)
    parser.add_argument("-e", "--endtime", type=int, default=23)
    parser.add_argument("-d", "--delete", type=bool, default=False)
    args = parser.parse_args()
    config = vars(args)
    print(config)
    main()