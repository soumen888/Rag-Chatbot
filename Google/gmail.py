import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build

class GmailClient:
    def __init__(self, credentials):
        self.service = build('gmail', 'v1', credentials=credentials)

    def list_emails(self, max_results=10, query="", include_spam_trash=True):
        """Lists Gmail messages matching a query, including Spam and Trash by default."""
        results = self.service.users().messages().list(
            userId='me', maxResults=max_results, q=query, includeSpamTrash=include_spam_trash
        ).execute()
        return results.get('messages', [])

    def get_email(self, message_id):
        """Retrieves details of a specific message by ID."""
        return self.service.users().messages().get(
            userId='me', id=message_id, format='full'
        ).execute()

    def send_email(self, to, subject, body_text):
        """Sends a plain text email."""
        message = MIMEText(body_text)
        message['to'] = to
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return self.service.users().messages().send(
            userId='me', body={'raw': raw_message}
        ).execute()

    def update_email_labels(self, message_id, add_labels=None, remove_labels=None):
        """Adds or removes labels from an email (e.g. marking as read/unread or starring)."""
        body = {}
        if add_labels:
            body['addLabelIds'] = add_labels
        if remove_labels:
            body['removeLabelIds'] = remove_labels
        return self.service.users().messages().modify(
            userId='me', id=message_id, body=body
        ).execute()

    def delete_email(self, message_id):
        """Moves a message to trash."""
        return self.service.users().messages().trash(
            userId='me', id=message_id
        ).execute()
