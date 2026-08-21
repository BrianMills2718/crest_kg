"""Bounded local text extraction for operator-supplied source documents."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .models import UploadExtractionMethod


TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".csv", ".tsv"}
IMAGE_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
)


class AcquisitionError(ValueError):
    """Base class for upload failures safe to show to an operator."""


class UnsupportedUpload(AcquisitionError):
    """The uploaded bytes are not one of the supported source formats."""


class ExtractionUnavailable(AcquisitionError):
    """A required local extraction dependency is unavailable."""


class ExtractedUpload(BaseModel):
    """Strict portable result produced before persistence or catalog adoption."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    filename: str
    title: str
    media_type: str
    body_text: str = Field(min_length=1)
    extraction_method: UploadExtractionMethod
    page_count: int = Field(ge=1)


def safe_filename(filename: str | None) -> str:
    name = Path(filename or "upload").name.strip()
    if not name or name in {".", ".."}:
        return "upload"
    return name[:240]


def _normalized_text(value: str) -> str:
    lines = [line.rstrip() for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    normalized = "\n".join(lines).strip()
    if not normalized:
        raise AcquisitionError("No readable text was extracted from the document.")
    return normalized


def _title(filename: str, supplied_title: str | None) -> str:
    candidate = " ".join((supplied_title or "").split())
    if not candidate:
        candidate = Path(filename).stem.replace("_", " ").replace("-", " ").strip()
    return (candidate or "Uploaded document")[:200]


def detect_media_type(filename: str, data: bytes) -> str:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    for signature, media_type in IMAGE_SIGNATURES:
        if data.startswith(signature):
            return media_type
    if Path(filename).suffix.casefold() in TEXT_SUFFIXES and b"\x00" not in data[:4096]:
        return "text/plain"
    raise UnsupportedUpload(
        "Supported uploads are PDF, PNG, JPEG, TIFF, plain text, Markdown, CSV, and TSV."
    )


def _ocr_image(image: object) -> str:
    try:
        import pytesseract
        from pytesseract import TesseractNotFoundError
    except ImportError as exc:  # pragma: no cover - deployment packaging guard
        raise ExtractionUnavailable("The OCR Python dependency is unavailable.") from exc
    try:
        return str(pytesseract.image_to_string(image))
    except TesseractNotFoundError as exc:
        raise ExtractionUnavailable("The local Tesseract OCR engine is unavailable.") from exc


def _extract_image(data: bytes, *, max_image_pixels: int) -> tuple[str, str, int]:
    try:
        from PIL import Image, UnidentifiedImageError
        from PIL.Image import DecompressionBombError
    except ImportError as exc:  # pragma: no cover - deployment packaging guard
        raise ExtractionUnavailable("The image extraction dependency is unavailable.") from exc

    try:
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > max_image_pixels:
                raise AcquisitionError(
                    f"Image dimensions exceed the {max_image_pixels:,}-pixel limit."
                )
            image.load()
            text = _ocr_image(image.convert("RGB"))
    except (UnidentifiedImageError, DecompressionBombError) as exc:
        raise UnsupportedUpload("The uploaded image could not be decoded safely.") from exc
    return _normalized_text(text), "image-ocr", 1


def _extract_pdf(
    data: bytes,
    *,
    max_pages: int,
    max_image_pixels: int,
    native_text_threshold: int,
) -> tuple[str, str, int]:
    try:
        import fitz
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - deployment packaging guard
        raise ExtractionUnavailable("The PDF extraction dependency is unavailable.") from exc

    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise UnsupportedUpload("The uploaded PDF could not be opened.") from exc
    with document:
        page_count = document.page_count
        if page_count < 1:
            raise AcquisitionError("The PDF contains no pages.")
        if page_count > max_pages:
            raise AcquisitionError(f"PDF page count exceeds the {max_pages}-page limit.")

        sections: list[str] = []
        native_pages = 0
        ocr_pages = 0
        for index, page in enumerate(document):
            native_text = str(page.get_text("text") or "").strip()
            visible_chars = len(re.sub(r"\s+", "", native_text))
            page_text = native_text
            if visible_chars >= native_text_threshold:
                native_pages += 1
            else:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
                    width, height = image.size
                    if width * height > max_image_pixels:
                        raise AcquisitionError(
                            f"Rendered PDF page exceeds the {max_image_pixels:,}-pixel limit."
                        )
                    page_text = _ocr_image(image.convert("RGB")).strip()
                ocr_pages += 1
            if page_text.strip():
                sections.append(f"[Page {index + 1}]\n{page_text.strip()}")

    if native_pages and ocr_pages:
        method = "pdf-mixed"
    elif ocr_pages:
        method = "pdf-ocr"
    else:
        method = "pdf-text"
    return _normalized_text("\n\n".join(sections)), method, page_count


def extract_upload(
    data: bytes,
    *,
    filename: str | None,
    supplied_title: str | None,
    max_pages: int,
    max_extracted_chars: int,
    max_image_pixels: int,
    native_text_threshold: int = 24,
) -> ExtractedUpload:
    """Extract one upload without calling an external model or OCR service."""

    safe_name = safe_filename(filename)
    media_type = detect_media_type(safe_name, data)
    if media_type == "text/plain":
        try:
            body_text = _normalized_text(data.decode("utf-8-sig"))
        except UnicodeDecodeError as exc:
            raise UnsupportedUpload("Text uploads must use UTF-8 encoding.") from exc
        method = "plain-text"
        page_count = 1
    elif media_type == "application/pdf":
        body_text, method, page_count = _extract_pdf(
            data,
            max_pages=max_pages,
            max_image_pixels=max_image_pixels,
            native_text_threshold=native_text_threshold,
        )
    else:
        body_text, method, page_count = _extract_image(
            data,
            max_image_pixels=max_image_pixels,
        )

    if len(body_text) > max_extracted_chars:
        raise AcquisitionError(
            f"Extracted text exceeds the {max_extracted_chars:,}-character limit."
        )
    return ExtractedUpload(
        filename=safe_name,
        title=_title(safe_name, supplied_title),
        media_type=media_type,
        body_text=body_text,
        extraction_method=method,
        page_count=page_count,
    )
