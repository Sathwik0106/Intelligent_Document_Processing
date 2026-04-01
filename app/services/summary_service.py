import json
import logging

from google import genai

from app.config import settings
from app.services.image_ai_service import is_image_file
from app.services.json_service import extract_text_from_elements
from app.utils.cache_utils import cached_resource

logger = logging.getLogger(__name__)


class GeminiDocumentSummarizer:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def summarize(self, extracted_text: str, file_name: str) -> str:
        prompt = f"""
You are an enterprise document analyst.

Create an executive summary for this document for a business user.

Requirements:
- Keep it concise and clear.
- Use 4-6 sentences.
- Highlight key entities, values, dates, and obligations if present.
- Do not invent information.
- If data is missing, avoid assumptions.

Document Name: {file_name}

Document Text:
{extracted_text}
"""

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"temperature": 0.2},
        )
        return (response.text or "").strip()


class GeminiDocumentClassifier:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def classify(self, extracted_text: str, file_name: str) -> str:
        prompt = f"""
You are an expert document classification system for an Intelligent Document Processing platform.

Classify the uploaded file into the most accurate business-friendly document type.

Rules:
- Return only valid JSON.
- Use this schema: {{"document_type":"string"}}
- Prefer specific labels such as Invoice, Receipt, Bank Statement, Marksheet, Medical Prescription,
  Government ID, Government Certificate, Utility Bill, Contract, Tax Document, Resume, Report,
  Academic Transcript, Application Form, Insurance Document, or Letter.
- If the exact type is unclear, return the nearest high-level label like Government Document, Medical Document,
  Financial Document, or General Document.
- Do not include explanations.

Document Name: {file_name}

Document Text:
{extracted_text}
"""

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        )

        try:
            payload = json.loads((response.text or "").strip())
        except (json.JSONDecodeError, TypeError, AttributeError):
            return ""

        return str(payload.get("document_type") or "").strip()


@cached_resource
def generate_document_summary_cached(file_bytes: bytes, file_name: str, api_key: str) -> str:
    is_image = is_image_file(file_name)
    if is_image:
        logger.info("[IDP][IMAGE] Starting summary generation for '%s'", file_name)
    text = extract_text_from_elements(file_bytes, file_name)
    if not text.strip():
        if is_image:
            logger.warning("[IDP][IMAGE] Summary skipped because no text was extracted for '%s'", file_name)
        return "No extractable text was found in this document."
    if not api_key:
        if is_image:
            logger.warning("[IDP][IMAGE] Summary skipped because GEMINI_API_KEY is missing for '%s'", file_name)
        return "Summary unavailable because GEMINI_API_KEY is not configured."

    try:
        summarizer = GeminiDocumentSummarizer(api_key)
        summary = summarizer.summarize(text, file_name)
        if summary:
            if is_image:
                logger.info("[IDP][IMAGE] Summary generation completed for '%s'", file_name)
            return summary
    except Exception:
        if is_image:
            logger.exception("[IDP][IMAGE] Summary generation failed for '%s'", file_name)

    return "The document has been processed successfully, but a summary could not be generated at this time."


@cached_resource
def generate_document_type_cached(file_bytes: bytes, file_name: str, api_key: str) -> str:
    is_image = is_image_file(file_name)
    if is_image:
        logger.info("[IDP][IMAGE] Starting document type classification for '%s'", file_name)
    text = extract_text_from_elements(file_bytes, file_name)
    if not text.strip():
        if is_image:
            logger.warning(
                "[IDP][IMAGE] Document type fallback because no text was extracted for '%s'",
                file_name,
            )
        return "Document"
    if not api_key:
        if is_image:
            logger.warning(
                "[IDP][IMAGE] Document type fallback because GEMINI_API_KEY is missing for '%s'",
                file_name,
            )
        return _fallback_document_type(file_name, "")

    try:
        classifier = GeminiDocumentClassifier(api_key)
        document_type = classifier.classify(text, file_name)
        if document_type:
            if is_image:
                logger.info(
                    "[IDP][IMAGE] Document type classification completed for '%s': %s",
                    file_name,
                    document_type,
                )
            return document_type
    except Exception:
        if is_image:
            logger.exception("[IDP][IMAGE] Document type classification failed for '%s'", file_name)

    return _fallback_document_type(file_name, text)


def generate_document_summary(uploaded_file) -> str:
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    api_key = settings.get_gemini_api_key()
    return generate_document_summary_cached(file_bytes, file_name, api_key)


def generate_document_type(uploaded_file) -> str:
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    api_key = settings.get_gemini_api_key()
    return generate_document_type_cached(file_bytes, file_name, api_key)


def _fallback_document_type(file_name: str, extracted_text: str) -> str:
    haystack = f"{file_name}\n{extracted_text}".lower()
    checks = [
        ("marksheet", "Marksheet"),
        ("transcript", "Academic Transcript"),
        ("invoice", "Invoice"),
        ("receipt", "Receipt"),
        ("prescription", "Medical Prescription"),
        ("medical", "Medical Document"),
        ("aadhaar", "Government ID"),
        ("passport", "Government ID"),
        ("driving licence", "Government ID"),
        ("driver license", "Government ID"),
        ("government", "Government Document"),
        ("bank statement", "Bank Statement"),
        ("statement", "Statement"),
        ("bill", "Utility Bill"),
        ("tax", "Tax Document"),
        ("certificate", "Certificate"),
        ("resume", "Resume"),
        ("contract", "Contract"),
        ("report", "Report"),
    ]
    for needle, label in checks:
        if needle in haystack:
            return label
    return "Document"
