import logging
from typing import Any, List

from google import genai

from app.config import settings
from app.utils.cache_utils import cached_resource

logger = logging.getLogger(__name__)


def create_ai_enhanced_summary(text: str, tables: List[str], images: List[str]) -> str:
    try:
        prompt_text = f"""
You are creating a searchable description for document content retrieval.

CONTENT TO ANALYZE:

TEXT CONTENT:
{text}
"""

        if tables:
            prompt_text += "\nTABLES:\n"
            for i, table in enumerate(tables):
                prompt_text += f"Table {i + 1}:\n{table}\n\n"

        prompt_text += """
YOUR TASK:
Generate a comprehensive, searchable description.
"""

        api_key = settings.get_gemini_api_key()
        client = genai.Client(api_key=api_key) if api_key else None
        if client is None:
            raise RuntimeError("Missing GEMINI_API_KEY")

        contents = [{"text": prompt_text}]
        for img_base64 in images:
            contents.append(
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img_base64,
                    }
                }
            )

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
        )
        return response.text
    except Exception:
        logger.warning("Falling back to a text-only retrieval summary.", exc_info=True)
        summary = f"{text[:300]}..."
        if tables:
            summary += f" [Contains {len(tables)} table(s)]"
        if images:
            summary += f" [Contains {len(images)} image(s)]"
        return summary


@cached_resource
def get_embedding_model() -> Any:
    # Import lazily so the sentence-transformers / transformers stack is loaded
    # only when Q&A retrieval is actually used.
    from langchain_huggingface.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
