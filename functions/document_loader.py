"""Load and extract text from supported document files."""

from __future__ import annotations

from pathlib import Path

import openpyxl
from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls"}


def load_document_file(filepath: str | Path) -> list[dict]:
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix == ".docx":
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        if not text.strip():
            return []
        return [{"filename": path.name, "text": f"Document filename: {path.name}\n\n{text}", "type": "docx"}]

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
        text = "\n".join(pages)
        if not text.strip():
            return []
        return [{"filename": path.name, "text": f"Document filename: {path.name}\n\n{text}", "type": "pdf"}]

    if suffix in {".xlsx", ".xls"}:
        wb = openpyxl.load_workbook(path, data_only=True)
        docs = []
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                continue

            headers = [str(cell) if cell is not None else "" for cell in rows[0]]
            text_parts = [f"Sheet: {sheet_name}"]
            for row in rows[1:]:
                row_parts = [f"{header}: {cell}" for header, cell in zip(headers, row) if cell is not None]
                if row_parts:
                    text_parts.append(" | ".join(row_parts))

            sheet_text = "\n".join(text_parts)
            if sheet_text.strip():
                docs.append({
                    "filename": f"{path.name}-{sheet_name}",
                    "text": f"Document filename: {path.name}\nSheet: {sheet_name}\n\n{sheet_text}",
                    "type": "xlsx",
                })
        return docs

    raise ValueError(f"Unsupported file type: {suffix}")


def load_documents(documents_dir: str | Path) -> tuple[list[dict], list[str]]:
    docs = []
    warnings = []
    directory = Path(documents_dir)

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            warnings.append(f"Skipped unsupported file: {path.name}")
            continue
        try:
            docs.extend(load_document_file(path))
        except Exception as exc:
            warnings.append(f"Could not load {path.name}: {exc}")

    return docs, warnings
