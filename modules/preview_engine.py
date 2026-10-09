"""Web preview engine: matplotlib cross-section schematic and plan-view overlays."""
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw

from .cad_engine import PAVEMENT_H, cross_section_segments

SEGMENT_COLORS = {
    "drainase": "#a6cee3",
    "trotoar": "#c9c9c9",
    "kerb": "#525252",
    "bahu": "#fee08b",
    "lajur": "#4d4d4d",
    "median": "#a1d99b",
}

DARK_SEGMENTS = {"kerb", "lajur"}

MARKER_COLORS = {
    "Rambu": "#1f78b4",
    "PJU": "#ff7f00",
    "APILL": "#33a02c",
    "Halte": "#6a3d9a",
    "Marka": "#e31a1c",
}


def _draw_segments(ax, segments: List[Dict[str, Any]]) -> float:
    """Draw cross-section segment rectangles and lane markings on `ax`.

    Returns:
        The total cross-section width in metres.
    """
    total_width = 0.0
    lane_bounds: List[tuple] = []

    for seg in segments:
        x, w, h = total_width, seg["width"], seg["height"]
        if w > 1e-3:
            ax.add_patch(
                Rectangle(
                    (x, 0.0), w, h,
                    facecolor=SEGMENT_COLORS[seg["color_key"]],
                    edgecolor="black",
                    linewidth=0.8,
                )
            )
            if w >= 1.2:
                label_color = (
                    "white" if seg["color_key"] in DARK_SEGMENTS else "black"
                )
                ax.text(
                    x + w / 2.0, h / 2.0, seg["name"],
                    ha="center", va="center", fontsize=7, color=label_color,
                )
        if seg["layer"] == "LAJUR":
            lane_bounds.append((x, x + w, int(seg.get("lanes", 1))))
        total_width += w

    # Dashed lane-divider markings inside each carriageway block.
    for x0, x1, lanes in lane_bounds:
        if lanes > 1:
            lane_w = (x1 - x0) / lanes
            for k in range(1, lanes):
                ax.plot(
                    [x0 + k * lane_w] * 2, [0.0, PAVEMENT_H],
                    color="white", linewidth=0.7, linestyle=(0, (4, 3)),
                )
    return total_width


def draw_cross_section(params: Dict[str, Any]) -> plt.Figure:
    """Draw a schematic road cross-section based on the parameter dictionary.

    Args:
        params: dictionary of road parameters from render_sidebar().

    Returns:
        The matplotlib figure with the cross-section schematic.
    """
    segments = cross_section_segments(params)

    fig, ax = plt.subplots(figsize=(10, 3.6))
    total_width = _draw_segments(ax, segments)
    max_height = max(seg["height"] for seg in segments)

    # Width annotations below the section.
    x = 0.0
    for seg in segments:
        if seg["width"] > 0.4:
            ax.text(
                x + seg["width"] / 2.0, -max_height * 0.18,
                f"{seg['width']:.2f}", ha="center", va="top",
                fontsize=7, color="#444444",
            )
        x += seg["width"]

    ax.axhline(0.0, color="#666666", linewidth=0.8, zorder=0)
    ax.set_xlim(-total_width * 0.03, total_width * 1.03)
    ax.set_ylim(-max_height * 0.65, max_height * 1.9)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        f"Penampang Melintang — {params.get('project_name', '')} "
        f"(lebar total {total_width:.2f} m)",
        fontsize=11,
    )
    fig.tight_layout(pad=1.5)
    return fig


def draw_plan_view(
    image_file, markers_state: List[Dict[str, Any]]
) -> Optional[Image.Image]:
    """Load the uploaded Google Earth screenshot and overlay marker dots.

    Args:
        image_file: uploaded file-like object (PNG/JPG) or None.
        markers_state: list of marker dicts with keys x, y and type.

    Returns:
        The processed PIL image with markers drawn on top, or None.
    """
    if image_file is None:
        return None
    try:
        image = Image.open(image_file).convert("RGB")
    except Exception:
        return None

    if markers_state:
        draw = ImageDraw.Draw(image)
        for marker in markers_state:
            cx = int(round(float(marker["x"])))
            cy = int(round(float(marker["y"])))
            radius = 9
            color = MARKER_COLORS.get(marker.get("type", ""), "#e31a1c")
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=color,
                outline="white",
                width=2,
            )
    return image


def marker_legend_html(markers: List[Dict[str, Any]]) -> str:
    """Build an HTML legend summarising the placed markers by type."""
    counts: Dict[str, int] = {}
    for marker in markers:
        key = str(marker.get("type", "?"))
        counts[key] = counts.get(key, 0) + 1

    if not counts:
        return "<div><i>Belum ada marker.</i></div>"

    return "".join(
        f'<div><span style="color:{MARKER_COLORS.get(t, "#e31a1c")}">'
        f"&#9679;</span> {t}: {c}</div>"
        for t, c in counts.items()
    )


def build_report_figure(
    params: Dict[str, Any], plan_image: Optional[Image.Image]
) -> plt.Figure:
    """Compose a one-page report figure: header, cross-section and plan view."""
    fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
    fig.patch.set_facecolor("white")

    fig.text(
        0.5, 0.955, f"ARVI — {params.get('project_name', '')}",
        ha="center", va="center", fontsize=16, weight="bold",
    )
    fig.text(
        0.5, 0.915,
        f"Surveyor: {params.get('surveyor_name', '-')} | "
        f"Tahun: {params.get('year', '-')} | "
        f"Tata Guna Lahan: {params.get('tata_guna_lahan', '-')}",
        ha="center", va="center", fontsize=9,
    )
    fig.text(
        0.5, 0.885,
        f"{params.get('lajur', 2)} lajur / {params.get('jalur', 1)} jalur | "
        f"Lebar lajur: {params.get('lebar_lajur', 3.5)} m | "
        f"Drainase: {params.get('drainase_type', '-')}",
        ha="center", va="center", fontsize=8,
    )

    ax_cs = fig.add_axes([0.05, 0.40, 0.90, 0.42])
    segments = cross_section_segments(params)
    total_width = _draw_segments(ax_cs, segments)
    max_height = max(seg["height"] for seg in segments)
    ax_cs.set_xlim(-total_width * 0.03, total_width * 1.03)
    ax_cs.set_ylim(-max_height * 0.4, max_height * 1.4)
    ax_cs.set_aspect("equal")
    ax_cs.axis("off")
    ax_cs.set_title("Penampang Melintang", fontsize=10)

    ax_plan = fig.add_axes([0.10, 0.05, 0.80, 0.28])
    if plan_image is not None:
        ax_plan.imshow(plan_image)
    else:
        ax_plan.text(
            0.5, 0.5, "Belum ada peta dasar",
            ha="center", va="center", fontsize=10, color="#888888",
        )
    ax_plan.axis("off")
    ax_plan.set_title("Tampak Atas (Plan View)", fontsize=10)

    fig.text(
        0.5, 0.015, "Dibuat menggunakan ARVI — Ekspor AutoCAD .DXF & PDF",
        ha="center", va="center", fontsize=7, color="#999999",
    )
    return fig
