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

    def add_sheet(self, spreadsheet_id, title):
        """Adds a new tab (sheet) with the given title to an existing spreadsheet."""
        body = {
            'requests': [
                {
                    'addSheet': {
                        'properties': {
                            'title': title
                        }
                    }
                }
            ]
        }
        return self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()

    def get_sheet_names(self, spreadsheet_id):
        """Gets a list of all sheet tab names in a spreadsheet."""
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=spreadsheet_id, fields='sheets(properties/title)'
        ).execute()
        return [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]

    def delete_sheet(self, spreadsheet_id, title):
        """Deletes a sheet tab by its title string."""
        # 1. Fetch metadata to find matching sheetId for title
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=spreadsheet_id, fields='sheets(properties/title,properties/sheetId)'
        ).execute()
        
        sheet_id = None
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == title:
                sheet_id = sheet['properties']['sheetId']
                break
                
        if sheet_id is None:
            raise ValueError(f"No sheet tab named '{title}' found in spreadsheet.")
            
        # 2. Execute deletion request
        body = {
            'requests': [
                {
                    'deleteSheet': {
                        'sheetId': sheet_id
                    }
                }
            ]
        }
        return self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()
