import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class GoogleClient:
    def __init__(self, credentials):
        self.creds = credentials
        # Build standard Google API service instances
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.tasks_service = build('tasks', 'v1', credentials=self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    # ──────────────────────────────────────────────────────────────
    # Gmail APIs
    # ──────────────────────────────────────────────────────────────
    
    def list_emails(self, max_results=10, query=""):
        """Lists Gmail messages matching a query."""
        results = self.gmail_service.users().messages().list(
            userId='me', maxResults=max_results, q=query
        ).execute()
        return results.get('messages', [])

    def get_email(self, message_id):
        """Retrieves details of a specific message by ID."""
        return self.gmail_service.users().messages().get(
            userId='me', id=message_id, format='full'
        ).execute()

    def delete_email(self, message_id):
        """Moves a message to trash."""
        return self.gmail_service.users().messages().trash(
            userId='me', id=message_id
        ).execute()

    # ──────────────────────────────────────────────────────────────
    # Calendar APIs
    # ──────────────────────────────────────────────────────────────
    
    def list_calendar_events(self, max_results=10, time_min=None):
        """Lists calendar events."""
        results = self.calendar_service.events().list(
            calendarId='primary', maxResults=max_results, timeMin=time_min,
            singleEvents=True, orderBy='startTime'
        ).execute()
        return results.get('items', [])

    def create_calendar_event(self, summary, start_time, end_time, description=""):
        """Creates a calendar event (times in ISO 8601 string format)."""
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }
        return self.calendar_service.events().insert(
            calendarId='primary', body=event
        ).execute()

    # ──────────────────────────────────────────────────────────────
    # Tasks APIs
    # ──────────────────────────────────────────────────────────────
    
    def list_tasks(self, max_results=20):
        """Lists tasks from the default tasklist."""
        results = self.tasks_service.tasks().list(
            tasklist='@default', maxResults=max_results
        ).execute()
        return results.get('items', [])

    def create_task(self, title, notes=""):
        """Creates a new task in the default tasklist."""
        task = {'title': title, 'notes': notes}
        return self.tasks_service.tasks().insert(
            tasklist='@default', body=task
        ).execute()

    # ──────────────────────────────────────────────────────────────
    # Drive / Docs APIs
    # ──────────────────────────────────────────────────────────────
    
    def list_drive_files(self, max_results=20, query=None):
        """Lists files on Google Drive matching a query."""
        results = self.drive_service.files().list(
            maxResults=max_results, q=query,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        return results.get('files', [])

    def download_drive_file(self, file_id):
        """Downloads/exports a Google Drive file to memory bytes."""
        request = self.drive_service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_io.seek(0)
        return file_io.read()

    def delete_drive_file(self, file_id):
        """Deletes/trashes a file by ID."""
        return self.drive_service.files().delete(fileId=file_id).execute()
