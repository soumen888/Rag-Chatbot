from googleapiclient.discovery import build

class SheetsClient:
    def __init__(self, credentials):
        self.service = build('sheets', 'v4', credentials=credentials)

    def create_spreadsheet(self, title):
        """Creates a new spreadsheet with the given title."""
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        return self.service.spreadsheets().create(
            body=spreadsheet, fields='spreadsheetId,properties/title'
        ).execute()

    def get_spreadsheet_values(self, spreadsheet_id, range_name):
        """Gets cell values from a specific sheet range."""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        return result.get('values', [])

    def update_spreadsheet_values(self, spreadsheet_id, range_name, values, input_option="USER_ENTERED"):
        """Writes or updates cell values in a sheet range."""
        body = {
            'values': values
        }
        return self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=input_option, body=body
        ).execute()

    def append_spreadsheet_values(self, spreadsheet_id, range_name, values, input_option="USER_ENTERED"):
        """Appends rows of values to an existing table in a sheet range."""
        body = {
            'values': values
        }
        return self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=input_option, body=body
        ).execute()
