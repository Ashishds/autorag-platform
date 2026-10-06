"""Dropbox Connector Handler."""

import dropbox

class DropboxHandler:
    @staticmethod
    async def sync(connector, pipeline, existing_source_map, processed_source_ids, dependencies):
        """Sync files from Dropbox."""
        config = connector.get("config", {})
        oauth_tokens = config.get("oauth_tokens")
        if not oauth_tokens:
            raise ValueError("No OAuth tokens found for Dropbox connector")
            
        access_token = oauth_tokens.get("access_token")
        
        dbx = dropbox.Dropbox(access_token)
        
        # We can configure a folder path, defaulting to root ""
        folder_path = config.get("folder_path", "")
        
        has_more = True
        cursor = None
        
        while has_more:
            if cursor:
                result = dbx.files_list_folder_continue(cursor)
            else:
                result = dbx.files_list_folder(folder_path, recursive=True)
                
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    source_id = f"dropbox://{entry.id}"
                    processed_source_ids.add(source_id)
                    
                    if source_id in existing_source_map:
                        continue
                        
                    # Download file
                    md, res = dbx.files_download(entry.path_display)
                    content = res.content
                    
                    filename = entry.name
                    mime_type = "application/octet-stream"
                    if filename.endswith(".pdf"): mime_type = "application/pdf"
                    elif filename.endswith(".txt"): mime_type = "text/plain"
                    elif filename.endswith(".csv"): mime_type = "text/csv"
                    elif filename.endswith(".docx"): mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    
                    await dependencies["ingest_file"](
                        content=content,
                        filename=filename,
                        mime_type=mime_type,
                        source_id=source_id
                    )
            
            cursor = result.cursor
            has_more = result.has_more
