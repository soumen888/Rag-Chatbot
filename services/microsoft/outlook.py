import requests

class OutlookMailClient:
    def __init__(self, access_token):
        self.token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def list_emails(self, max_results=10, search_query=None, next_link=None):
        """Lists Outlook messages, returning a tuple (messages, next_link_url)."""
        if next_link:
            url = next_link
            params = {}
        else:
            url = f"{self.base_url}/me/messages"
            params = {"$top": max_results}
            if search_query:
                params["$search"] = f'"{search_query}"'
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("value", []), data.get("@odata.nextLink")

    def get_email(self, message_id):
        """Gets a detailed message."""
        url = f"{self.base_url}/me/messages/{message_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def send_email(self, to, subject, body_content, content_type="Text"):
        """Sends an email as the authenticated user."""
        url = f"{self.base_url}/me/sendMail"
        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": content_type,
                    "content": body_content
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to
                        }
                    }
                ]
            }
        }
        response = requests.post(url, headers=self.headers, json=email_data)
        response.raise_for_status()
        return response.status_code == 202

    def delete_email(self, message_id):
        """Deletes a message."""
        url = f"{self.base_url}/me/messages/{message_id}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 204
