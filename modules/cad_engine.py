"""CAD engine: builds the AutoCAD-compatible .DXF document with ezdxf."""
from typing import Any, Dict, List
import io

import ezdxf
from ezdxf.enums import TextEntityAlignment

PAVEMENT_H = 0.20
MEDIAN_W = 1.0

DEFAULTS = {
    "lajur": 2,
    "jalur": 1,
    "lebar_lajur": 3.5,
    "lebar_kerb": 0.25,
    "tinggi_kerb": 0.15,
    "lebar_trotoar": 1.5,
    "lebar_drainase": 0.5,
    "lebar_bahu": 1.5,
}

LAYER_COLORS = {
    "DRAINASE": 5,
    "TROTOAR": 8,
    "KERB": 7,
    "BAHU": 2,
    "LAJUR": 6,
    "MEDIAN": 3,
    "DIMENSI": 1,
    "TEKS": 4,
    "MARKA": 7,
}


def cross_section_segments(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute the ordered cross-section segments from the road parameters.

    Shared by the CAD engine (DXF geometry) and the preview engine
    (matplotlib schematic) so both always match exactly.

    Returns:
        List of segment dicts with keys: name, width, color_key, layer,
        height and, for carriageway blocks, lanes.
    """
    lajur = max(1, int(params.get("lajur", DEFAULTS["lajur"])))
    jalur = max(1, int(params.get("jalur", DEFAULTS["jalur"])))
    lebar_lajur = float(params.get("lebar_lajur", DEFAULTS["lebar_lajur"]))
    lebar_kerb = float(params.get("lebar_kerb", DEFAULTS["lebar_kerb"]))
    tinggi_kerb = float(params.get("tinggi_kerb", DEFAULTS["tinggi_kerb"]))
    lebar_trotoar = float(params.get("lebar_trotoar", DEFAULTS["lebar_trotoar"]))
    lebar_drainase = float(params.get("lebar_drainase", DEFAULTS["lebar_drainase"]))
    lebar_bahu = float(params.get("lebar_bahu", DEFAULTS["lebar_bahu"]))

    # Split the total lane count across the carriageways (jalur).
    if jalur <= 1:
        lane_groups = [lajur]
    else:
        left = lajur // 2
        lane_groups = [left, lajur - left]

    segments: List[Dict[str, Any]] = [
        {"name": "Drainase", "width": lebar_drainase, "color_key": "drainase",
         "layer": "DRAINASE", "height": PAVEMENT_H},
        {"name": "Trotoar", "width": lebar_trotoar, "color_key": "trotoar",
         "layer": "TROTOAR", "height": PAVEMENT_H},
        {"name": "Kerb", "width": lebar_kerb, "color_key": "kerb",
         "layer": "KERB", "height": PAVEMENT_H + tinggi_kerb},
        {"name": "Bahu", "width": lebar_bahu, "color_key": "bahu",
         "layer": "BAHU", "height": PAVEMENT_H},
    ]

    for i, lanes in enumerate(lane_groups):
        if i > 0:
            segments.append(
                {"name": "Median", "width": MEDIAN_W, "color_key": "median",
                 "layer": "MEDIAN", "height": PAVEMENT_H}
            )
        segments.append(
            {"name": f"Lajur ({lanes})", "width": lanes * lebar_lajur,
             "color_key": "lajur", "layer": "LAJUR", "height": PAVEMENT_H,
             "lanes": lanes}
        )

    segments += [
        {"name": "Bahu", "width": lebar_bahu, "color_key": "bahu",
         "layer": "BAHU", "height": PAVEMENT_H},
        {"name": "Kerb", "width": lebar_kerb, "color_key": "kerb",
         "layer": "KERB", "height": PAVEMENT_H + tinggi_kerb},
        {"name": "Trotoar", "width": lebar_trotoar, "color_key": "trotoar",
         "layer": "TROTOAR", "height": PAVEMENT_H},
        {"name": "Drainase", "width": lebar_drainase, "color_key": "drainase",
         "layer": "DRAINASE", "height": PAVEMENT_H},
    ]
    return segments


def generate_dxf(params: Dict[str, Any]) -> io.BytesIO:
    """Generate an AutoCAD .DXF file for the road cross-section.

    Args:
        params: dictionary of road parameters from render_sidebar().

    Returns:
        A BytesIO buffer containing the DXF data (ready for st.download_button).
    """
    project_name = params.get("project_name", "ARVI")
    surveyor_name = params.get("surveyor_name", "-")
    year = int(params.get("year", 2026))
    land_use = params.get("tata_guna_lahan", "-")
    drain_type = params.get("drainase_type", "-")

    segments = cross_section_segments(params)
    total_width = sum(seg["width"] for seg in segments)

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    for layername, color in LAYER_COLORS.items():
        doc.layers.add(layername, color=color)

    if "DASHED" not in doc.linetypes:
        try:
            doc.linetypes.add(
                "DASHED", description="DASH __ __ __", pattern=[0.25, -0.15]
            )
        except Exception:
            pass

    # --- Cross-section outlines -------------------------------------------
    bounds: List[tuple] = []
    x = 0.0
    for seg in segments:
        w, h = seg["width"], seg["height"]
        if w > 1e-3:
            msp.add_lwpolyline(
                [(x, 0.0), (x + w, 0.0), (x + w, h), (x, h)],
                close=True,
                dxfattribs={"layer": seg["layer"]},
            )
            bounds.append((x, x + w, seg))
        x += w

    # --- Lane markings: dashed lines between lanes of each carriageway ---
    for x0, x1, seg in bounds:
        if seg["layer"] != "LAJUR":
            continue
        lanes = int(seg.get("lanes", 1))
        if lanes > 1:
            lane_w = (x1 - x0) / lanes
            for k in range(1, lanes):
                msp.add_line(
                    (x0 + k * lane_w, 0.0),
                    (x0 + k * lane_w, PAVEMENT_H),
                    dxfattribs={"layer": "MARKA", "linetype": "DASHED", "color": 7},
                )

    # Solid centre line for single-carriageway roads with an even lane count.
    if int(params.get("jalur", 1)) <= 1 and int(params.get("lajur", 2)) % 2 == 0:
        lane_seg = next((b for b in bounds if b[2]["layer"] == "LAJUR"), None)
        if lane_seg is not None:
            cx = (lane_seg[0] + lane_seg[1]) / 2.0
            msp.add_line(
                (cx, 0.0), (cx, PAVEMENT_H),
                dxfattribs={"layer": "MARKA", "color": 2},
            )

    # --- Linear dimensions ----------------------------------------------
    def add_linear_dim(p1, p2, base, angle, text):
        try:
            dim = msp.add_linear_dim(
                base=base, p1=p1, p2=p2, angle=angle, text=text
            )
            dim.render()
        except Exception:
            pass

    # Per-segment widths, staggered over two rows to avoid text collisions.
    dim_rows = (-0.35, -0.55)
    for i, (x0, x1, seg) in enumerate(bounds):
        w = x1 - x0
        if w < 1e-3:
            continue
        add_linear_dim(
            (x0, 0.0), (x1, 0.0),
            ((x0 + x1) / 2.0, dim_rows[i % 2]),
            0.0, f"{w:.2f}",
        )

    # Overall section width.
    add_linear_dim(
        (0.0, -0.95), (total_width, -0.95),
        (total_width / 2.0, -1.10),
        0.0, f"Total {total_width:.2f}",
    )

    # Kerb height (vertical dimension on the first kerb).
    kerb = next((b for b in bounds if b[2]["layer"] == "KERB"), None)
    if kerb is not None:
        x0, _, seg = kerb
        top = seg["height"]
        add_linear_dim(
            (x0, PAVEMENT_H), (x0, top),
            (x0 - 0.45, (PAVEMENT_H + top) / 2.0),
            90.0, f"{top - PAVEMENT_H:.2f}",
        )

    # --- Title block text ----------------------------------------------
    msp.add_text(
        f"ARVI - {project_name}",
        dxfattribs={"height": 0.34, "layer": "TEKS"},
    ).set_placement(
        (total_width / 2.0, PAVEMENT_H + 0.85),
        align=TextEntityAlignment.MIDDLE_CENTER,
    )
    msp.add_text(
        f"Penampang Melintang | Surveyor: {surveyor_name} | Tahun: {year} | "
        f"Tata Guna Lahan: {land_use} | Drainase: {drain_type}",
        dxfattribs={"height": 0.16, "layer": "TEKS"},
    ).set_placement(
        (total_width / 2.0, PAVEMENT_H + 0.48),
        align=TextEntityAlignment.MIDDLE_CENTER,
    )

    # ezdxf writes str to the stream, so wrap the binary buffer in a text IO.
    buf = io.BytesIO()
    text_buf = io.TextIOWrapper(buf, encoding="utf-8", newline="\n")
    doc.write(text_buf)
    text_buf.flush()
    text_buf.detach()
    buf.seek(0)
    return buf
