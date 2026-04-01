import json

import pandas as pd
import streamlit as st


@st.dialog("Structured JSON", width="large")
def _open_structured_json_modal(data: dict):
    st.code(json.dumps(data, indent=2), language="json")


def render_structured_tab():
    structured_data = st.session_state.get("structured_json") or {}
    tables_data = structured_data.get("tables", {}) if isinstance(structured_data, dict) else {}
    json_payload = json.dumps(structured_data, indent=2).encode("utf-8")

    st.markdown('<div class="structured-header-card">', unsafe_allow_html=True)
    header_left, header_right = st.columns([3.4, 1.6], gap="large", vertical_alignment="bottom")
    with header_left:
        st.markdown(
            """
            <div class="card-header" style="margin-bottom:10px;">
                <div class="card-icon">DAT</div>
                <span class="card-title">Structured Extraction</span>
            </div>
            <div class="structured-header-copy">
                <div class="structured-header-title">Review extracted entities and export clean JSON.</div>
                <div class="structured-header-description">
                    Tables are formatted for fast scanning on desktop and remain readable on narrower screens.
                    Use the actions below to inspect the raw payload or download it for downstream workflows.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_right:
        st.markdown('<div class="structured-actions-shell"><div class="structured-button-group">', unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2, gap="small")
        with btn_col1:
            if st.button("View JSON", key="view_json_btn_top", width="stretch"):
                _open_structured_json_modal(structured_data)
        with btn_col2:
            st.download_button(
                label="Export JSON",
                data=json_payload,
                file_name="structured_output.json",
                mime="application/json",
                key="export_json_btn_top",
                on_click="ignore",
                disabled=not bool(structured_data),
                width="stretch",
            )
        st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    def _safe_rows_for_display(rows):
        serial_keys = {
            "id",
            "sr_no",
            "sr no",
            "serial_no",
            "serial no",
            "serial number",
            "s no",
            "s_no",
            "sno",
            "sl no",
            "sl_no",
            "slno",
        }
        safe_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            safe_row = {}
            for key, value in row.items():
                normalized_key = str(key).strip().lower().replace("-", " ").replace("_", " ")
                if normalized_key in serial_keys:
                    continue
                if value is None:
                    safe_row[key] = ""
                elif isinstance(value, str) and value.strip().lower() in {"n/a", "na", "none", "null", "-"}:
                    safe_row[key] = ""
                else:
                    safe_row[key] = str(value)
            safe_rows.append(safe_row)
        return safe_rows

    def _pretty_label(value: str) -> str:
        return str(value).replace("_", " ").strip().title()

    def _render_structured_table(rows):
        st.dataframe(pd.DataFrame(_safe_rows_for_display(rows)), width="stretch", hide_index=True)

    primary_entity_rows = tables_data.get("primary_entity", []) if isinstance(tables_data, dict) else []
    h1, h2 = st.columns([9, 2])
    with h1:
        st.markdown(
            '<h2 style="font-size:18px;font-weight:800;color:#111827;margin-bottom:4px;">'
            "Primary Entity Details</h2>",
            unsafe_allow_html=True,
        )
    with h2:
        st.markdown(
            '<div style="display:flex;justify-content:flex-end;padding-top:2px;">'
            '<div class="verified-badge">Verified</div></div>',
            unsafe_allow_html=True,
        )

    if isinstance(primary_entity_rows, list) and primary_entity_rows:
        normalized_primary_rows = [row for row in primary_entity_rows if isinstance(row, dict)]
        if normalized_primary_rows:
            _render_structured_table(normalized_primary_rows)
        else:
            st.write("No rows found")
    else:
        st.markdown(
            '<p style="font-size:12px;color:#9ca3af;margin-bottom:16px;">No primary entity table found yet.</p>',
            unsafe_allow_html=True,
        )

    other_tables = []
    if isinstance(tables_data, dict):
        other_tables = [(k, v) for k, v in tables_data.items() if k != "primary_entity"]

    if other_tables:
        for table_name, rows in other_tables:
            st.markdown(
                f'<h3 style="font-size:16px;font-weight:800;color:#111827;margin-bottom:4px;">{_pretty_label(table_name)}</h3>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p style="font-size:12px;color:#9ca3af;margin-bottom:16px;">Extracted data rows from the primary document table.</p>',
                unsafe_allow_html=True,
            )
            if isinstance(rows, list) and rows:
                _render_structured_table(rows)
            else:
                st.write("No rows found")
    elif not primary_entity_rows:
        st.markdown(
            '<p style="font-size:12px;color:#9ca3af;margin-bottom:16px;">Upload and process a document to view extracted tables.</p>',
            unsafe_allow_html=True,
        )
