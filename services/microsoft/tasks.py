import requests

class MicrosoftTasksClient:
    def __init__(self, access_token):
        self.token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_default_todo_list_id(self):
        """Helper to retrieve the user's default To-Do tasks list ID."""
        url = f"{self.base_url}/me/todo/lists"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        lists = response.json().get("value", [])
        for lst in lists:
            if lst.get("wellKnownName") == "defaultList":
                return lst["id"]
        return lists[0]["id"] if lists else None

    def list_tasks(self, list_id=None, max_results=20):
        """Lists tasks in a Microsoft To-Do list."""
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
        """Creates a task in a Microsoft To-Do list."""
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

    def update_task(self, task_id, list_id=None, title=None, notes=None, status=None):
        """Updates details of an existing task (patch update). Status can be 'notStarted' or 'completed'."""
        if not list_id:
            list_id = self.get_default_todo_list_id()
        if not list_id:
            raise Exception("No task list found to update task.")
            
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        task_data = {}
        if title is not None:
            task_data["title"] = title
        if notes is not None:
            task_data["body"] = {"content": notes, "contentType": "text"}
        if status is not None:
            task_data["status"] = status
            
        response = requests.patch(url, headers=self.headers, json=task_data)
        response.raise_for_status()
        return response.json()

    def delete_task(self, task_id, list_id=None):
        """Deletes a task by ID."""
        if not list_id:
            list_id = self.get_default_todo_list_id()
        if not list_id:
            raise Exception("No task list found to delete task.")
            
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204
