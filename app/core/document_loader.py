import logging
import os

from app.config import settings
from app.utils.cache_utils import cached_resource
from app.utils.file_utils import _write_temp_file

logger = logging.getLogger(__name__)


def load_elements(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name
    return _load_elements_cached(file_bytes, file_name)


@cached_resource
def _load_elements_cached(file_bytes: bytes, file_name: str):
    lower_name = file_name.lower()
    is_image = lower_name.endswith((".png", ".jpg", ".jpeg"))

    if not lower_name.endswith(tuple(settings.SUPPORTED_EXTENSIONS)):
        raise ValueError(
            f"Unsupported file type for '{file_name}'. Supported types: {', '.join(settings.SUPPORTED_EXTENSIONS)}"
        )

    file_path = _write_temp_file(file_bytes, file_name)

    if is_image:
        logger.info("[IDP][IMAGE] Starting OCR partition for '%s'", file_name)
        tesseract_cmd = settings.get_tesseract_cmd()
        if tesseract_cmd:
            tesseract_dir = os.path.dirname(tesseract_cmd)
            os.environ["PATH"] = tesseract_dir + os.pathsep + os.environ.get("PATH", "")
            os.environ["TESSERACT_CMD"] = tesseract_cmd
            tessdata_dir = os.path.join(tesseract_dir, "tessdata")
            if os.path.isdir(tessdata_dir):
                os.environ.setdefault("TESSDATA_PREFIX", tessdata_dir)
            logger.info("[IDP][IMAGE] Using Tesseract at '%s'", tesseract_cmd)
        else:
            logger.warning("[IDP][IMAGE] No Tesseract binary found for image OCR")

        from unstructured.partition.image import partition_image

        elements = partition_image(
            filename=file_path,
            strategy="ocr_only",
            languages=["eng"],
        )
        logger.info(
            "[IDP][IMAGE] OCR partition completed for '%s' with %s elements",
            file_name,
            len(elements),
        )
    elif lower_name.endswith(".docx"):
        from unstructured.partition.docx import partition_docx

        elements = partition_docx(
            filename=file_path,
        )
    elif lower_name.endswith((".ppt", ".pptx")):
        from unstructured.partition.pptx import partition_pptx

        elements = partition_pptx(
            filename=file_path,
        )
    else:
        from unstructured.partition.pdf import partition_pdf

        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",
            infer_table_structure=True,
            extract_image_block_types=["Image"],
            extract_image_block_to_payload=True,
        )
    if is_image:
        logger.info("[IDP][IMAGE] Returning extracted elements for '%s'", file_name)
    return elements
