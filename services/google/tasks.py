from googleapiclient.discovery import build

class TasksClient:
    def __init__(self, credentials):
        self.service = build('tasks', 'v1', credentials=credentials)

    def list_tasks(self, max_results=20):
        """Lists tasks from the default tasklist."""
        results = self.service.tasks().list(
            tasklist='@default', maxResults=max_results
        ).execute()
        return results.get('items', [])

    def create_task(self, title, notes=""):
        """Creates a new task in the default tasklist."""
        task = {'title': title, 'notes': notes}
        return self.service.tasks().insert(
            tasklist='@default', body=task
        ).execute()

    def update_task(self, task_id, title=None, notes=None, status=None):
        """Edits a task (e.g. updating details or marking as 'completed' / 'needsAction')."""
        task = {}
        if title is not None:
            task['title'] = title
        if notes is not None:
            task['notes'] = notes
        if status is not None:
            task['status'] = status
            
        return self.service.tasks().patch(
            tasklist='@default', task=task_id, body=task
        ).execute()

    def delete_task(self, task_id):
        """Deletes a task by ID."""
        return self.service.tasks().delete(
            tasklist='@default', task=task_id
        ).execute()
