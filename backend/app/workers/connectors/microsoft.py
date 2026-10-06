"""Microsoft (OneDrive/SharePoint) Connector Handler."""

import httpx

class MicrosoftHandler:
    @staticmethod
    async def sync(connector, pipeline, existing_source_map, processed_source_ids, dependencies):
        """Sync files from OneDrive or SharePoint."""
        config = connector.get("config", {})
        oauth_tokens = config.get("oauth_tokens")
        if not oauth_tokens:
            raise ValueError("No OAuth tokens found for Microsoft connector")
            
        access_token = oauth_tokens.get("access_token")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        c_type = connector.get("type")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if c_type == "onedrive":
                url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            else:
                site_id = config.get("site_id")
                if not site_id:
                    raise ValueError("SharePoint connector requires a site_id configuration")
                url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/children"
                
            # For this iteration we will just fetch the root contents without recursion for simplicity
            
            while url:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    break
                    
                data = resp.json()
                items = data.get("value", [])
                
                for item in items:
                    if "folder" in item:
                        continue # Skip folders for MVP
                        
                    item_id = item["id"]
                    source_id = f"{c_type}://{item_id}"
                    processed_source_ids.add(source_id)
                    
                    if source_id in existing_source_map:
                        continue
                        
                    download_url = item.get("@microsoft.graph.downloadUrl")
                    if not download_url:
                        continue
                        
                    dl_resp = await client.get(download_url)
                    content = dl_resp.content
                    filename = item.get("name", "untitled")
                    
                    mime_type = item.get("file", {}).get("mimeType", "application/octet-stream")
                    
                    await dependencies["ingest_file"](
                        content=content,
                        filename=filename,
                        mime_type=mime_type,
                        source_id=source_id
                    )
                    
                url = data.get("@odata.nextLink")
