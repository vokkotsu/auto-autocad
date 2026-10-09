"""ARVI (Automatic Road Visualization) — main Streamlit orchestration (mobile-first)."""
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
from modules.ui_inputs import render_inputs

MARKER_TYPES = ["Rambu", "PJU", "APILL", "Halte", "Marka"]


def main() -> None:
    st.set_page_config(
        page_title="ARVI - Automatic Road Visualization",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Mobile-first: use tabs instead of sidebar
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Input Data",
        "🛣️ Potongan Melintang",
        "🗺️ Tampak Atas",
        "💾 Export",
    ])

    # ── Tab 1: Input Data ─────────────────────────────────────────
    with tab1:
        st.title("ARVI — Automatic Road Visualization")
        st.caption(
            "Aplikasi MVP untuk inventaris jalan: pratinjau penampang melintang, "
            "tampak atas, dan ekspor AutoCAD .DXF, PDF, PNG."
        )
        params = render_inputs()

    # ── Tab 2: Cross-Section Preview ──────────────────────────────
    with tab2:
        st.header("🛣️ Pratinjau Penampang Melintang")
        fig = draw_cross_section(params)
        # width="stretch" makes it responsive on mobile (Streamlit 1.65+)
        st.pyplot(fig, width="stretch")
        plt.close(fig)

        # Quick summary metrics
        total_width = sum([
            params["lebar_drainase"], params["lebar_trotoar"], params["lebar_kerb"],
            params["lebar_bahu"], params["lajur"] * params["lebar_lajur"],
            (1.0 if params["jalur"] > 1 else 0),
            params["lebar_bahu"], params["lebar_kerb"],
            params["lebar_trotoar"], params["lebar_drainase"],
        ])
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Lebar", f"{total_width:.2f} m")
        col2.metric("Jumlah Lajur", f"{params['lajur']}")
        col3.metric("Jalur", f"{params['jalur']}")

    # ── Tab 3: Plan View (Upload + Marker Interaction) ───────────
    with tab3:
        st.header("🗺️ Pratinjau Tampak Atas (Plan View)")

        uploaded_image = st.file_uploader(
            "Unggah screenshot Google Earth (basis peta)",
            type=["png", "jpg", "jpeg"],
            help="Unggah gambar peta untuk menempatkan marker",
        )

        if "markers" not in st.session_state:
            st.session_state.markers = []
        if "last_click" not in st.session_state:
            st.session_state.last_click = None

        plan_image = draw_plan_view(uploaded_image, st.session_state.markers)

        # Marker type selector (full width on mobile)
        marker_type = st.radio(
            "Pilih Jenis Marker",
            MARKER_TYPES,
            index=0,
            horizontal=True,
        )

        if plan_image is not None:
            from streamlit_image_coordinates import streamlit_image_coordinates

            # use_column_width=True for streamlit_image_coordinates (not use_container_width)
            coords = streamlit_image_coordinates(
                plan_image, key="plan_map", use_column_width=True
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

            # Marker legend and controls
            st.markdown("**Legend Marker**")
            st.markdown(marker_legend_html(st.session_state.markers), unsafe_allow_html=True)

            if st.session_state.markers:
                st.caption(f"Total marker: {len(st.session_state.markers)}")
                if st.button("🗑️ Hapus Semua Marker", width="stretch"):
                    st.session_state.markers.clear()
                    st.session_state.last_click = None
                    st.rerun()

                st.dataframe(
                    st.session_state.markers,
                    width="stretch",
                    hide_index=True,
                    column_config={"type": "Marker Type"},
                )
        else:
            st.info("👆 Unggah screenshot Google Earth untuk memulai penempatan marker")

    # ── Tab 4: Export Options ────────────────────────────────────
    with tab4:
        st.header("💾 Ekspor Hasil")

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

        st.caption(f"Nama file: **{safe_name}**")

        # Full-width buttons for easy tapping on mobile
        st.download_button(
            "📄 Download Laporan (PDF)",
            data=pdf_buffer.getvalue(),
            file_name=f"{safe_name}_Laporan.pdf",
            mime="application/pdf",
            width="stretch",
        )
        st.download_button(
            "🖼️ Download Layout (PNG)",
            data=png_buffer.getvalue(),
            file_name=f"{safe_name}_Layout.png",
            mime="image/png",
            width="stretch",
        )
        st.download_button(
            "📐 Download CAD (.DXF)",
            data=dxf_buffer.getvalue(),
            file_name=f"{safe_name}.dxf",
            mime="image/vnd.autocad.dxf",
            width="stretch",
            help="File AutoCAD-compatible berisi penampang melintang dengan dimensi.",
        )

        st.markdown("---")
        st.caption("ARVI MVP — Mobile-First Responsive UI")


def _render_report_buffers(fig: plt.Figure) -> tuple:
    """Render the report figure to in-memory PDF and PNG buffers."""
    pdf_buffer = io.BytesIO()
    png_buffer = io.BytesIO()
    fig.savefig(pdf_buffer, format="pdf", bbox_inches="tight")
    fig.savefig(png_buffer, format="png", dpi=180, bbox_inches="tight")
    pdf_buffer.seek(0)
    png_buffer.seek(0)
    return pdf_buffer, png_buffer


if __name__ == "__main__":
    main()