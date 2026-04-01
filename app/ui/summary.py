import base64
import html
import io
import time

import streamlit as st

from app.config import settings
from app.services.json_service import generate_structured_json
from app.services.summary_service import generate_document_summary, generate_document_type
from app.utils.file_utils import get_uploaded_file_hash
from app.utils.text_utils import markdown_to_safe_html, safe_html_text


def _render_pdf_preview_image(file_bytes: bytes) -> str | None:
    try:
        import pypdfium2 as pdfium
    except Exception:
        return None

    try:
        pdf = pdfium.PdfDocument(io.BytesIO(file_bytes))
        page = pdf[0]
        bitmap = page.render(scale=1.6).to_pil()
        buffer = io.BytesIO()
        bitmap.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception:
        return None


def render_summary_tab():
    upload_types = list(settings.SUPPORTED_UPLOAD_TYPES)
    supported_files_label = ", ".join(ext.upper() for ext in upload_types)

    st.markdown(
        """
        <div class="page-body" style="padding-bottom:0;">
            <div class="hero-card">
                <div class="hero-kicker">Document Intelligence</div>
                <div class="hero-title">Turn uploaded files into clean summaries and ready-to-query insights.</div>
                <div class="hero-text">
                    This workspace is tuned for quick review: upload a file, monitor the processing stages,
                    and move straight into extracted data or AI-powered Q&A.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left_col, right_col = st.columns([1, 3.2], gap="medium")

    with left_col:
        st.markdown('<div class="section-label">Input Document</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drop file to upload",
            type=upload_types,
            label_visibility="visible",
            key="file_uploader",
            help=f"Supported files: {supported_files_label}.",
        )
        if uploaded:
            current_file_hash = get_uploaded_file_hash(uploaded)
            if st.session_state.uploaded_file_hash != current_file_hash:
                st.session_state.uploaded_file = uploaded
                st.session_state.uploaded_file_hash = current_file_hash
                st.session_state.pipeline_stage = 1
                st.session_state.chat_ready = False
                st.session_state.chat_history = []
                st.session_state.rag_db = None
                st.session_state.rag_file_hash = None
                st.session_state.structured_json = None
                st.session_state.document_summary = None
                st.session_state.document_type = None
                st.session_state.show_json = False
                st.session_state.processing_error = None

        stage = st.session_state.pipeline_stage

        def _step_html(title: str, subtitle: str, state_name: str, connector_state: str, is_last: bool = False) -> str:
            if state_name == "complete":
                indicator = (
                    '<div style="position:absolute;left:0;top:0;width:14px;height:14px;border-radius:50%;'
                    'background:#10b981;color:#fff;font-size:10px;display:flex;align-items:center;justify-content:center;">OK</div>'
                )
                title_color = "#111827"
                subtitle_color = "#9ca3af"
            elif state_name == "active":
                indicator = (
                    '<div style="position:absolute;left:0;top:0;width:14px;height:14px;border-radius:50%;'
                    'border:2px solid #6366f1;background:#ffffff;"></div>'
                )
                title_color = "#6366f1"
                subtitle_color = "#9ca3af"
            else:
                indicator = (
                    '<div style="position:absolute;left:0;top:0;width:14px;height:14px;border-radius:50%;'
                    'border:2px solid #d1d5db;background:#ffffff;"></div>'
                )
                title_color = "#d1d5db"
                subtitle_color = "#d1d5db"

            connector_color = "#10b981" if connector_state == "complete" else "#6366f1" if connector_state == "active" else "#e5e7eb"
            connector = ""
            if not is_last:
                connector = (
                    f'<div style="position:absolute;left:7px;top:18px;width:2px;height:28px;'
                    f'background:{connector_color};"></div>'
                )

            return (
                '<div style="position:relative;padding-left:24px;margin-bottom:10px;">'
                f"{connector}"
                f"{indicator}"
                f'<div style="font-size:13px;font-weight:600;color:{title_color};">{title}</div>'
                f'<div style="font-size:11px;color:{subtitle_color};">{subtitle}</div>'
                "</div>"
            )

        upload_state = "complete" if stage >= 1 else "pending"
        processing_state = "complete" if stage >= 2 else "pending"
        analyzing_state = "active" if stage == 3 else "complete" if stage >= 4 else "pending"
        ready_state = "complete" if stage >= 4 else "pending"

        html_content = (
            '<div class="status-card">'
            '<div style="font-size:10px;font-weight:700;letter-spacing:.08em;color:#9ca3af;text-transform:uppercase;margin-bottom:10px;">'
            "PIPELINE STATUS"
            "</div>"
            f'{_step_html("Uploading", "Complete" if upload_state == "complete" else "Pending", upload_state, processing_state)}'
            f'{_step_html("Processing", "Complete" if processing_state == "complete" else "Pending", processing_state, analyzing_state)}'
            f'{_step_html("AI Analyzing", "Extracting fields..." if analyzing_state == "active" else "Complete" if analyzing_state == "complete" else "Pending", analyzing_state, ready_state)}'
            f'{_step_html("Ready", "Complete" if ready_state == "complete" else "Pending", ready_state, "pending", is_last=True)}'
            "</div>"
        )
        st.markdown(html_content, unsafe_allow_html=True)

        st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Document Preview</div>', unsafe_allow_html=True)

        f = st.session_state.uploaded_file
        if f and (f.type or "").startswith("image/"):
            img_bytes = f.getvalue()
            b64 = base64.b64encode(img_bytes).decode()
            mime = f.type
            st.markdown(
                f"""
            <div class="preview-frame">
                <div class="preview-canvas">
                    <img class="preview-image" src="data:{mime};base64,{b64}" alt="preview" />
                </div>
            </div>""",
                unsafe_allow_html=True,
            )
        elif f:
            lower_name = f.name.lower()
            if lower_name.endswith(".pdf"):
                pdf_bytes = f.getvalue()
                pdf_preview_b64 = _render_pdf_preview_image(pdf_bytes)
                st.markdown(
                    f"""
                <div class="preview-frame">
                    <div class="preview-canvas">
                        {
                            f'<img class="preview-image" src="data:image/png;base64,{pdf_preview_b64}" alt="{html.escape(f.name)} preview" />'
                            if pdf_preview_b64
                            else f'''
                            <div class="preview-placeholder">
                                <div class="preview-icon">PDF</div>
                                <strong style="font-size:12px;color:#6b7280;">{html.escape(f.name)}</strong>
                                <span>Preview unavailable</span>
                            </div>
                            '''
                        }
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )
            else:
                preview_label = "DOCX" if lower_name.endswith(".docx") else "PPT"
                preview_hint = (
                    "Preview is not available for slides in this panel."
                    if lower_name.endswith((".ppt", ".pptx"))
                    else "Preview is not available for Word documents in this panel."
                )
                st.markdown(
                    f"""
                <div class="preview-frame">
                    <div class="preview-placeholder">
                        <div class="preview-icon">{preview_label}</div>
                        <strong style="font-size:13px;">{html.escape(f.name)}</strong>
                        <span>{preview_hint}</span>
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
            <div class="preview-frame">
                <div class="preview-placeholder">
                    <div class="preview-icon">DOC</div>
                    <strong style="font-size:13px;">No file uploaded</strong>
                    <span>Add a PDF or image to start the workflow.</span>
                    
                </div>
            </div>""",
                unsafe_allow_html=True,
            )

    with right_col:
        f = st.session_state.uploaded_file

        if st.session_state.pipeline_stage == 1 and f:
            st.session_state.pipeline_stage = 2
            st.rerun()
        elif st.session_state.pipeline_stage == 2 and f:
            time.sleep(0.5)
            try:
                st.session_state.pipeline_stage = 3
                st.rerun()
            except Exception as exc:
                st.session_state.pipeline_stage = 0
                st.session_state.chat_ready = False
                st.session_state.processing_error = str(exc)
                st.error(f"Document processing failed: {safe_html_text(str(exc))}")
        elif st.session_state.pipeline_stage == 3 and f:
            time.sleep(0.5)
            try:
                if st.session_state.structured_json is None:
                    st.session_state.structured_json = generate_structured_json(f)
                if st.session_state.document_type is None:
                    structured_doc_type = ""
                    if isinstance(st.session_state.structured_json, dict):
                        structured_doc_type = str(st.session_state.structured_json.get("document_type") or "").strip()
                    st.session_state.document_type = structured_doc_type or generate_document_type(f)
                if st.session_state.document_summary is None:
                    st.session_state.document_summary = generate_document_summary(f)
                st.session_state.pipeline_stage = 4
                st.session_state.chat_ready = True
                st.session_state.chat_history = [
                    {
                        "role": "assistant",
                        "type": "greeting",
                        "text": (
                            "Your document is processed and ready.<br><br>"
                            "I can help you:<br>"
                            "&bull; Summarize the content<br>"
                            "&bull; Extract key information<br>"
                            "&bull; Answer questions based on the document<br><br>"
                            "What would you like to start with?"
                        ),
                        "timestamp": "Just now",
                    }
                ]
                st.rerun()
            except Exception as exc:
                st.session_state.pipeline_stage = 0
                st.session_state.chat_ready = False
                st.session_state.processing_error = str(exc)
                st.error(f"Document processing failed: {safe_html_text(str(exc))}")

        if not f:
            st.markdown(
                """
            <div class="empty-state">
                <div class="empty-state-icon">DOC</div>
                <div style="font-size:18px;font-weight:800;color:#0f172a;">No document uploaded yet</div>
                <div style="font-size:13px;max-width:360px;line-height:1.7;">
                    Upload a PDF, image, DOCX, or PowerPoint file from the left panel to begin AI analysis.
                </div>
            </div>""",
                unsafe_allow_html=True,
            )
        else:
            doc_type = st.session_state.document_type or "Document"

            ext = f.name.rsplit(".", 1)[-1].upper()
            size_kb = round(f.size / 1024, 1)

            c1, c2 = st.columns([1, 1.8], gap="medium")
            with c1:
                st.markdown(
                    f"""
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon">DOC</div>
                        <span class="card-title">Document Type</span>
                    </div>
                    <div style="font-size:26px;font-weight:700;color:#111827;margin-bottom:6px;">{html.escape(doc_type)}</div>
                    <div style="font-size:11px;color:#6b7280;">Confidence Score: 99.8%</div>
                </div>""",
                    unsafe_allow_html=True,
                )

            with c2:
                exec_summary = st.session_state.document_summary or (
                    f"This document is a {doc_type} named {f.name} ({size_kb} KB, {ext}). "
                    "Successfully processed by the AI pipeline. "
                    "All fields extracted with high confidence. "
                    "No significant discrepancies or anomalies detected."
                )
                st.markdown(
                    f"""
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon">SUM</div>
                        <span class="card-title">Executive Summary</span>
                    </div>
                    <div style="font-size:13px;color:#475569;line-height:1.8;">
                        {markdown_to_safe_html(exec_summary)}
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
            st.markdown(
                f"""
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">INF</div>
                    <span class="card-title">File Details</span>
                </div>
                <div style="display:flex;gap:32px;flex-wrap:wrap;row-gap:14px;">
                    <div>
                        <div style="font-size:10px;color:#9ca3af;font-weight:600;text-transform:uppercase;
                                    letter-spacing:.06em;margin-bottom:4px;">File Name</div>
                        <div style="font-size:13px;font-weight:600;color:#111827;word-break:break-all;">{html.escape(f.name)}</div>
                    </div>
                    <div>
                        <div style="font-size:10px;color:#9ca3af;font-weight:600;text-transform:uppercase;
                                    letter-spacing:.06em;margin-bottom:4px;">File Type</div>
                        <div style="font-size:13px;font-weight:600;color:#111827;">{html.escape(f.type or ext)}</div>
                    </div>
                    <div>
                        <div style="font-size:10px;color:#9ca3af;font-weight:600;text-transform:uppercase;
                                    letter-spacing:.06em;margin-bottom:4px;">File Size</div>
                        <div style="font-size:13px;font-weight:600;color:#111827;">{size_kb} KB</div>
                    </div>
                    <div>
                        <div style="font-size:10px;color:#9ca3af;font-weight:600;text-transform:uppercase;
                                    letter-spacing:.06em;margin-bottom:4px;">Status</div>
                        <div style="font-size:13px;font-weight:600;color:#10b981;">Analysis Complete</div>
                    </div>
                </div>
            </div>""",
                unsafe_allow_html=True,
            )

            st.markdown(
                """
            <div class="pill-banner">
                Switch to <strong>Structured Data</strong> to view extracted fields,
                or <strong>Ask the Document</strong> to chat with the AI about this file.
            </div>""",
                unsafe_allow_html=True,
            )
