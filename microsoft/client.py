import requests

class MicrosoftClient:
    def __init__(self, access_token):
        self.token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    # ──────────────────────────────────────────────────────────────
    # Outlook Mail APIs
    # ──────────────────────────────────────────────────────────────
    
    def list_emails(self, max_results=10, search_query=None):
        """Lists Outlook messages."""
        url = f"{self.base_url}/me/messages"
        params = {"$top": max_results}
        if search_query:
            params["$search"] = f'"{search_query}"'
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("value", [])

    def get_email(self, message_id):
        """Gets a detailed message."""
        url = f"{self.base_url}/me/messages/{message_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def delete_email(self, message_id):
        """Deletes a message."""
        url = f"{self.base_url}/me/messages/{message_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204

    # ──────────────────────────────────────────────────────────────
    # Calendar APIs
    # ──────────────────────────────────────────────────────────────
    
    def list_calendar_events(self, max_results=10):
        """Lists calendar events."""
        url = f"{self.base_url}/me/calendar/events"
        params = {"$top": max_results, "$select": "subject,body,start,end,location"}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("value", [])

    def create_calendar_event(self, subject, start_time, end_time, body_content=""):
        """Creates a calendar event (times in ISO 8601 string, e.g., '2026-08-10T12:00:00')."""
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
        response = requests.post(url, headers=self.headers, json=event_data)
        response.raise_for_status()
        return response.json()

    # ──────────────────────────────────────────────────────────────
    # ToDo / Tasks APIs
    # ──────────────────────────────────────────────────────────────
    
    def get_default_todo_list_id(self):
        """Helper to retrieve the user's default tasks list ID."""
        url = f"{self.base_url}/me/todo/lists"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        lists = response.json().get("value", [])
        for lst in lists:
            if lst.get("wellKnownName") == "defaultList":
                return lst["id"]
        return lists[0]["id"] if lists else None

    def list_tasks(self, list_id=None, max_results=20):
        """Lists tasks in a To-Do list."""
        if not list_id:
            list_id = self.get_default_todo_list_id()
        if not list_id:
            return []
            
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks"
        params = {"$top": max_results}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("value", [])

    def create_task(self, title, list_id=None, notes=None):
        """Creates a task in a To-Do list."""
        if not list_id:
            list_id = self.get_default_todo_list_id()
        if not list_id:
            raise Exception("No task list found to create task.")
            
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks"
        task_data = {"title": title}
        if notes:
            task_data["body"] = {"content": notes, "contentType": "text"}
            
        response = requests.post(url, headers=self.headers, json=task_data)
        response.raise_for_status()
        return response.json()

    # ──────────────────────────────────────────────────────────────
    # OneDrive APIs
    # ──────────────────────────────────────────────────────────────
    
    def list_onedrive_files(self, folder_path=None, max_results=20):
        """Lists files in OneDrive root or a specific folder path."""
        if folder_path:
            url = f"{self.base_url}/me/drive/root:/{folder_path}:/children"
        else:
            url = f"{self.base_url}/me/drive/root/children"
            
        params = {"$top": max_results}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("value", [])

    def download_onedrive_file(self, item_id):
        """Downloads a OneDrive file content as bytes."""
        url = f"{self.base_url}/me/drive/items/{item_id}/content"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.content

    def delete_onedrive_file(self, item_id):
        """Deletes a file or folder in OneDrive."""
        url = f"{self.base_url}/me/drive/items/{item_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204
