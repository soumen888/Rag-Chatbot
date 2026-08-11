import time
from googleapiclient.discovery import build

class CalendarClient:
    def __init__(self, credentials):
        self.service = build('calendar', 'v3', credentials=credentials)

    def list_calendar_events(self, max_results=10, time_min=None):
        """Lists calendar events."""
        results = self.service.events().list(
            calendarId='primary', maxResults=max_results, timeMin=time_min,
            singleEvents=True, orderBy='startTime'
        ).execute()
        return results.get('items', [])

    def create_calendar_event(self, summary, start_time, end_time, description="", add_meet_link=False):
        """Creates a calendar event (times in ISO 8601 string format) with an optional Google Meet link."""
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }
        
        params = {'calendarId': 'primary', 'body': event}
        
        if add_meet_link:
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': f"meet-{int(time.time())}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
            params['conferenceDataVersion'] = 1

        return self.service.events().insert(**params).execute()

    def update_calendar_event(self, event_id, summary=None, start_time=None, end_time=None, description=None):
        """Edits an existing calendar event (patch updates)."""
        event = {}
        if summary is not None:
            event['summary'] = summary
        if description is not None:
            event['description'] = description
        if start_time is not None:
            event['start'] = {'dateTime': start_time, 'timeZone': 'UTC'}
        if end_time is not None:
            event['end'] = {'dateTime': end_time, 'timeZone': 'UTC'}
            
        return self.service.events().patch(
            calendarId='primary', eventId=event_id, body=event
        ).execute()

    def delete_calendar_event(self, event_id):
        """Deletes a calendar event by ID."""
        return self.service.events().delete(
            calendarId='primary', eventId=event_id
        ).execute()
