"""Notion Connector Handler."""

from notion_client import AsyncClient

class NotionHandler:
    @staticmethod
    async def sync(connector, pipeline, existing_source_map, processed_source_ids, dependencies):
        """Sync files from Notion."""
        config = connector.get("config", {})
        oauth_tokens = config.get("oauth_tokens")
        if not oauth_tokens:
            raise ValueError("No OAuth tokens found for Notion connector")
            
        notion = AsyncClient(auth=oauth_tokens.get("access_token"))
        
        # Search for all pages the integration has access to
        results = await notion.search(
            filter={"property": "object", "value": "page"}
        )
        
        pages = results.get("results", [])
        
        for page in pages:
            page_id = page["id"]
            source_id = f"notion://{page_id}"
            processed_source_ids.add(source_id)
            
            if source_id in existing_source_map:
                continue
                
            # Get page title
            title = "Untitled Page"
            if "properties" in page:
                for prop_name, prop_data in page["properties"].items():
                    if prop_data["type"] == "title":
                        title_arr = prop_data.get("title", [])
                        if title_arr:
                            title = "".join([t.get("plain_text", "") for t in title_arr])
                        break
                        
            filename = f"{title}.md"
            
            # Fetch blocks
            blocks = await notion.blocks.children.list(block_id=page_id)
            
            content_lines = [f"# {title}\n"]
            for block in blocks.get("results", []):
                b_type = block.get("type")
                if b_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
                    rich_text = block[b_type].get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if b_type.startswith("heading_"):
                        level = int(b_type[-1]) + 1
                        content_lines.append(f"{'#' * level} {text}")
                    elif b_type in ["bulleted_list_item", "numbered_list_item"]:
                        content_lines.append(f"- {text}")
                    else:
                        content_lines.append(text)
                        
            content = "\n\n".join(content_lines).encode("utf-8")
            
            await dependencies["ingest_file"](
                content=content,
                filename=filename,
                mime_type="text/markdown",
                source_id=source_id
            )
