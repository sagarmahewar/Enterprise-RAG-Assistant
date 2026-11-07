from __future__ import annotations

import io

import fitz
from docx import Document

from app.domain.models import ParsedDocument, ParsedTextBlock


class TextDocumentParser:
    provider_name = "local-text-parser"

    def supported_mime_types(self) -> set[str]:
        return {"text/plain"}

    def parse(self, document_id: str, document_name: str, content: bytes) -> ParsedDocument:
        text = content.decode("utf-8", errors="replace")
        block = ParsedTextBlock(
            text=text,
            page_ref=None,
            metadata={"source": "txt"},
        )
        return ParsedDocument(
            document_id=document_id,
            document_name=document_name,
            mime_type="text/plain",
            text=text,
            blocks=[block],
            metadata={"parser": self.provider_name},
        )


class DocxDocumentParser:
    provider_name = "local-docx-parser"

    def supported_mime_types(self) -> set[str]:
        return {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}

    def parse(self, document_id: str, document_name: str, content: bytes) -> ParsedDocument:
        document = Document(io.BytesIO(content))
        blocks: list[ParsedTextBlock] = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            blocks.append(
                ParsedTextBlock(
                    text=text,
                    page_ref=None,
                    metadata={"source": "docx"},
                )
            )

        full_text = "\n\n".join(block.text for block in blocks)
        return ParsedDocument(
            document_id=document_id,
            document_name=document_name,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            text=full_text,
            blocks=blocks,
            metadata={"parser": self.provider_name},
        )


class PdfDocumentParser:
    provider_name = "local-pdf-parser"

    def supported_mime_types(self) -> set[str]:
        return {"application/pdf"}

    def parse(self, document_id: str, document_name: str, content: bytes) -> ParsedDocument:
        blocks: list[ParsedTextBlock] = []

        with fitz.open(stream=content, filetype="pdf") as document:
            for page_index, page in enumerate(document):
                text = page.get_text("text").strip()
                if not text:
                    continue
                blocks.append(
                    ParsedTextBlock(
                        text=text,
                        page_ref=str(page_index + 1),
                        metadata={"source": "pdf"},
                    )
                )

        full_text = "\n\n".join(block.text for block in blocks)
        return ParsedDocument(
            document_id=document_id,
            document_name=document_name,
            mime_type="application/pdf",
            text=full_text,
            blocks=blocks,
            metadata={"parser": self.provider_name},
        )

