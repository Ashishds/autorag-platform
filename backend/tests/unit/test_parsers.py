from __future__ import annotations

import pytest
from app.parsers.registry import ParserRegistry
from app.parsers.pdf import PDFParser
from app.parsers.docx import DOCXParser
from app.parsers.image import ImageParser
from app.parsers.pptx import PPTXParser
from app.parsers.text import TextParser


def test_parser_registry_resolution():
    registry = ParserRegistry()

    # PDF resolution
    assert isinstance(registry.get_parser("test.pdf"), PDFParser)
    assert isinstance(registry.get_parser("test.pdf", "application/pdf"), PDFParser)

    # DOCX resolution
    assert isinstance(registry.get_parser("doc.docx"), DOCXParser)
    assert isinstance(registry.get_parser("doc.doc"), DOCXParser)
    assert isinstance(
        registry.get_parser(
            "doc.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        DOCXParser,
    )

    # Image resolution
    assert isinstance(registry.get_parser("image.png"), ImageParser)
    assert isinstance(registry.get_parser("photo.jpeg"), ImageParser)
    assert isinstance(registry.get_parser("screenshot.jpg"), ImageParser)
    assert isinstance(registry.get_parser("img.png", "image/png"), ImageParser)

    # PPTX resolution
    assert isinstance(registry.get_parser("deck.pptx"), PPTXParser)
    assert isinstance(
        registry.get_parser(
            "deck.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
        PPTXParser,
    )

    # HTML resolution
    from app.parsers.html import HTMLParser
    assert isinstance(registry.get_parser("page.html"), HTMLParser)
    assert isinstance(registry.get_parser("page.htm"), HTMLParser)
    assert isinstance(registry.get_parser("page.html", "text/html"), HTMLParser)

    # Fallback to TextParser
    assert isinstance(registry.get_parser("readme.txt"), TextParser)
    assert isinstance(registry.get_parser("code.py"), TextParser)
    assert isinstance(registry.get_parser("unrecognized_ext.xyz"), TextParser)


@pytest.mark.asyncio
async def test_text_parser():
    parser = TextParser()
    content = "Hello, world! AutoRAG is awesome."
    blocks = await parser.parse(content.encode("utf-8"), "test.txt")

    assert len(blocks) == 1
    assert blocks[0].type == "text"
    assert blocks[0].content == content
    assert blocks[0].page_number == 1
    assert blocks[0].media_path is None


@pytest.mark.asyncio
async def test_html_parser():
    from app.parsers.html import HTMLParser
    parser = HTMLParser()
    content = (
        "<html><body>"
        "<h1>Main Title</h1>"
        "<p>This is a paragraph.</p>"
        "<table>"
        "<tr><th>Header 1</th><th>Header 2</th></tr>"
        "<tr><td>Row 1 Col 1</td><td>Row 1 Col 2</td></tr>"
        "</table>"
        "</body></html>"
    )
    blocks = await parser.parse(content.encode("utf-8"), "test.html")
    assert len(blocks) == 3
    assert blocks[0].type == "text"
    assert blocks[0].content == "Main Title"
    assert blocks[1].type == "text"
    assert blocks[1].content == "This is a paragraph."
    assert blocks[2].type == "table"
    assert "Row 1 Col 1" in blocks[2].content
    assert "|" in blocks[2].content
