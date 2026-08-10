from googleapiclient.discovery import build

class DocsClient:
    def __init__(self, credentials):
        self.service = build('docs', 'v1', credentials=credentials)

    def create_document(self, title):
        """Creates a blank document with the given title."""
        doc = {
            'title': title
        }
        return self.service.documents().create(body=doc).execute()

    def get_document_content(self, document_id):
        """Retrieves the full content structure of a Google Doc."""
        return self.service.documents().get(documentId=document_id).execute()

    def append_document_text(self, document_id, text):
        """Appends plain text to the end of a Google Doc."""
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': text
                }
            }
        ]
        try:
            doc = self.get_document_content(document_id)
            end_index = doc.get('body').get('content')[-1].get('endIndex') - 1
            requests[0]['insertText']['location']['index'] = end_index
        except Exception:
            requests[0]['insertText']['location']['index'] = 1

        return self.service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}
        ).execute()
