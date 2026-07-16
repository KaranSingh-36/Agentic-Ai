from __future__ import annotations

import html
import shutil
import uuid
from pathlib import Path
from typing import Any

from PIL import Image as PILImage
from pypdf import PdfReader
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
OUTPUT_DIR = BASE_DIR / "data" / "generated"
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log", ".html", ".htm"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS | PDF_EXTENSIONS


def _ensure_directories() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem.strip()

    if not stem:
        stem = "document"

    cleaned = []
    for char in stem:
        if char.isalnum() or char in {"-", "_"}:
            cleaned.append(char)
        else:
            cleaned.append("_")

    result = "".join(cleaned).strip("._")
    return result or "document"


def _safe_output_path(base_name: str, suffix: str) -> Path:
    _ensure_directories()
    safe_name = f"{_safe_stem(base_name)}_{uuid.uuid4().hex[:8]}{suffix}"
    return OUTPUT_DIR / safe_name


def _resolve_output_path(base_name: str, suffix: str, output_name: str | None) -> Path:
    if output_name:
        candidate = Path(output_name).name
        candidate_suffix = Path(candidate).suffix.lower() or suffix
        candidate_stem = _safe_stem(candidate)
        return OUTPUT_DIR / f"{candidate_stem}{candidate_suffix}"

    return _safe_output_path(base_name, suffix)


def _read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    return path.read_text(encoding="utf-8", errors="replace")


def save_uploaded_file(filename: str, file_bytes: bytes) -> str:
    _ensure_directories()

    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {suffix or 'unknown'}. Allowed types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError("File is too large. Maximum size is 10 MB.")

    safe_name = f"{uuid.uuid4().hex}_{_safe_stem(filename)}{suffix}"
    target_path = UPLOAD_DIR / safe_name
    target_path.write_bytes(file_bytes)
    return str(target_path)


def create_pdf_from_text(text: str, title: str = "Document", output_name: str | None = None) -> str:
    _ensure_directories()

    output_path = _resolve_output_path(title, ".pdf", output_name)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        alignment=TA_LEFT,
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        leading=14,
        spaceAfter=8,
    )

    story = [Paragraph(html.escape(title), title_style), Spacer(1, 0.2 * inch)]
    safe_text = html.escape(text or "").replace("\n", "<br/>")
    story.append(Paragraph(safe_text or "No content provided.", body_style))

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=48,
        bottomMargin=36,
    )
    document.build(story)
    return str(output_path)


def _convert_image_to_pdf(image_path: Path, output_name: str | None = None) -> str:
    output_path = _resolve_output_path(image_path.stem, ".pdf", output_name)

    page_width, page_height = A4
    margin = 36
    max_width = page_width - (2 * margin)
    max_height = page_height - (2 * margin)

    with PILImage.open(image_path) as source_image:
        image_width, image_height = source_image.size
        if image_width == 0 or image_height == 0:
            raise ValueError("The image file is empty or corrupted.")

        scale = min(max_width / image_width, max_height / image_height)
        draw_width = image_width * scale
        draw_height = image_height * scale

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=margin,
        leftMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )
    image_flowable = Image(str(image_path), width=draw_width, height=draw_height)
    image_flowable.hAlign = "CENTER"
    document.build([image_flowable])
    return str(output_path)


def convert_file_to_pdf(input_path: str, output_name: str | None = None) -> str:
    source_path = Path(input_path)

    if not source_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    suffix = source_path.suffix.lower()

    if suffix in TEXT_EXTENSIONS:
        content = _read_text_file(source_path)
        return create_pdf_from_text(content, title=source_path.stem, output_name=output_name)

    if suffix in IMAGE_EXTENSIONS:
        return _convert_image_to_pdf(source_path, output_name=output_name)

    if suffix in PDF_EXTENSIONS:
        output_path = _resolve_output_path(source_path.stem, ".pdf", output_name)
        shutil.copy2(source_path, output_path)
        return str(output_path)

    raise ValueError(
        f"Unsupported source file type: {suffix or 'unknown'}. Use a text, image, or PDF file."
    )


def extract_text_from_pdf(input_path: str, output_name: str | None = None) -> dict[str, Any]:
    source_path = Path(input_path)

    if not source_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    if source_path.suffix.lower() != ".pdf":
        raise ValueError("Text extraction is only available for PDF files.")

    reader = PdfReader(str(source_path))
    pages: list[str] = []

    for page_number, page in enumerate(reader.pages, start=1):
        extracted = page.extract_text() or ""
        pages.append(f"--- Page {page_number} ---\n{extracted.strip()}".strip())

    extracted_text = "\n\n".join(part for part in pages if part).strip()
    output_path = _resolve_output_path(source_path.stem, ".txt", output_name)

    output_path.write_text(extracted_text or "No text could be extracted from this PDF.", encoding="utf-8")

    return {
        "source_path": str(source_path),
        "output_path": str(output_path),
        "extracted_text": extracted_text,
    }


def execute(arguments: dict[str, Any]) -> dict[str, Any]:
    action = (arguments.get("action") or "convert_to_pdf").strip().lower()
    source_path = arguments.get("source_path") or arguments.get("file_path")
    text = arguments.get("text") or arguments.get("content") or ""
    title = arguments.get("title") or arguments.get("output_title") or "Document"
    output_name = arguments.get("output_name")

    if action == "create_pdf":
        if not text:
            raise ValueError("Missing text content for PDF creation.")

        output_path = create_pdf_from_text(text=text, title=title, output_name=output_name)
        return {
            "status": "success",
            "action": action,
            "source_path": None,
            "output_path": output_path,
            "download_name": Path(output_path).name,
        }

    if action == "convert_to_pdf":
        if not source_path:
            raise ValueError("Missing source_path for file conversion.")

        output_path = convert_file_to_pdf(str(source_path), output_name=output_name)
        return {
            "status": "success",
            "action": action,
            "source_path": str(source_path),
            "output_path": output_path,
            "download_name": Path(output_path).name,
        }

    if action == "extract_text":
        if not source_path:
            raise ValueError("Missing source_path for text extraction.")

        result = extract_text_from_pdf(str(source_path), output_name=output_name)
        result["status"] = "success"
        result["action"] = action
        result["download_name"] = Path(result["output_path"]).name
        return result

    raise ValueError(
        "Unsupported pdf tool action. Use create_pdf, convert_to_pdf, or extract_text."
    )


if __name__ == "__main__":
    sample_path = create_pdf_from_text("Hello PDF", title="Sample")
    print(sample_path)