from .gmail import GmailClient
from .calendar import CalendarClient
from .tasks import TasksClient
from .drive import DriveClient
from .sheets import SheetsClient
from .docs import DocsClient

class GoogleClient:
    def __init__(self, credentials):
        self.creds = credentials
        self.gmail = GmailClient(credentials)
        self.calendar = CalendarClient(credentials)
        self.tasks = TasksClient(credentials)
        self.drive = DriveClient(credentials)
        self.sheets = SheetsClient(credentials)
        self.docs = DocsClient(credentials)
