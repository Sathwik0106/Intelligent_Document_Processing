import random

import streamlit as st

from app.config import settings


def init_session_state():
    defaults = {
        "active_tab": "summary",
        "uploaded_file": None,
        "uploaded_file_hash": None,
        "pipeline_stage": 0,
        "show_json": False,
        "chat_history": [],
        "chat_ready": False,
        "rag_db": None,
        "rag_file_hash": None,
        "structured_json": None,
        "document_summary": None,
        "document_type": None,
        "processing_error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_global_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #f6f8fc;
    --surface: rgba(255, 255, 255, 0.84);
    --surface-strong: #ffffff;
    --border: rgba(15, 23, 42, 0.08);
    --text: #14213d;
    --muted: #64748b;
    --soft: #e8eef7;
    --primary: #2f6fed;
    --primary-deep: #1d4ed8;
    --primary-soft: #e8f0ff;
    --accent: #f59e0b;
    --success: #059669;
    --shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
}

html { box-sizing: border-box; }
*, *::before, *::after { box-sizing: inherit; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    font-family: 'Manrope', sans-serif !important;
    background:
        radial-gradient(circle at top left, rgba(47, 111, 237, 0.10), transparent 28%),
        radial-gradient(circle at top right, rgba(14, 165, 233, 0.08), transparent 22%),
        linear-gradient(180deg, #fbfcff 0%, #f5f8fc 48%, #f7f9fd 100%) !important;
    color: var(--text);
}

body {
    margin: 0;
    padding: 0;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"]    { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.block-container             { padding: 0 0 2rem !important; max-width: 100% !important; }

[data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
    gap: 0.5rem;
}

.idp-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 20px 30px;
    background: rgba(255, 255, 255, 0.78);
    backdrop-filter: blur(22px);
    border-bottom: 1px solid rgba(15, 23, 42, 0.06);
    position: sticky;
    top: 0;
    z-index: 200;
    box-shadow: 0 8px 30px rgba(15, 23, 42, 0.05);
}
.idp-navbar-main {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
}
.idp-navbar-logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--primary) 0%, #60a5fa 100%);
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 800; font-size: 13px;
    letter-spacing: -0.2px;
    flex-shrink: 0;
    box-shadow: 0 14px 28px rgba(47, 111, 237, 0.22);
}
.idp-navbar-copy {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
}
.idp-navbar-kicker {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--primary);
}
.idp-navbar-title {
    font-size: 17px;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.03em;
}
.idp-navbar-subtitle {
    font-size: 13px;
    color: var(--muted);
}
.idp-navbar-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 15px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(15, 23, 42, 0.07);
    color: var(--text);
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
}
.idp-navbar-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--success);
    box-shadow: 0 0 0 6px rgba(5, 150, 105, 0.10);
}

[data-testid="stHorizontalBlock"] {
    gap: 14px !important;
}

div[data-testid="stHorizontalBlock"] {
    margin-top: 22px !important;
}

.stButton {
    display: flex !important;
    width: 100% !important;
}

.stButton > button {
    background: rgba(255, 255, 255, 0.86) !important;
    color: var(--muted) !important;
    border: 1px solid rgba(15, 23, 42, 0.06) !important;
    border-radius: 14px !important;
    padding: 14px 16px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    width: 100% !important;
    min-height: 54px !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04) !important;
}

.stButton > button:hover {
    border-color: rgba(47, 111, 237, 0.18) !important;
    color: var(--primary) !important;
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06) !important;
}

.stButton > button:focus,
.stButton > button:active {
    box-shadow: 0 0 0 3px rgba(47, 111, 237, 0.14) !important;
    outline: none !important;
    color: var(--primary) !important;
    border: 1px solid rgba(47, 111, 237, 0.24) !important;
}

button[kind="primary"],
[data-testid="stBaseButton-primary"],
.stDownloadButton > button {
    background: linear-gradient(135deg, var(--primary) 0%, #4f8df7 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    font-family: 'Manrope', sans-serif !important;
    box-shadow: 0 14px 28px rgba(47, 111, 237, 0.22) !important;
    cursor: pointer !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.94) !important;
    border: 1.5px dashed rgba(47, 111, 237, 0.22) !important;
    border-radius: 18px !important;
    padding: 16px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

[data-testid="stFileUploaderDropzone"] * {
    color: var(--text) !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--primary) !important;
    background: rgba(232, 240, 255, 0.95) !important;
}

[data-testid="stFileUploader"] button {
    color: #ffffff !important;
    background: var(--primary) !important;
    border: none !important;
}

/* Keep Streamlit interaction overlays readable during reruns and uploads. */
[data-testid="stDialog"]::before,
[data-testid="stStatusWidget"],
[data-testid="stToast"],
[data-testid="stSpinner"] {
    color: var(--text) !important;
}

