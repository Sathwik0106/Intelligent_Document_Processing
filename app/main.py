import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")
os.environ.setdefault("STREAMLIT_SERVER_MAX_UPLOAD_SIZE", os.getenv("MAX_UPLOAD_SIZE_MB", "20"))

# Reduce non-fatal advisory warning spam from transformers during startup.
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import streamlit as st

# Suppress repeated non-fatal FutureWarning lines like:
# "Accessing `__path__` from `.models...`. Returning `__path__` instead."
warnings.filterwarnings("ignore", message=r"Accessing `__path__` from .*", category=FutureWarning)

from app.ui.components import init_session_state, render_global_css, render_navbar_and_tabs, render_runtime_alerts
from app.ui.qa import render_qa_tab
from app.ui.structured import render_structured_tab
from app.ui.summary import render_summary_tab

def run_app():
    st.set_page_config(
        page_title="Intelligent Document Processing",
        page_icon=":page_facing_up:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    init_session_state()
    render_global_css()
    render_runtime_alerts()
    render_navbar_and_tabs()

    if st.session_state.active_tab == "summary":
        render_summary_tab()
    elif st.session_state.active_tab == "structured":
        render_structured_tab()
    elif st.session_state.active_tab == "qa":
        render_qa_tab()
