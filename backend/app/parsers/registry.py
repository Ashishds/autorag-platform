from __future__ import annotations

from app.parsers.base import DocumentParser
from app.parsers.pdf import PDFParser
from app.parsers.docx import DOCXParser
from app.parsers.image import ImageParser
from app.parsers.text import TextParser
from app.parsers.csv import CSVParser
from app.parsers.excel import ExcelParser
from app.parsers.pptx import PPTXParser
from app.parsers.html import HTMLParser
from app.parsers.youtube import YouTubeParser


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, DocumentParser] = {}

        # PDF Parsers
        pdf_parser = PDFParser()
        self.register(".pdf", pdf_parser)
        self.register("application/pdf", pdf_parser)

        # Word Document Parsers
        docx_parser = DOCXParser()
        self.register(".docx", docx_parser)
        self.register(".doc", docx_parser)
        self.register(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            docx_parser,
        )
        self.register("application/msword", docx_parser)

        # Image Parsers (PNG / JPG only)
        image_parser = ImageParser()
        self.register(".png", image_parser)
        self.register(".jpg", image_parser)
        self.register(".jpeg", image_parser)
        self.register("image/png", image_parser)
        self.register("image/jpeg", image_parser)

        # PowerPoint
        pptx_parser = PPTXParser()
        self.register(".pptx", pptx_parser)
        self.register(
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            pptx_parser,
        )

        # Tabular Data Parsers
        csv_parser = CSVParser()
        self.register(".csv", csv_parser)
        self.register("text/csv", csv_parser)

        excel_parser = ExcelParser()
        self.register(".xlsx", excel_parser)
        self.register(".xls", excel_parser)
        self.register("application/vnd.ms-excel", excel_parser)
        self.register(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            excel_parser,
        )

        self._default_parser = TextParser()

        # HTML
        html_parser = HTMLParser()
        self.register(".html", html_parser)
        self.register(".htm", html_parser)
        self.register("text/html", html_parser)

        # YouTube Transcripts
        youtube_parser = YouTubeParser()
        self.register(".youtube", youtube_parser)
        self.register("application/x-youtube", youtube_parser)

    def register(self, ext_or_mime: str, parser: DocumentParser) -> None:
        self._parsers[ext_or_mime.lower()] = parser

    def get_parser(self, filename: str, mime_type: str | None = None) -> DocumentParser:
        if mime_type and mime_type.lower() in self._parsers:
            return self._parsers[mime_type.lower()]

        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if ext in self._parsers:
            return self._parsers[ext]

        return self._default_parser
