import json

from langchain_core.documents import Document
from unstructured.chunking.title import chunk_by_title

from app.config import settings
from app.core.embeddings import create_ai_enhanced_summary


def separate_content_types(chunk):
    content_data = {
        "text": chunk.text,
        "tables": [],
        "images": [],
        "types": ["text"],
    }

    if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
        for element in chunk.metadata.orig_elements:
            element_type = type(element).__name__

            if element_type == "Table":
                content_data["types"].append("table")
                table_html = getattr(element.metadata, "text_as_html", element.text)
                content_data["tables"].append(table_html)

            elif element_type == "Image":
                if hasattr(element, "metadata") and hasattr(element.metadata, "image_base64"):
                    content_data["types"].append("image")
                    content_data["images"].append(element.metadata.image_base64)

    return content_data


def create_chunks(elements):
    return chunk_by_title(
        elements,
        max_characters=settings.CHUNK_MAX_CHARACTERS,
        new_after_n_chars=settings.CHUNK_NEW_AFTER_N_CHARS,
        combine_text_under_n_chars=settings.CHUNK_COMBINE_TEXT_UNDER_N_CHARS,
    )


def summarise_chunks(chunks):
    langchain_documents = []

    for chunk in chunks:
        content_data = separate_content_types(chunk)
        raw_text = (content_data.get("text") or "").strip()

        if not raw_text and not content_data["tables"] and not content_data["images"]:
            continue

        if content_data["tables"] or content_data["images"]:
            enhanced_content = create_ai_enhanced_summary(
                raw_text,
                content_data["tables"],
                content_data["images"],
            )
        else:
            enhanced_content = raw_text

        enhanced_content = (enhanced_content or "").strip()
        if not enhanced_content:
            continue

        doc = Document(
            page_content=enhanced_content,
            metadata={
                "original_content": json.dumps(
                    {
                        "raw_text": raw_text,
                        "tables_html": content_data["tables"],
                        "images_base64": content_data["images"],
                    }
                )
            },
        )
        langchain_documents.append(doc)

    return langchain_documents
