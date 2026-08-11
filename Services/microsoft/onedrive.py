import requests

class OneDriveClient:
    def __init__(self, access_token):
        self.token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

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

    def upload_onedrive_file(self, filename, content, parent_id=None):
        """Uploads or replaces a file in OneDrive."""
        if parent_id:
            url = f"{self.base_url}/me/drive/items/{parent_id}:/{filename}:/content"
        else:
            url = f"{self.base_url}/me/drive/root:/{filename}:/content"
            
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        # Graph API requires PUT for file uploads under 4MB
        response = requests.put(url, headers=self.headers, data=content)
        response.raise_for_status()
        return response.json()

    def delete_onedrive_file(self, item_id):
        """Deletes a file or folder in OneDrive."""
        url = f"{self.base_url}/me/drive/items/{item_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204
