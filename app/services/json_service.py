import json
import logging
from io import BytesIO

from google import genai

from app.config import settings
from app.core.document_loader import load_elements
from app.services.image_ai_service import is_image_file
from app.utils.cache_utils import cached_resource

logger = logging.getLogger(__name__)


class GeminiJSONExtractor:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def extract_json(self, extracted_text: str) -> dict:
        if not extracted_text.strip():
            return {}

        prompt = """
You are an enterprise-grade Intelligent Document Processing (IDP) engine.

OBJECTIVE:
Convert the document into a FULLY TABULAR structured JSON format.
By viewing only the tables, a person must understand the entire document.

---

## STRICT OUTPUT REQUIREMENTS (MANDATORY)

* Return ONLY valid JSON.
* No explanations.
* No markdown.
* No extra text.
* No trailing commas.
* Use double quotes only.
* Must be directly parsable using json.loads().
* STRICTLY follow the schema.

---

## CRITICAL ENFORCEMENT RULES (DO NOT VIOLATE)

1. "primary_entity" MUST contain EXACTLY ONE object.
2. ALL extracted fields MUST be inside that ONE object.
3. NEVER split attributes into multiple objects.
4. If you create multiple objects -> YOUR OUTPUT IS WRONG -> FIX IT BEFORE RETURNING.

---

## REQUIRED JSON SCHEMA

{
"document_type": "string",
"tables": {
"primary_entity": [
{ "column_name": "value" }
],
"additional_table_name": [
{ "column_name": "value" }
]
}
}

---

## CORRECT VS WRONG FORMAT (STRICT)

CORRECT:
"primary_entity": [
{
"document_title": "INCOME TAX DEPARTMENT",
"document_id_number": "23",
"name": "ABC"
}
]

WRONG:
"primary_entity": [
{"document_title": "INCOME TAX DEPARTMENT"},
{"document_id_number": "23"},
{"name": "ABC"}
]

IF YOU PRODUCE WRONG FORMAT -> REGENERATE INTERNALLY.

---

## STRUCTURING RULES

1. ALL structured information MUST be inside "tables".
2. Do NOT create a "metadata" section.
3. Every document MUST contain "primary_entity".
4. Create additional tables ONLY for repeating rows.
5. Table names -> lowercase snake_case.
6. Column names -> lowercase snake_case.
7. No important information outside tables.

---

## TEXT CORRECTION RULES

1. Fix OCR mistakes.
2. DO NOT modify:

   * IDs
   * PAN numbers
   * Dates
   * Numeric values
3. Preserve meaning.
4. If unsure -> keep original.
5. For missing values, use null (JSON null), never "N/A".

---

## SELF-VALIDATION STEP (VERY IMPORTANT)

Before returning output:

* Check if "primary_entity" has ONLY ONE object.
* Check if all fields are merged into that object.
* If NOT -> FIX automatically.

---

## DOCUMENT TEXT

""" + extracted_text

        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        )

        try:
            return json.loads((response.text or "").strip())
        except (json.JSONDecodeError, AttributeError, TypeError):
            return {}


class _UploadedFileLike(BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name

    def getvalue(self):
        return super().getvalue()


@cached_resource
def extract_text_from_elements(file_bytes: bytes, file_name: str) -> str:
    is_image = is_image_file(file_name)
    if is_image:
        logger.info("[IDP][IMAGE] Starting text extraction for '%s'", file_name)

    uploaded_like = _UploadedFileLike(file_bytes, file_name)
    elements = load_elements(uploaded_like)

    text_parts: list[str] = []
    for element in elements:
        if getattr(element, "text", None):
            text_parts.append(element.text)

    text = "\n".join(text_parts)
    if is_image:
        logger.info(
            "[IDP][IMAGE] Text extraction completed for '%s' with %s characters",
            file_name,
            len(text),
        )
    return text


@cached_resource
def process_document_from_upload(file_bytes: bytes, file_name: str, api_key: str):
    is_image = is_image_file(file_name)
    if is_image:
        logger.info("[IDP][IMAGE] Starting structured extraction for '%s'", file_name)

    text = extract_text_from_elements(file_bytes, file_name)
    empty_response = {"document_type": "unknown", "tables": {"primary_entity": []}}
    if not text.strip():
        return empty_response
    if not api_key:
        return empty_response

    extractor = GeminiJSONExtractor(api_key)
    try:
        result = extractor.extract_json(text)
        if is_image:
            logger.info("[IDP][IMAGE] Structured extraction completed for '%s'", file_name)
    except Exception:
        if is_image:
            logger.exception("[IDP][IMAGE] Structured extraction failed for '%s'", file_name)
        return empty_response

    if not isinstance(result, dict):
        return empty_response
    if "tables" not in result or not isinstance(result.get("tables"), dict):
        result["tables"] = {}
    result["tables"].setdefault("primary_entity", [])
    return result


def generate_structured_json(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    api_key = settings.get_gemini_api_key()
    return process_document_from_upload(file_bytes, file_name, api_key)
