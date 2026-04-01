import html
import time

import streamlit as st

from app.ui.components import ai_response
from app.utils.text_utils import markdown_to_safe_html, safe_html_text


def render_qa_tab():
    from app.services.rag_service import build_vector_db_from_upload, query_rag

    st.markdown(
        """
        <div class="card" style="margin-bottom:18px;">
            <div class="card-header">
                <div class="card-icon">AI</div>
                <span class="card-title">Ask The Document</span>
            </div>
            <div style="font-size:24px;font-weight:800;color:#0f172a;letter-spacing:-0.03em;margin-bottom:8px;">
                Chat with the uploaded file and surface answers faster.
            </div>
            <div style="font-size:13px;line-height:1.7;color:#64748b;max-width:760px;">
                The conversation view is optimized for both desktop and mobile, with room for richer answers,
                extracted metrics, and source-backed responses.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if (
        not st.session_state.chat_history
        and st.session_state.uploaded_file
        and st.session_state.chat_ready
    ):
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

    if not st.session_state.uploaded_file or not st.session_state.chat_ready:
        st.markdown(
            """
            <div class="card" style="margin-top:18px;">
                <div style="font-size:18px;font-weight:800;color:#0f172a;margin-bottom:8px;">
                    Upload and process a document to start chatting
                </div>
                <div style="font-size:13px;line-height:1.7;color:#64748b;max-width:720px;">
                    Once the file finishes processing, the assistant will open with a ready state and you can ask questions about the uploaded content.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for msg in st.session_state.chat_history:
        if msg["role"] == "assistant":
            if msg["type"] == "greeting":
                st.markdown(
                    f"""
                <div class="msg-row">
                    <div class="avatar">AI</div>
                    <div class="msg-content">
                        <div class="sender-label">IDP Assistant</div>
                        <div class="bubble">{msg["text"]}</div>
                        <div class="timestamp">{msg["timestamp"]}</div>
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )
            elif msg["type"] == "pending":
                st.markdown(
                    f"""
                <div class="msg-row">
                    <div class="avatar">AI</div>
                    <div class="msg-content" style="max-width:82%;">
                        <div class="sender-label">IDP Assistant</div>
                        <div class="answer-card" style="color:#64748b;">{markdown_to_safe_html(msg["text"])}</div>
                        <div class="timestamp">{msg["timestamp"]}</div>
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )
            elif msg["type"] == "text":
                st.markdown(
                    f"""
                <div class="msg-row">
                    <div class="avatar">AI</div>
                    <div class="msg-content" style="max-width:82%;">
                        <div class="sender-label">IDP Assistant</div>
                        <div class="answer-card">{markdown_to_safe_html(msg["text"])}</div>
                        <div class="timestamp">{msg["timestamp"]}</div>
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )
            elif msg["type"] == "rich":
                metrics_html = ""
                for metric in msg.get("metrics", []):
                    value_class = "metric-value green" if metric["green"] else "metric-value"
                    metrics_html += f"""
                    <div class="metric-box">
                        <div class="metric-label">{html.escape(metric["label"])}</div>
                        <div class="{value_class}">{html.escape(metric["value"])}</div>
                    </div>"""
                st.markdown(
                    f"""
                <div class="msg-row">
                    <div class="avatar">AI</div>
                    <div class="msg-content" style="max-width:82%;">
                        <div class="sender-label">IDP Assistant</div>
                        <div class="answer-card">
                            <div style="margin-bottom:2px;">{msg["intro"]}</div>
                            <div class="metrics-row">{metrics_html}</div>
                            <div>{msg["body"]}</div>
                            <div class="source-tag">Source: {html.escape(msg["source"])}</div>
                        </div>
                        <div class="timestamp">{msg["timestamp"]}</div>
                    </div>
                </div>""",
                    unsafe_allow_html=True,
                )
        elif msg["role"] == "user":
            st.markdown(
                f"""
            <div class="msg-row user">
                <div class="msg-content">
                    <div class="sender-label">You</div>
                    <div class="bubble user-bubble">{safe_html_text(msg["text"])}</div>
                    <div class="timestamp">{msg["timestamp"]}</div>
                </div>
            </div>""",
                unsafe_allow_html=True,
            )

    st.markdown('<div style="height:80px;"></div>', unsafe_allow_html=True)

    pending_message = None
    if (
        st.session_state.chat_history
        and st.session_state.chat_history[-1]["role"] == "assistant"
        and st.session_state.chat_history[-1]["type"] == "pending"
    ):
        pending_message = st.session_state.chat_history[-1]

    if pending_message:
        try:
            with st.spinner("Analyzing your question..."):
                question_text = pending_message.get("question", "")
                time.sleep(0.2)
                if st.session_state.rag_db is None and st.session_state.uploaded_file is not None:
                    st.session_state.rag_db = build_vector_db_from_upload(st.session_state.uploaded_file)
                    st.session_state.rag_file_hash = st.session_state.uploaded_file_hash

                if st.session_state.rag_db is not None:
                    answer = {
                        "role": "assistant",
                        "type": "text",
                        "text": query_rag(question_text, st.session_state.rag_db),
                        "timestamp": "Just now",
                    }
                else:
                    answer = dict(ai_response(question_text))
                    answer["role"] = "assistant"
                    answer["timestamp"] = "Just now"
        except Exception as exc:
            answer = {
                "role": "assistant",
                "type": "text",
                "text": f"I could not run retrieval for this question. Error: {exc}",
                "timestamp": "Just now",
            }
        st.session_state.chat_history[-1] = answer
        st.rerun()

    user_input = st.chat_input("Ask a question about this document...", key="qa_input")
    if user_input:
        st.session_state.chat_history.append(
            {
                "role": "user",
                "type": "text",
                "text": user_input,
                "timestamp": "Just now",
            }
        )
        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "type": "pending",
                "text": "Thinking through the document...",
                "question": user_input,
                "timestamp": "Sending...",
            }
        )
        st.rerun()
