from __future__ import annotations

import csv
import io
from app.parsers.base import DocumentBlock


class CSVParser:
    async def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str | None = None,
        storage_path: str | None = None,
    ) -> list[DocumentBlock]:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="ignore")

        f = io.StringIO(text.strip())
        reader = csv.reader(f)

        try:
            rows = list(reader)
        except Exception:
            return []

        if not rows:
            return []

        # Extract headers and clean them
        headers = [str(cell).strip() for cell in rows[0]]
        if not headers or all(h == "" for h in headers):
            return []

        data_rows = rows[1:]
        if not data_rows:
            # Just the headers, return a single block
            markdown_table = f"| {' | '.join(headers)} |\n| {' | '.join(['---'] * len(headers))} |"
            return [
                DocumentBlock(
                    type="table",
                    content=markdown_table,
                    page_number=1,
                    media_path=storage_path,
                )
            ]

        blocks = []
        chunk_size = 10

        for idx in range(0, len(data_rows), chunk_size):
            chunk_data = data_rows[idx : idx + chunk_size]

            # Construct markdown table structure for this row group
            lines = []
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for r in chunk_data:
                padded_row = [str(cell).strip() for cell in r]
                if len(padded_row) < len(headers):
                    padded_row += [""] * (len(headers) - len(padded_row))
                elif len(padded_row) > len(headers):
                    padded_row = padded_row[: len(headers)]
                lines.append("| " + " | ".join(padded_row) + " |")

            markdown_table = "\n".join(lines)
            blocks.append(
                DocumentBlock(
                    type="table",
                    content=markdown_table,
                    page_number=1,
                    media_path=storage_path,
                )
            )

        return blocks