[data-testid="stDialog"] {
    background: rgba(15, 23, 42, 0.16) !important;
}

[data-testid="stDialog"] [role="dialog"] {
    background: #ffffff !important;
}

.page-body {
    padding: 28px 32px;
    max-width: 1280px;
    margin: 0 auto;
}

.hero-card {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at top right, rgba(96, 165, 250, 0.22), transparent 24%),
        radial-gradient(circle at bottom left, rgba(255, 255, 255, 0.18), transparent 26%),
        linear-gradient(135deg, #f8fbff 0%, #eef4ff 46%, #f8fbff 100%);
    color: var(--text);
    border-radius: 24px;
    padding: 30px;
    margin-bottom: 22px;
    border: 1px solid rgba(47, 111, 237, 0.08);
    box-shadow: var(--shadow);
}
.hero-card::after {
    content: "";
    position: absolute;
    right: -20px;
    top: -40px;
    width: 180px;
    height: 180px;
    border-radius: 999px;
    background: rgba(47, 111, 237, 0.08);
}
.hero-kicker {
    position: relative;
    z-index: 1;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--primary);
    margin-bottom: 10px;
}
.hero-title {
    position: relative;
    z-index: 1;
    font-size: clamp(1.8rem, 3vw, 2.5rem);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.04em;
    max-width: 680px;
}
.hero-text {
    position: relative;
    z-index: 1;
    margin-top: 12px;
    max-width: 650px;
    font-size: 14px;
    line-height: 1.7;
    color: #52637a;
}
.hero-meta-row {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
}
.hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(15, 23, 42, 0.08);
    font-size: 12px;
    font-weight: 700;
    color: #334155;
}

.card {
    background: var(--surface);
    backdrop-filter: blur(18px);
    border-radius: 18px;
    padding: 22px 24px;
    border: 1px solid var(--border);
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.05);
}
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.card-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, rgba(47, 111, 237, 0.12), rgba(96, 165, 250, 0.14));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    color: var(--primary-deep);
}
.card-title { font-size: 13px; font-weight: 700; color: var(--muted); }

.section-label {
    font-size: 10px; font-weight: 800;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 10px;
}

.preview-frame {
    width: 100%;
    height: 340px;
    background: linear-gradient(180deg, #fbfdff 0%, #f3f7fc 100%);
    border-radius: 18px;
    border: 1px solid var(--border);
    overflow: hidden;
    display: flex; align-items: center; justify-content: center;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
    padding: 18px;
}
.preview-frame img { width: 100%; height: 100%; object-fit: contain; display: block; }
.preview-canvas {
    width: 100%;
    height: 100%;
    border-radius: 14px;
    background: #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    box-shadow: 0 18px 38px rgba(15, 23, 42, 0.10);
}
.preview-pdf {
    width: 100%;
    height: 100%;
    border: none;
    border-radius: 14px;
    overflow: hidden;
    pointer-events: none;
}
.preview-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
    border-radius: 12px;
    background: #ffffff;
}
.preview-placeholder {
    display: flex; flex-direction: column; align-items: center;
    gap: 8px; color: var(--muted); font-size: 12px; text-align: center;
    padding: 24px;
}
.preview-icon { font-size: 34px; font-weight: 800; color: var(--primary); }

.verified-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: #e7f8ef; color: #0f766e;
    font-size: 11px; font-weight: 700;
    padding: 6px 12px; border-radius: 20px;
    border: 1px solid rgba(5, 150, 105, 0.10);
}

