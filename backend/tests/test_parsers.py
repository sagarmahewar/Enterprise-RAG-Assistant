from __future__ import annotations

import io

import fitz
from docx import Document

from app.infrastructure.providers.parsers import (
    DocxDocumentParser,
    PdfDocumentParser,
    TextDocumentParser,
)


def test_text_parser_extracts_content() -> None:
    parser = TextDocumentParser()
    parsed = parser.parse("doc-1", "notes.txt", b"line one\nline two")
    assert parsed.document_id == "doc-1"
    assert parsed.document_name == "notes.txt"
    assert parsed.text == "line one\nline two"
    assert len(parsed.blocks) == 1


def test_docx_parser_extracts_paragraphs() -> None:
    doc = Document()
    doc.add_paragraph("First paragraph")
    doc.add_paragraph("Second paragraph")
    buffer = io.BytesIO()
    doc.save(buffer)

    parser = DocxDocumentParser()
    parsed = parser.parse("doc-2", "report.docx", buffer.getvalue())
    assert parsed.document_id == "doc-2"
    assert "First paragraph" in parsed.text
    assert "Second paragraph" in parsed.text
    assert len(parsed.blocks) == 2


def test_pdf_parser_extracts_page_text() -> None:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Policy retention is seven years.")
    content = pdf.tobytes()
    pdf.close()

    parser = PdfDocumentParser()
    parsed = parser.parse("doc-3", "policy.pdf", content)
    assert parsed.document_id == "doc-3"
    assert "Policy retention is seven years." in parsed.text
    assert parsed.blocks[0].page_ref == "1"
