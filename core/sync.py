import os
import time
import email
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from Google.client import GoogleClient
from Google.auth import GoogleAuthManager
from core.db import LocalDB

class GoogleSyncEngine:
    def __init__(self, db_path=None):
        self.auth_manager = GoogleAuthManager()
        self.local_db = LocalDB(db_path)

    def parse_email_headers(self, msg_detail):
        """Parses Gmail message headers into structured format."""
        headers = msg_detail.get('payload', {}).get('headers', [])
        header_dict = {h['name'].lower(): h['value'] for h in headers}
        
        sender_raw = header_dict.get('from', '')
        sender_name = ''
        sender_email = sender_raw
        if '<' in sender_raw and '>' in sender_raw:
            parts = sender_raw.split('<')
            sender_name = parts[0].strip().replace('"', '')
            sender_email = parts[1].replace('>', '').strip()

        recipient = header_dict.get('to', '')
        subject = header_dict.get('subject', '(No Subject)')
        date_str = header_dict.get('date', '')
        
        # Parse ISO date and epoch timestamp
        timestamp = int(time.time())
        iso_date = datetime.now(timezone.utc).isoformat()
        if date_str:
            try:
                dt = parsedate_to_datetime(date_str)
                # Ensure timezone aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                timestamp = int(dt.timestamp())
                iso_date = dt.isoformat()
            except Exception:
                pass

        # Extract body snippet or full text
        snippet = msg_detail.get('snippet', '')
        
        # Extract body text
        body = ""
        payload = msg_detail.get('payload', {})
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                    import base64
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break
        elif payload.get('body', {}).get('data'):
            import base64
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

        if not body:
            body = snippet

        return {
            'id': msg_detail['id'],
            'sender': sender_email,
            'sender_name': sender_name,
            'recipient': recipient,
            'subject': subject,
            'date': iso_date,
            'timestamp': timestamp,
            'snippet': snippet,
            'body': body
        }

    def sync_gmail(self, profile_name, limit=50):
        """Fetches recent emails, filters duplicates using SQLite, and saves them."""
        print(f"[*] Starting Gmail sync for profile: '{profile_name}'...")
        try:
            creds = self.auth_manager.get_credentials(profile_name)
            client = GoogleClient(creds)
        except Exception as e:
            print(f"[!] Authentication error for profile '{profile_name}': {e}")
            return 0

        # Construct query based on last sync timestamp
        last_sync = self.local_db.get_last_sync(profile_name, 'gmail')
        query = ""
        if last_sync:
            # Query Gmail for messages after the last sync timestamp
            query = f"after:{last_sync}"
        
        try:
            messages_list = client.gmail.list_emails(max_results=limit, query=query)
        except Exception as e:
            print(f"[!] Failed to list messages from Gmail: {e}")
            return 0

        if not messages_list:
            print(f"[+] Gmail for profile '{profile_name}' is already up-to-date.")
            self.local_db.update_last_sync(profile_name, 'gmail', int(time.time()))
            return 0

        parsed_emails = []
        synced_count = 0
        for msg_ref in messages_list:
            msg_id = msg_ref['id']
            try:
                msg_detail = client.gmail.get_email(msg_id)
                email_data = self.parse_email_headers(msg_detail)
                email_data['profile_name'] = profile_name
                parsed_emails.append(email_data)
                synced_count += 1
            except Exception as e:
                print(f"[!] Failed to download email {msg_id}: {e}")

        if parsed_emails:
            self.local_db.save_emails(parsed_emails)
            
        self.local_db.update_last_sync(profile_name, 'gmail', int(time.time()))
        print(f"[+] Successfully synced {synced_count} emails for profile '{profile_name}'.")
        return synced_count
