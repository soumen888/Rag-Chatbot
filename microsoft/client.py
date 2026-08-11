from .outlook import OutlookMailClient
from .calendar import OutlookCalendarClient
from .tasks import MicrosoftTasksClient
from .onedrive import OneDriveClient

class MicrosoftClient:
    def __init__(self, access_token):
        self.token = access_token
        self.outlook = OutlookMailClient(access_token)
        self.calendar = OutlookCalendarClient(access_token)
        self.tasks = MicrosoftTasksClient(access_token)
        self.onedrive = OneDriveClient(access_token)
