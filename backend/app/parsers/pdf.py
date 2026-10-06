from __future__ import annotations

import io
from app.parsers.base import DocumentBlock


class PDFParser:
    async def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str | None = None,
        storage_path: str | None = None,
    ) -> list[DocumentBlock]:
        blocks = []
        
        # 1. Extract text page-by-page
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_idx, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    blocks.append(
                        DocumentBlock(type="text", content=text, page_number=page_idx + 1)
                    )
        except ImportError:
            # Fallback to pypdf
            import pypdf

            pdf_file = io.BytesIO(file_bytes)
            try:
                reader = pypdf.PdfReader(pdf_file, strict=False)
                for page_idx, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        blocks.append(
                            DocumentBlock(type="text", content=text, page_number=page_idx + 1)
                        )
            except Exception:
                try:
                    text = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    text = file_bytes.decode("latin-1", errors="ignore")
                if text.strip():
                    blocks.append(DocumentBlock(type="text", content=text, page_number=1))

        # 2. Extract tables page-by-page using pdfplumber
        try:
            import pdfplumber
            pdf_file = io.BytesIO(file_bytes)
            with pdfplumber.open(pdf_file) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    extracted_tables = page.extract_tables()
                    for table in extracted_tables:
                        clean_rows = []
                        for r in table:
                            if any(c is not None for c in r):
                                clean_rows.append([str(c).strip() if c is not None else "" for c in r])

                        if not clean_rows:
                            continue

                        headers = clean_rows[0]
                        if not headers or all(h == "" for h in headers):
                            continue

                        data_rows = clean_rows[1:]
                        if not data_rows:
                            markdown_table = f"| {' | '.join(headers)} |\n| {' | '.join(['---'] * len(headers))} |"
                            blocks.append(
                                DocumentBlock(
                                    type="table",
                                    content=markdown_table,
                                    page_number=page_idx + 1,
                                    media_path=storage_path,
                                )
                            )
                            continue

                        chunk_size = 10
                        for idx in range(0, len(data_rows), chunk_size):
                            chunk_data = data_rows[idx : idx + chunk_size]

                            lines = []
                            lines.append("| " + " | ".join(headers) + " |")
                            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                            for r in chunk_data:
                                padded_row = list(r)
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
                                    page_number=page_idx + 1,
                                    media_path=storage_path,
                                )
                            )
        except ImportError:
            pass
        except Exception:
            pass

        return blocks
