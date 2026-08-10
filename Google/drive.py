import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

class DriveClient:
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def list_drive_files(self, max_results=20, query=None):
        """Lists files on Google Drive matching a query."""
        results = self.service.files().list(
            maxResults=max_results, q=query,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        return results.get('files', [])

    def create_drive_file(self, name, mime_type="text/plain", content=None, parent_id=None):
        """Creates a new file or folder on Google Drive."""
        file_metadata = {'name': name}
        if mime_type == 'application/vnd.google-apps.folder':
            file_metadata['mimeType'] = mime_type
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        if content is not None and mime_type != 'application/vnd.google-apps.folder':
            if isinstance(content, str):
                content = content.encode('utf-8')
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
            return self.service.files().create(
                body=file_metadata, media_body=media, fields='id, name, mimeType'
            ).execute()
        else:
            return self.service.files().create(
                body=file_metadata, fields='id, name, mimeType'
            ).execute()

    def download_drive_file(self, file_id):
        """Downloads/exports a Google Drive file to memory bytes."""
        request = self.service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_io.seek(0)
        return file_io.read()

    def update_drive_file(self, file_id, name=None, content=None, mime_type="text/plain"):
        """Updates file metadata (e.g. rename) and/or replaces content."""
        file_metadata = {}
        if name is not None:
            file_metadata['name'] = name
            
        if content is not None:
            if isinstance(content, str):
                content = content.encode('utf-8')
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
            return self.service.files().update(
                fileId=file_id, body=file_metadata, media_body=media, fields='id, name'
            ).execute()
        else:
            return self.service.files().update(
                fileId=file_id, body=file_metadata, fields='id, name'
            ).execute()

    def delete_drive_file(self, file_id):
        """Deletes/trashes a file by ID."""
        return self.service.files().delete(fileId=file_id).execute()
