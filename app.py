"""ARVI (Automatic Road Visualization) — main Streamlit orchestration."""
import io
import os
import re
import sys

import matplotlib.pyplot as plt
import streamlit as st

# Ensure the `modules` package is importable regardless of the working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.cad_engine import generate_dxf
from modules.preview_engine import (
    build_report_figure,
    draw_cross_section,
    draw_plan_view,
    marker_legend_html,
)
from modules.ui_inputs import render_sidebar

MARKER_TYPES = ["Rambu", "PJU", "APILL", "Halte", "Marka"]


def main() -> None:
    st.set_page_config(page_title="ARVI - Automatic Road Visualization", layout="wide")
    st.title("ARVI — Automatic Road Visualization")
    st.markdown(
        "Aplikasi MVP yang mengambil parameter inventaris jalan dan screenshot "
        "Google Earth untuk menghasilkan pratinjau penampang melintang, "
        "tampak atas (plan view), serta ekspor file AutoCAD .DXF, PDF, dan PNG."
    )

    # ── 1. Sidebar inputs ─────────────────────────────────────
    params = render_sidebar()

    # ── 2. Cross-section preview ──────────────────────────────
    st.header("1. Pratinjau Penampang Melintang (Cross-Section)")
    fig = draw_cross_section(params)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── 3. Plan view (upload + marker interaction) ────────────
    st.header("2. Pratinjau Tampak Atas (Plan View)")
    uploaded_image = st.sidebar.file_uploader(
        "Unggah screenshot Google Earth (basis peta)", type=["png", "jpg", "jpeg"]
    )

    if "markers" not in st.session_state:
        st.session_state.markers = []
    if "last_click" not in st.session_state:
        st.session_state.last_click = None

    plan_image = draw_plan_view(uploaded_image, st.session_state.markers)

    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.markdown("**Jenis Marker**")
        marker_type = st.radio("Pilih marker", MARKER_TYPES, index=0, horizontal=True)
        st.markdown(
            marker_legend_html(st.session_state.markers), unsafe_allow_html=True
        )
        if st.session_state.markers:
            st.caption(f"Total marker: {len(st.session_state.markers)}")
            if st.button("Hapus Semua Marker", use_container_width=True):
                st.session_state.markers.clear()
                st.session_state.last_click = None
                st.rerun()

    with col_right:
        if plan_image is not None:
            from streamlit_image_coordinates import streamlit_image_coordinates

            coords = streamlit_image_coordinates(
                plan_image, key="plan_map", use_container_width=True
            )
            if (
                coords is not None
                and "x" in coords
                and "y" in coords
                and coords != st.session_state.last_click
            ):
                st.session_state.last_click = dict(coords)
                st.session_state.markers.append(
                    {
                        "x": float(coords["x"]),
                        "y": float(coords["y"]),
                        "type": marker_type,
                    }
                )
                st.rerun()
        else:
            st.caption("Unggah screenshot Google Earth pada sidebar untuk memulai.")

    if st.session_state.markers:
        st.dataframe(
            st.session_state.markers,
            use_container_width=True,
            hide_index=True,
            column_config={"type": "Marker Type"},
        )

    # ── 4. Export options ─────────────────────────────────────
    st.header("3. Export Options")

    dxf_buffer = generate_dxf(params)
    report_fig = build_report_figure(params, plan_image)
    pdf_buffer, png_buffer = _render_report_buffers(report_fig)
    plt.close(report_fig)

    safe_name = (
        re.sub(r"[^A-Za-z0-9 _-]", "", params["project_name"])
        .strip()
        .replace(" ", "_")
        or "ARVI"
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Download Laporan (PDF)",
            data=pdf_buffer.getvalue(),
            file_name=f"{safe_name}_Laporan.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Download Layout (PNG)",
            data=png_buffer.getvalue(),
            file_name=f"{safe_name}_Layout.png",
            mime="image/png",
            use_container_width=True,
        )
    with c3:
        st.download_button(
            "Download CAD (.DXF)",
            data=dxf_buffer.getvalue(),
            file_name=f"{safe_name}.dxf",
            mime="image/vnd.autocad.dxf",
            use_container_width=True,
            help="File AutoCAD-compatible berisi penampang melintang dengan dimensi.",
        )

    st.sidebar.markdown("---")
    st.sidebar.caption("ARVI MVP — Modular Architecture")


def _render_report_buffers(fig: plt.Figure) -> tuple:
    """Render the report figure to in-memory PDF and PNG buffers."""
    pdf_buffer = io.BytesIO()
    png_buffer = io.BytesIO()
    fig.savefig(pdf_buffer, format="pdf")
    fig.savefig(png_buffer, format="png", dpi=180)
    pdf_buffer.seek(0)
    png_buffer.seek(0)
    return pdf_buffer, png_buffer


if __name__ == "__main__":
    main()
