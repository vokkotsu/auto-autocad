"""UI inputs module: collects road inventory parameters via Streamlit (mobile-first)."""
from typing import Any, Dict

import streamlit as st


def render_inputs() -> Dict[str, Any]:
    """Render input fields in the main content area with expanders for mobile.

    Returns:
        Dict containing all user inputs organized by category.
    """
    st.subheader("📝 Input Data Proyek")

    # --- Project Info ---
    with st.expander("📋 Info Proyek", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Nama Proyek", "Jalan Contoh")
        with col2:
            surveyor_name = st.text_input("Nama Surveyor", "Nama Surveyor")
        year = st.number_input("Tahun", 1900, 2100, 2026, step=1)

    # --- Cross-Section Parameters ---
    with st.expander("🛣️ Dimensi Jalan (Penampang Melintang)", expanded=True):
        lajur_jalur = st.text_input(
            "Lajur / Jalur (format: lajur/jalur, cth: 2/1 atau 4/2)", "2/1"
        )
        # Parse "X/Y" into lajur (lanes) and jalur (carriageways).
        parts = [p.strip() for p in lajur_jalur.split("/")]
        try:
            lajur = int(parts[0])
            jalur = int(parts[1]) if len(parts) > 1 else 1
        except (ValueError, IndexError):
            lajur, jalur = 2, 1
        lajur = max(1, lajur)
        jalur = max(1, jalur)

        col1, col2 = st.columns(2)
        with col1:
            lebar_lajur = st.number_input("Lebar Lajur (m)", 0.5, 10.0, 3.5, 0.1)
            lebar_kerb = st.number_input("Lebar Kerb (m)", 0.0, 2.0, 0.25, 0.05)
            tinggi_kerb = st.number_input("Tinggi Kerb (m)", 0.0, 1.0, 0.15, 0.05)
            lebar_trotoar = st.number_input("Lebar Trotoar (m)", 0.0, 10.0, 1.5, 0.1)
        with col2:
            drainase_type = st.selectbox(
                "Tipe Drainase", ["Open Channel", "Box Culvert", "Gorong-Gorong"]
            )
            lebar_drainase = st.number_input("Lebar Drainase (m)", 0.0, 10.0, 0.5, 0.1)
            lebar_bahu = st.number_input("Lebar Bahu Jalan (m)", 0.0, 10.0, 1.5, 0.1)
            tata_guna_lahan = st.selectbox(
                "Tata Guna Lahan", ["Pemukiman", "Komersial", "Kosong"]
            )

    return {
        "project_name": project_name.strip() or "Tanpa Nama",
        "surveyor_name": surveyor_name.strip() or "-",
        "year": int(year),
        "lajur": lajur,
        "jalur": jalur,
        "lebar_lajur": float(lebar_lajur),
        "lebar_kerb": float(lebar_kerb),
        "tinggi_kerb": float(tinggi_kerb),
        "lebar_trotoar": float(lebar_trotoar),
        "drainase_type": drainase_type,
        "lebar_drainase": float(lebar_drainase),
        "lebar_bahu": float(lebar_bahu),
        "tata_guna_lahan": tata_guna_lahan,
    }


# Backward compatibility alias
render_sidebar = render_inputs