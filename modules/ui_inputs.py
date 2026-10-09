"""UI inputs module: collects road inventory parameters via the Streamlit sidebar."""
from typing import Any, Dict

import streamlit as st


def render_sidebar() -> Dict[str, Any]:
    """Render the Streamlit sidebar for user inputs and return the parameters dict.

    Returns:
        Dict containing all user inputs organized by category.
    """
    st.sidebar.title("ARVI - Input Parameters")

    # --- Project Info ---
    st.sidebar.subheader("Project Info")
    project_name = st.sidebar.text_input("Project Name", "Jalan Contoh")
    surveyor_name = st.sidebar.text_input("Surveyor Name", "Nama Surveyor")
    year = st.sidebar.number_input("Year", 1900, 2100, 2026, step=1)

    # --- Cross-Section Parameters ---
    st.sidebar.subheader("Cross-Section Parameters (Penampang Melintang)")
    lajur_jalur = st.sidebar.text_input(
        "Jumlah Lajur & Jalur (format: lajur/jalur, e.g., 2/1 atau 4/2)", "2/1"
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

    lebar_lajur = st.sidebar.number_input("Lebar Lajur (m)", 0.5, 10.0, 3.5, 0.1)
    lebar_kerb = st.sidebar.number_input("Lebar Kerb (m)", 0.0, 2.0, 0.25, 0.05)
    tinggi_kerb = st.sidebar.number_input("Tinggi Kerb (m)", 0.0, 1.0, 0.15, 0.05)
    lebar_trotoar = st.sidebar.number_input("Lebar Trotoar (m)", 0.0, 10.0, 1.5, 0.1)
    drainase_type = st.sidebar.selectbox(
        "Tipe Drainase", ["Open Channel", "Box Culvert", "Gorong-Gorong"]
    )
    lebar_drainase = st.sidebar.number_input("Lebar Drainase (m)", 0.0, 10.0, 0.5, 0.1)
    lebar_bahu = st.sidebar.number_input("Lebar Bahu Jalan (m)", 0.0, 10.0, 1.5, 0.1)
    tata_guna_lahan = st.sidebar.selectbox(
        "Tata Guna Lahan Sekitar (Land Use)", ["Pemukiman", "Komersial", "Kosong"]
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
