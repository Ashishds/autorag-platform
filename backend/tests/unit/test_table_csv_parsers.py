from __future__ import annotations

import io
import pytest
from app.parsers.csv import CSVParser
from app.parsers.excel import ExcelParser


@pytest.mark.asyncio
async def test_csv_parser_chunking():
    # Construct a CSV with 15 rows of data (+ 1 header row)
    csv_content = "Product,SKU,Price,Stock\n"
    for i in range(1, 16):
        csv_content += f"Item {i},SKU-{i:03d},{10.0 + i},{100 + i}\n"

    parser = CSVParser()
    blocks = await parser.parse(csv_content.encode("utf-8"), "inventory.csv")

    # Group size is 10, so 15 rows should yield 2 chunks
    assert len(blocks) == 2

    # Verify first chunk (contains 10 rows)
    block1 = blocks[0]
    assert block1.type == "table"
    assert "Product | SKU | Price | Stock" in block1.content
    assert "Item 1 |" in block1.content
    assert "Item 10 |" in block1.content
    assert "Item 11 |" not in block1.content

    # Verify second chunk (contains remaining 5 rows)
    block2 = blocks[1]
    assert block2.type == "table"
    assert "Product | SKU | Price | Stock" in block2.content  # Header preserved
    assert "Item 1 |" not in block2.content
    assert "Item 11 |" in block2.content
    assert "Item 15 |" in block2.content


@pytest.mark.asyncio
async def test_excel_parser_sheets():
    import openpyxl

    # Create an in-memory workbook with openpyxl
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Inventory"

    # Add header + 5 rows
    sheet.append(["Product", "SKU", "Price"])
    for i in range(1, 6):
        sheet.append([f"Laptop {i}", f"LP-{i}", 500 + i])

    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_bytes = excel_file.getvalue()
    wb.close()

    parser = ExcelParser()
    blocks = await parser.parse(excel_bytes, "test.xlsx")

    assert len(blocks) == 1
    block = blocks[0]
    assert block.type == "table"
    assert "Sheet: Inventory" in block.content
    assert "Product | SKU | Price" in block.content
    assert "Laptop 1" in block.content
    assert "Laptop 5" in block.content
