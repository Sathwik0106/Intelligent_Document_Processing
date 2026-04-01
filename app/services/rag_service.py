import hashlib
import logging
from typing import Optional

from google import genai
from langchain_chroma import Chroma

from app.config import settings
from app.core.chunking import create_chunks, summarise_chunks
from app.core.document_loader import _load_elements_cached
from app.core.embeddings import get_embedding_model
from app.services.image_ai_service import is_image_file
from app.utils.cache_utils import cached_resource

logger = logging.getLogger(__name__)


@cached_resource
def build_vector_db(file_bytes: bytes, file_name: str) -> Optional[Chroma]:
    is_image = is_image_file(file_name)
    if is_image:
        logger.info("[IDP][IMAGE] Starting RAG build for '%s'", file_name)
    elements = _load_elements_cached(file_bytes, file_name)

    chunks = create_chunks(elements)
    if is_image:
        logger.info("[IDP][IMAGE] Chunking completed for '%s' with %s chunks", file_name, len(chunks))

    processed_chunks = summarise_chunks(chunks)
    if not processed_chunks:
        if is_image:
            logger.warning(
                "[IDP][IMAGE] RAG build stopped because no processed chunks were created for '%s'",
                file_name,
            )
        return None

    embedding_model = get_embedding_model()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    persist_directory = settings.VECTOR_STORE_DIR / file_hash
    persist_directory.mkdir(parents=True, exist_ok=True)

    try:
        db = Chroma.from_documents(
            documents=processed_chunks,
            embedding=embedding_model,
            collection_name=f"doc_{file_hash}",
            persist_directory=str(persist_directory),
        )
        if is_image:
            logger.info("[IDP][IMAGE] RAG build completed for '%s'", file_name)
        return db
    except ValueError as exc:
        if "Expected Embeddings to be non-empty" in str(exc):
            if is_image:
                logger.warning(
                    "[IDP][IMAGE] RAG build failed because embeddings were empty for '%s'",
                    file_name,
                )
            return None
        raise


def build_vector_db_from_upload(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    return build_vector_db(file_bytes, file_name)


def query_rag(query: str, db: Chroma):
    api_key = settings.get_gemini_api_key()
    client = genai.Client(api_key=api_key) if api_key else None
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not set")

    retriever = db.as_retriever(search_kwargs={"k": settings.RAG_RETRIEVAL_K})
    retrieved_chunks = retriever.invoke(query)
    if not retrieved_chunks:
        return "I could not find enough relevant context in the document to answer that confidently."

    parts = [f"Answer the question based on the document text: {query}\n\nContext:\n"]
    for doc in retrieved_chunks:
        parts.append(doc.page_content)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=parts,
    )
    return (response.text or "").strip() or "I could not generate an answer for that question."
