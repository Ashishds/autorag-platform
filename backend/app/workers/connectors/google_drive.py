"""Google Drive Connector Handler."""

import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class GoogleDriveHandler:
    @staticmethod
    async def sync(connector, pipeline, existing_source_map, processed_source_ids, dependencies):
        """Sync files from Google Drive."""
        config = connector.get("config", {})
        oauth_tokens = config.get("oauth_tokens")
        if not oauth_tokens:
            raise ValueError("No OAuth tokens found for Google Drive connector")
            
        creds = Credentials(
            token=oauth_tokens.get("access_token"),
            refresh_token=oauth_tokens.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=dependencies["client_id"],
            client_secret=dependencies["client_secret"],
        )
        
        service = build('drive', 'v3', credentials=creds)
        
        # Get folder ID or use root
        folder_id = config.get("folder_id", "root")
        
        query = f"'{folder_id}' in parents and trashed = false"
        
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
        ).execute()
        
        items = results.get('files', [])
        
        for item in items:
            source_id = f"gdrive://{item['id']}"
            processed_source_ids.add(source_id)
            
            if source_id in existing_source_map:
                # Could check modifiedTime here to see if we need to re-sync
                continue
                
            mime_type = item['mimeType']
            file_id = item['id']
            filename = item['name']
            
            # Skip folders for now (or implement recursive later)
            if mime_type == 'application/vnd.google-apps.folder':
                continue
                
            request = service.files().get_media(fileId=file_id)
            
            # If it's a google doc, we need to export it instead
            if mime_type.startswith('application/vnd.google-apps.'):
                if mime_type == 'application/vnd.google-apps.document':
                    request = service.files().export_media(fileId=file_id, mimeType='text/plain')
                    mime_type = 'text/plain'
                    filename += '.txt'
                elif mime_type == 'application/vnd.google-apps.spreadsheet':
                    request = service.files().export_media(fileId=file_id, mimeType='text/csv')
                    mime_type = 'text/csv'
                    filename += '.csv'
                else:
                    continue # Unsupported google workspace type for now
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
            content = fh.getvalue()
            
            await dependencies["ingest_file"](
                content=content,
                filename=filename,
                mime_type=mime_type,
                source_id=source_id
            )
