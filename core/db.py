import os
import sqlite3
from datetime import datetime

class LocalDB:
    def __init__(self, db_path=None):
        if not db_path:
            config_dir = os.path.expanduser("~/.config/ragchat")
            os.makedirs(config_dir, exist_ok=True)
            self.db_path = os.path.join(config_dir, "ragchat_local.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # Table for storing raw emails
            conn.execute("""
                CREATE TABLE IF NOT EXISTS google_emails (
                    id TEXT PRIMARY KEY,
                    profile_name TEXT,
                    sender TEXT,
                    sender_name TEXT,
                    recipient TEXT,
                    subject TEXT,
                    date TEXT, -- ISO 8601 string
                    timestamp INTEGER, -- Epoch timestamp for fast sorting/filtering
                    snippet TEXT,
                    body TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_profile_time ON google_emails(profile_name, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_emails_sender ON google_emails(sender)")

            # Table for tracking last sync timestamp per profile/service
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_history (
                    profile_name TEXT,
                    service_type TEXT, -- 'gmail', 'drive', etc.
                    last_sync_timestamp INTEGER,
                    PRIMARY KEY (profile_name, service_type)
                )
            """)

            conn.commit()

    def save_emails(self, emails):
        """
        emails: list of dicts with keys matching google_emails table columns.
        """
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO google_emails 
                (id, profile_name, sender, sender_name, recipient, subject, date, timestamp, snippet, body)
                VALUES (:id, :profile_name, :sender, :sender_name, :recipient, :subject, :date, :timestamp, :snippet, :body)
            """, emails)
            conn.commit()

    def get_emails(self, profile_name, since_timestamp=None, limit=50):
        query = "SELECT * FROM google_emails WHERE profile_name = ?"
        params = [profile_name]
        
        if since_timestamp is not None:
            query += " AND timestamp >= ?"
            params.append(since_timestamp)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_last_sync(self, profile_name, service_type):
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT last_sync_timestamp FROM sync_history WHERE profile_name = ? AND service_type = ?",
                (profile_name, service_type)
            ).fetchone()
            return row['last_sync_timestamp'] if row else None

    def update_last_sync(self, profile_name, service_type, timestamp):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sync_history (profile_name, service_type, last_sync_timestamp)
                VALUES (?, ?, ?)
            """, (profile_name, service_type, timestamp))
            conn.commit()