.status-card {
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.pill-banner {
    margin-top: 16px;
    padding: 15px 18px;
    background: linear-gradient(135deg, rgba(232, 240, 255, 0.95), rgba(245, 248, 255, 0.96));
    border-radius: 18px;
    border: 1px solid rgba(47, 111, 237, 0.10);
    font-size: 13px;
    color: #365172;
    line-height: 1.6;
}

.stTable table {
    width: 100%;
    border-collapse: collapse;
    border: 1px solid rgba(15, 23, 42, 0.08) !important;
    background: #ffffff !important;
    border-radius: 14px;
    overflow: hidden;
}
.stTable thead th {
    background: #f8fbff !important;
    color: #334155 !important;
    border-bottom: 1px solid #e7edf6 !important;
    border-right: 1px solid #f1f5fb !important;
    font-weight: 700 !important;
}
.stTable tbody td {
    background: #ffffff !important;
    color: #1f2937 !important;
    border-top: 1px solid #f1f5fa !important;
    border-right: 1px solid #f7f9fc !important;
}

[data-testid="stDialog"] [role="dialog"] {
    width: min(920px, 94vw) !important;
}
[data-testid="stDialog"] [data-testid="stCodeBlock"] {
    height: 62vh;
    max-height: 62vh;
    overflow-y: auto;
    border: 1px solid #2b2f45;
    border-radius: 10px;
}

.chat-shell {
    background: rgba(255, 255, 255, 0.76);
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
    padding: 18px;
}
.chat-wrap { max-width: 920px; margin: 0 auto; padding-bottom: 100px; }
.msg-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 24px; }
.msg-row.user { flex-direction: row-reverse; }
.avatar {
    width: 40px; height: 40px; border-radius: 14px;
    background: linear-gradient(135deg, var(--primary) 0%, #60a5fa 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0; color: #fff; font-weight: 800;
    box-shadow: 0 10px 20px rgba(47, 111, 237, 0.20);
}
.msg-content { max-width: 75%; }
.sender-label {
    font-size: 10px; font-weight: 800; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--muted); margin-bottom: 6px;
}
.msg-row.user .sender-label { text-align: right; }
.bubble {
    background: #ffffff; border: 1px solid var(--border);
    border-radius: 18px; padding: 15px 18px;
    font-size: 13.5px; color: #334155; line-height: 1.7;
    box-shadow: 0 10px 20px rgba(15, 23, 42, 0.04);
}
.bubble.user-bubble {
    background: linear-gradient(135deg, var(--primary) 0%, #4f8df7 100%);
    color: #ffffff; border: none;
    border-radius: 18px 18px 6px 18px;
}
.timestamp { font-size: 10px; color: #94a3b8; margin-top: 5px; }
.msg-row.user .timestamp { text-align: right; }

.answer-card {
    background: #ffffff; border: 1px solid var(--border);
    border-radius: 20px; padding: 18px 20px;
    font-size: 13.5px; color: #334155; line-height: 1.7;
    box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
}
.answer-card p,
.card p {
    margin: 0 0 10px 0;
}
.answer-card p:last-child,
.card p:last-child {
    margin-bottom: 0;
}
.answer-card ul,
.card ul {
    margin: 0 0 10px 18px;
    padding: 0;
}
.answer-card ul:last-child,
.card ul:last-child {
    margin-bottom: 0;
}
.answer-card li,
.card li {
    margin-bottom: 4px;
}
.answer-card code,
.card code {
    background: rgba(15, 23, 42, 0.06);
    padding: 2px 6px;
    border-radius: 6px;
    font-size: 0.92em;
}
.metrics-row { display: flex; gap: 14px; margin: 14px 0; flex-wrap: wrap; }
.metric-box {
    flex: 1; min-width: 120px;
    background: linear-gradient(180deg, #fbfdff 0%, #ffffff 100%);
    border: 1px solid #e8eef7;
    border-radius: 14px; padding: 14px 16px;
}
.metric-label { font-size: 11px; color: var(--muted); margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 800; color: var(--text); }
.metric-value.green { color: var(--success); }
.source-tag {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 11px; color: var(--muted); margin-top: 12px;
}
.reactions { display: flex; gap: 8px; margin-top: 8px; }
.react-btn {
    background: #e5e7eb; border: 1px solid #e5e7eb;
    border-radius: 6px; padding: 4px 10px; font-size: 14px; cursor: pointer;
}

[data-testid="stChatInput"] {
    max-width: 920px;
    margin: 0 auto;
}
[data-testid="stChatInput"] > div {
    border-radius: 18px !important;
    border: 1px solid rgba(47, 111, 237, 0.10) !important;
    box-shadow: 0 14px 28px rgba(15, 23, 42, 0.06) !important;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 380px;
    gap: 14px;
    text-align: center;
    padding: 32px 20px;
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid var(--border);
    box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
    color: var(--muted);
}
.empty-state-icon {
    width: 72px;
    height: 72px;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(47, 111, 237, 0.14), rgba(96, 165, 250, 0.16));
    color: var(--primary);
    font-size: 28px;
    font-weight: 800;
}

.section-stack {
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.structured-header-card {
    background: #ffffff;
    padding: 22px 24px;
    border-radius: 12px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
    margin-top: 24px;
}

.structured-header-copy {
    padding-right: 8px;
}

.structured-header-title {
    font-size: 24px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.03em;
    margin-bottom: 10px;
}

.structured-header-description {
    font-size: 13px;
    line-height: 1.7;
    color: #64748b;
    max-width: 760px;
}

.structured-actions-shell {
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;
    min-height: 100%;
}

.structured-button-group {
    width: 100%;
    max-width: 320px;
}

.structured-button-group [data-testid="stHorizontalBlock"] {
    gap: 12px !important;
    justify-content: flex-end;
    align-items: stretch;
}

.structured-button-group [data-testid="column"] {
    min-width: 0;
}

.structured-button-group div[data-testid="stButton"],
.structured-button-group div[data-testid="stDownloadButton"] {
    margin: 0;
}

.structured-button-group button {
    min-height: 40px;
}

@media (max-width: 768px) {
    .block-container { padding-bottom: 1.25rem !important; }
    .page-body { padding: 18px 14px; }
    .structured-header-card { padding: 18px; }
    .structured-actions-shell { margin-top: 14px; }
    .structured-button-group { max-width: none; }
    .structured-header-title { font-size: 20px; }
    .idp-navbar {
        padding: 14px 16px;
        align-items: flex-start;
        flex-direction: column;
    }
    .idp-navbar-status {
        width: 100%;
        justify-content: center;
    }
    .idp-navbar-title { font-size: 16px; }
    .idp-navbar-subtitle { font-size: 12px; }
    .chat-shell { padding: 12px; border-radius: 22px; }
    .chat-wrap { padding: 0 2px 100px; }
    .msg-content { max-width: 90%; }
    .hero-card { padding: 22px 18px; border-radius: 20px; }
    .card { padding: 18px; border-radius: 18px; }
    .preview-frame { height: 260px; border-radius: 18px; padding: 14px; }
    .stButton > button {
        min-height: 48px !important;
        padding: 12px 10px !important;
        font-size: 12px !important;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_runtime_alerts():
    if not settings.get_gemini_api_key():
        st.warning(
            "GEMINI_API_KEY is not configured. Summary, structured extraction, and AI Q&A will run in limited mode."
        )


def render_navbar_and_tabs():
    st.markdown(
        """
<div class="idp-navbar">
    <div class="idp-navbar-main">
        <div class="idp-navbar-logo">IDP</div>
        <div class="idp-navbar-copy">
            <div class="idp-navbar-kicker">Workspace</div>
            <span class="idp-navbar-title">Intelligent Document Processing</span>
            <div class="idp-navbar-subtitle">Upload, extract, summarize, and chat from one responsive dashboard.</div>
        </div>
    </div>
    <div class="idp-navbar-status">
        <span class="idp-navbar-status-dot"></span>
        AI workflow ready
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1], gap="small")

    with col1:
        if st.button(
            "Document Summary",
            key="btn_summary",
            width="stretch",
            type="primary" if st.session_state.active_tab == "summary" else "secondary",
        ):
            st.session_state.active_tab = "summary"
            st.rerun()

    with col2:
        if st.button(
            "Structured Data",
            key="btn_structured",
            width="stretch",
            type="primary" if st.session_state.active_tab == "structured" else "secondary",
        ):
            st.session_state.active_tab = "structured"
            st.rerun()

    with col3:
        if st.button(
            "Ask the Document",
            key="btn_qa",
            width="stretch",
            type="primary" if st.session_state.active_tab == "qa" else "secondary",
        ):
            st.session_state.active_tab = "qa"
            st.rerun()


DEMO_ANSWERS = [
    {
        "type": "rich",
        "intro": "According to the 'Regional Performance' table on page 14:",
        "metrics": [
            {"label": "September Revenue (APAC)", "value": "$4.28M", "green": False},
            {"label": "MoM Growth", "value": "+12.4%", "green": True},
        ],
        "body": "In August, the net revenue was <strong>$3.81M</strong>. The increase is primarily "
        "attributed to the new product launch in the Southeast Asian market during the first week of September.",
        "source": 'Page 14, Section 3.2 "Regional Growth Metrics"',
    },
    {
        "type": "rich",
        "intro": "Based on the invoice line items extracted:",
        "metrics": [
            {"label": "Total Amount Due", "value": "$12,450", "green": False},
            {"label": "Payment Terms", "value": "Net-30", "green": True},
        ],
        "body": "The invoice includes three service items: Cloud Infrastructure, Data Storage, "
        "and Security Audit. A <strong>5% discount</strong> was applied to the storage upgrade.",
        "source": 'Invoice, Section 1 "Billing Summary"',
    },
    {
        "type": "text",
        "text": "The document does not contain explicit information about that. "
        "Based on context, the vendor is <strong>Acme Global Solutions Inc.</strong> "
        "with Tax ID <strong>TX-99821-B45</strong>. Shall I look for related figures?",
    },
]


def ai_response(q: str) -> dict:
    q = q.lower()
    if any(k in q for k in ["revenue", "apac", "september", "august", "growth"]):
        return DEMO_ANSWERS[0]
    if any(k in q for k in ["invoice", "total", "amount", "payment", "line"]):
        return DEMO_ANSWERS[1]
    return random.choice(DEMO_ANSWERS)
