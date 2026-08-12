import requests

class OutlookCalendarClient:
    def __init__(self, access_token):
        self.token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def list_calendar_events(self, max_results=10):
        """Lists calendar events."""
        url = f"{self.base_url}/me/calendar/events"
        params = {"$top": max_results, "$select": "subject,body,start,end,location,onlineMeeting"}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("value", [])

    def create_calendar_event(self, subject, start_time, end_time, body_content="", add_teams_link=False):
        """Creates a calendar event (times in ISO 8601 UTC string format) with optional Microsoft Teams link."""
        url = f"{self.base_url}/me/calendar/events"
        event_data = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_content
            },
            "start": {
                "dateTime": start_time,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "UTC"
            }
        }
        
        if add_teams_link:
            event_data["isOnlineMeeting"] = True
            event_data["onlineMeetingProvider"] = "teamsForBusiness"
            
        response = requests.post(url, headers=self.headers, json=event_data)
        response.raise_for_status()
        return response.json()

    def update_calendar_event(self, event_id, subject=None, start_time=None, end_time=None, body_content=None):
        """Updates details of an existing calendar event (patch update)."""
        url = f"{self.base_url}/me/calendar/events/{event_id}"
        event_data = {}
        if subject is not None:
            event_data["subject"] = subject
        if body_content is not None:
            event_data["body"] = {"contentType": "HTML", "content": body_content}
        if start_time is not None:
            event_data["start"] = {"dateTime": start_time, "timeZone": "UTC"}
        if end_time is not None:
            event_data["end"] = {"dateTime": end_time, "timeZone": "UTC"}
            
        response = requests.patch(url, headers=self.headers, json=event_data)
        response.raise_for_status()
        return response.json()

    def delete_calendar_event(self, event_id):
        """Deletes a calendar event by ID."""
        url = f"{self.base_url}/me/calendar/events/{event_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204
