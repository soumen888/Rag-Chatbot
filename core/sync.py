import os
import time
import email
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from services.google.client import GoogleClient
from services.google.auth import GoogleAuthManager
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

    def sync_gmail(self, profile_name, limit=50, sync_all=False):
        """Fetches recent emails, filters duplicates using SQLite, and saves them. If sync_all=True, paginates all emails."""
        print(f"[*] Starting Gmail sync for profile: '{profile_name}' (Sync All: {sync_all})...")
        try:
            creds = self.auth_manager.get_credentials(profile_name)
            client = GoogleClient(creds)
        except Exception as e:
            print(f"[!] Authentication error for profile '{profile_name}': {e}")
            return 0

        # Construct query based on last sync timestamp (only if not syncing everything)
        query = ""
        if not sync_all:
            last_sync = self.local_db.get_last_sync(profile_name, 'gmail')
            if last_sync:
                query = f"after:{last_sync}"
        
        messages_list = []
        page_token = None
        
        try:
            while True:
                # Fetch N messages at a time (larger page size if syncing all to reduce API hits)
                fetch_size = 100 if sync_all else limit
                msgs, next_token = client.gmail.list_emails(max_results=fetch_size, query=query, page_token=page_token)
                messages_list.extend(msgs)
                
                # If we aren't performing a full history sync or there's no more pages, break
                if not sync_all or not next_token:
                    break
                page_token = next_token
                
                # Cap the safety limit on full syncs to 1000 messages to prevent infinite loops
                if len(messages_list) >= 1000:
                    print("[*] Reached full sync safety cap (1000 emails). Wrapping up...")
                    break
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


class MicrosoftSyncEngine:
    def __init__(self, db_path=None):
        from services.microsoft.auth import MicrosoftAuthManager
        self.auth_manager = MicrosoftAuthManager()
        self.local_db = LocalDB(db_path)

    def parse_outlook_email(self, msg_detail):
        """Parses Microsoft Graph message details into a database-compatible dictionary."""
        sender_obj = msg_detail.get('from', {}).get('emailAddress', {})
        sender_email = sender_obj.get('address', '')
        sender_name = sender_obj.get('name', '')

        # Extract primary recipient
        recipients_list = msg_detail.get('toRecipients', [])
        recipient = ""
        if recipients_list:
            recipient = recipients_list[0].get('emailAddress', {}).get('address', '')

        subject = msg_detail.get('subject', '(No Subject)')
        date_str = msg_detail.get('receivedDateTime', '')
        
        # Parse ISO date and epoch timestamp
        timestamp = int(time.time())
        iso_date = datetime.now(timezone.utc).isoformat()
        if date_str:
            try:
                # Graph datetime looks like '2026-08-11T17:42:13Z'
                # Remove Z and parse
                clean_date = date_str.replace('Z', '+00:00')
                dt = datetime.fromisoformat(clean_date)
                timestamp = int(dt.timestamp())
                iso_date = dt.isoformat()
            except Exception:
                pass

        snippet = msg_detail.get('inferenceClassification', '') or msg_detail.get('bodyPreview', '')
        body = msg_detail.get('body', {}).get('content', '')
        # Simple HTML tag stripper if body content is HTML
        if msg_detail.get('body', {}).get('contentType') == 'html':
            import re
            # Basic text-conversion of HTML to plain text
            body = re.sub('<[^<]+?>', '', body)
            
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
            'snippet': snippet[:200] if snippet else "",
            'body': body
        }

    def sync_outlook(self, profile_name, limit=50, sync_all=False):
        """Fetches recent emails from Outlook via Microsoft Graph and saves them. If sync_all=True, paginates all emails."""
        print(f"[*] Starting Outlook sync for profile: '{profile_name}' (Sync All: {sync_all})...")
        from services.microsoft.client import MicrosoftClient
        try:
            token = self.auth_manager.get_token(profile_name)
            client = MicrosoftClient(token)
        except Exception as e:
            print(f"[!] Authentication error for profile '{profile_name}': {e}")
            return 0

        messages_list = []
        next_link = None
        
        # Sync from Outlook
        try:
            while True:
                fetch_size = 100 if sync_all else limit
                msgs, next_token = client.outlook.list_emails(max_results=fetch_size, next_link=next_link)
                messages_list.extend(msgs)
                
                # Stop if not syncing all or no more pages
                if not sync_all or not next_token:
                    break
                next_link = next_token
                
                # Cap the safety limit on full syncs to 1000 messages to prevent infinite loops
                if len(messages_list) >= 1000:
                    print("[*] Reached full sync safety cap (1000 emails). Wrapping up...")
                    break
        except Exception as e:
            print(f"[!] Failed to list messages from Outlook: {e}")
            return 0

        if not messages_list:
            print(f"[+] Outlook for profile '{profile_name}' is already up-to-date.")
            self.local_db.update_last_sync(profile_name, 'outlook', int(time.time()))
            return 0

        parsed_emails = []
        synced_count = 0
        for msg_detail in messages_list:
            try:
                email_data = self.parse_outlook_email(msg_detail)
                email_data['profile_name'] = profile_name
                parsed_emails.append(email_data)
                synced_count += 1
            except Exception as e:
                print(f"[!] Failed to parse Outlook email: {e}")

        if parsed_emails:
            self.local_db.save_microsoft_emails(parsed_emails)
            
        self.local_db.update_last_sync(profile_name, 'outlook', int(time.time()))
        print(f"[+] Successfully synced {synced_count} Outlook emails for profile '{profile_name}'.")
        return synced_count
