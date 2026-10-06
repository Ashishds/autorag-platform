from __future__ import annotations

from bs4 import BeautifulSoup
from app.parsers.base import DocumentBlock


class HTMLParser:
    async def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str | None = None,
        storage_path: str | None = None,
    ) -> list[DocumentBlock]:
        try:
            html_content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            html_content = file_bytes.decode("latin-1", errors="ignore")

        soup = BeautifulSoup(html_content, "html.parser")

        # Clean script, style, nav, footer, header, form elements
        for element in soup(["script", "style", "nav", "footer", "header", "form"]):
            element.decompose()

        blocks: list[DocumentBlock] = []
        body = soup.body or soup

        # Traverse and extract paragraphs, headings, tables, and lists in appearance order
        for element in body.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol"]):
            # Prevent processing elements that are descendants of nested lists/tables that we already handle
            # check if inside a table that is not the element itself
            if any(p.name == "table" for p in element.parents):
                continue
            # check if inside a ul/ol list that is not the element itself
            if any(p.name in ["ul", "ol"] for p in element.parents):
                continue

            if element.name == "table":
                # Convert HTML table to Markdown table
                rows = []
                for tr in element.find_all("tr"):
                    cells = [td_or_th.get_text(strip=True) for td_or_th in tr.find_all(["td", "th"])]
                    if any(cells):
                        rows.append(cells)

                if not rows:
                    continue

                # Get maximum number of columns in rows
                max_cols = max(len(r) for r in rows)
                if max_cols == 0:
                    continue

                lines = []
                headers = rows[0]
                if len(headers) < max_cols:
                    headers += [""] * (max_cols - len(headers))

                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

                for r in rows[1:]:
                    if len(r) < max_cols:
                        r += [""] * (max_cols - len(r))
                    lines.append("| " + " | ".join(r) + " |")

                markdown_table = "\n".join(lines)
                blocks.append(
                    DocumentBlock(
                        type="table",
                        content=markdown_table,
                        page_number=1,
                        media_path=storage_path,
                    )
                )

            elif element.name in ["ul", "ol"]:
                # Convert list items to markdown-like bullet points
                items = []
                for li in element.find_all("li"):
                    text = li.get_text(strip=True)
                    if text:
                        items.append(f"- {text}")

                list_content = "\n".join(items)
                if list_content.strip():
                    blocks.append(
                        DocumentBlock(
                            type="text",
                            content=list_content,
                            page_number=1,
                            media_path=storage_path,
                        )
                    )

            else:
                # Text element like p, h1-h6
                text_content = element.get_text(strip=True)
                if text_content:
                    blocks.append(
                        DocumentBlock(
                            type="text",
                            content=text_content,
                            page_number=1,
                            media_path=storage_path,
                        )
                    )

        # Fallback to plain text if no structured blocks could be extracted
        if not blocks:
            text = soup.get_text(separator="\n\n")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            cleaned_text = "\n\n".join(lines)
            if cleaned_text.strip():
                blocks.append(
                    DocumentBlock(
                        type="text",
                        content=cleaned_text,
                        page_number=1,
                        media_path=storage_path,
                    )
                )

        return blocks
