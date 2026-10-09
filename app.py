import io
import re
from collections import Counter

import streamlit as st
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw, ImageFont
import ezdxf
from ezdxf.enums import TextEntityAlignment
from streamlit_image_coordinates import streamlit_image_coordinates

PAVEMENT_H = 0.20
MEDIAN_W = 1.00

MARKER_TYPES = ["Rambu", "PJU", "APILL", "Halte", "Marka"]
MARKER_COLORS = {
    "Rambu": "#d62728",
    "PJU": "#f2b705",
    "APILL": "#1f77b4",
    "Halte": "#2ca02c",
    "Marka": "#9467bd",
}
MARKER_COLORS_RGB = {
    "Rambu": (214, 39, 40),
    "PJU": (242, 183, 5),
    "APILL": (31, 119, 180),
    "Halte": (44, 160, 44),
    "Marka": (148, 103, 189),
}

SEGMENT_COLORS = {
    "Drainase": "#a6cee3",
    "Trotoar": "#c9c9c9",
    "Kerb": "#525252",
    "Bahu": "#fee08b",
    "Lajur": "#4d4d4d",
    "Median": "#a1d99b",
}

DXF_LAYER_MAP = {
    "Drainase": ("DRAINASE", 5),
    "Trotoar": ("TROTOAR", 8),
    "Kerb": ("KERB", 7),
    "Bahu": ("BAHU", 2),
    "Lajur": ("LAJUR", 6),
    "Median": ("MEDIAN", 3),
}


def parse_lajur_jalur(text):
    m = re.search(r"(\d+)\s*/\s*(\d+)", str(text))
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)", str(text))
    if m:
        return int(m.group(1)), 1
    return 2, 1


def read_sidebar_inputs():
    st.sidebar.title("ARVI Input")
    st.sidebar.markdown("### Identitas Proyek")
    project_name = st.sidebar.text_input("Nama Proyek", "Jalan Raya Contoh")
    surveyor_name = st.sidebar.text_input("Nama Surveyor", "Nama Surveyor")
    year = st.sidebar.number_input("Tahun", 1900, 2100, 2026, step=1)

    st.sidebar.markdown("### Parameter Penampang Melintang")
    jumlah_lajur_jalur = st.sidebar.text_input(
        "Jumlah Lajur & Jalur (contoh: 2/1, 4/2)", "2/1"
    )
    lajur, jalur = parse_lajur_jalur(jumlah_lajur_jalur)
    lebar_lajur = st.sidebar.number_input(
        "Lebar Lajur (m)", 0.0, 20.0, 3.5, 0.1, format="%.2f"
    )
    lebar_kerb = st.sidebar.number_input(
        "Lebar Kerb (m)", 0.0, 5.0, 0.25, 0.05, format="%.2f"
    )
    tinggi_kerb = st.sidebar.number_input(
        "Tinggi Kerb (m)", 0.0, 1.0, 0.15, 0.05, format="%.2f"
    )
    lebar_trotoar = st.sidebar.number_input(
        "Lebar Trotoar (m)", 0.0, 10.0, 1.50, 0.10, format="%.2f"
    )
    lebar_drainase = st.sidebar.number_input(
        "Lebar Drainase (m)", 0.0, 10.0, 0.50, 0.10, format="%.2f"
    )
    lebar_bahu = st.sidebar.number_input(
        "Lebar Bahu Jalan (m)", 0.0, 10.0, 1.50, 0.10, format="%.2f"
    )
    tata_guna_lahan = st.sidebar.selectbox(
        "Tata Guna Lahan Sekitar", ["Pemukiman", "Komersial", "Kosong"]
    )

    st.sidebar.markdown("### Parameter Tampak Atas")
    uploaded_map = st.sidebar.file_uploader(
        "Unggah peta dasar (screenshot Google Earth)",
        type=["png", "jpg", "jpeg"],
    )

    params = {
        "project_name": project_name.strip() or "Tanpa Nama",
        "surveyor_name": surveyor_name.strip() or "-",
        "year": int(year),
        "jumlah_lajur_jalur_raw": str(jumlah_lajur_jalur),
        "lajur": int(lajur),
        "jalur": int(jalur),
        "lebar_lajur": float(lebar_lajur),
        "lebar_kerb": float(lebar_kerb),
        "tinggi_kerb": float(tinggi_kerb),
        "lebar_trotoar": float(lebar_trotoar),
        "lebar_drainase": float(lebar_drainase),
        "lebar_bahu": float(lebar_bahu),
        "tata_guna_lahan": tata_guna_lahan,
    }
    return params, uploaded_map


def compute_layout(params):
    w_drain = float(params["lebar_drainase"])
    w_trot = float(params["lebar_trotoar"])
    w_kerb = float(params["lebar_kerb"])
    w_bahu = float(params["lebar_bahu"])
    w_lajur = float(params["lebar_lajur"])
    lajur = int(params["lajur"])
    jalur = int(params["jalur"])
    t_kerb = float(params["tinggi_kerb"])

    if jalur <= 1:
        groups = [max(1, lajur)]
        median_w = 0.0
    else:
        left = max(1, lajur // 2)
        groups = [left, max(1, lajur - left)]
        median_w = MEDIAN_W

    segs = []
    lane_groups = []
    x = 0.0

    def seg(name, w, top, color):
        nonlocal x
        s = {"name": name, "x0": x, "x1": x + w, "top": top, "color": color}
        segs.append(s)
        x += w
        return s

    seg("Drainase", w_drain, 0.10, SEGMENT_COLORS["Drainase"])
    seg("Trotoar", w_trot, PAVEMENT_H, SEGMENT_COLORS["Trotoar"])
    kerb_l = seg("Kerb", w_kerb, PAVEMENT_H + t_kerb, SEGMENT_COLORS["Kerb"])
    seg("Bahu", w_bahu, PAVEMENT_H, SEGMENT_COLORS["Bahu"])

    for gi, n in enumerate(groups):
        lg = seg("Lajur", n * w_lajur, PAVEMENT_H, SEGMENT_COLORS["Lajur"])
        lane_groups.append({"x0": lg["x0"], "x1": lg["x1"], "n": n})
        if gi == 0 and median_w > 0:
            seg("Median", median_w, PAVEMENT_H, SEGMENT_COLORS["Median"])

    seg("Bahu", w_bahu, PAVEMENT_H, SEGMENT_COLORS["Bahu"])
    seg("Kerb", w_kerb, PAVEMENT_H + t_kerb, SEGMENT_COLORS["Kerb"])
    seg("Trotoar", w_trot, PAVEMENT_H, SEGMENT_COLORS["Trotoar"])
    seg("Drainase", w_drain, 0.10, SEGMENT_COLORS["Drainase"])

    max_top = max(s["top"] for s in segs)
    return {
        "segments": segs,
        "lane_groups": lane_groups,
        "kerb_left": kerb_l,
        "total_width": x,
        "max_top": max_top,
        "median_w": median_w,
        "groups": groups,
        "jalur": jalur,
        "lajur": lajur,
    }


def pavement_width(layout):
    total = 0.0
    for s in layout["segments"]:
        if s["name"] in ("Lajur", "Bahu", "Median"):
            total += s["x1"] - s["x0"]
    return total


def dimension_specs(layout):
    specs = []
    rows = [-0.30, -0.56]
    i = 0
    for s in layout["segments"]:
        w = s["x1"] - s["x0"]
        if w <= 1e-9:
            continue
        specs.append((s["x0"], s["x1"], f"{w:.2f}", rows[i % 2], w < 1.2))
        i += 1
    overall_y = min(sp[3] for sp in specs) - 0.34
    specs.append(
        (0.0, layout["total_width"], f"TOTAL {layout['total_width']:.2f} m", overall_y, False)
    )
    return specs


def draw_dashed_vline(ax, x, y0, y1, color="white", lw=0.9, dash=0.30, gap=0.20):
    y = y0
    while y < y1:
        ye = min(y + dash, y1)
        ax.plot(
            [x, x], [y, ye], color=color, lw=lw, solid_capstyle="butt", zorder=4
        )
        y = ye + gap


def draw_width_dim(ax, x0, x1, y, label, rotated):
    ax.annotate(
        "",
        xy=(x0, y),
        xytext=(x1, y),
        arrowprops=dict(arrowstyle="<->", color="black", lw=0.7, mutation_scale=7),
        zorder=3,
    )
    ax.plot([x0, x0], [0.0, y - 0.04], color="#999999", lw=0.5, linestyle=":", zorder=1)
    ax.plot([x1, x1], [0.0, y - 0.04], color="#999999", lw=0.5, linestyle=":", zorder=1)
    if rotated:
        ax.text(
            (x0 + x1) / 2.0, y + 0.03, label, ha="center", va="bottom", fontsize=6.5, rotation=90
        )
    else:
        ax.text((x0 + x1) / 2.0, y + 0.03, label, ha="center", va="bottom", fontsize=6.5)


def draw_kerb_height_dim(ax, kerb_seg, t_kerb, xd):
    y0 = PAVEMENT_H
    y1 = kerb_seg["top"]
    ax.annotate(
        "",
        xy=(xd, y0),
        xytext=(xd, y1),
        arrowprops=dict(arrowstyle="<->", color="black", lw=0.7, mutation_scale=7),
        zorder=3,
    )
    ax.plot([kerb_seg["x0"], xd - 0.05], [y0, y0], color="#999999", lw=0.5, linestyle=":", zorder=1)
    ax.plot([kerb_seg["x0"], xd - 0.05], [y1, y1], color="#999999", lw=0.5, linestyle=":", zorder=1)
    ax.text(
        xd - 0.08,
        (y0 + y1) / 2.0,
        f"t={t_kerb:.2f} m",
        rotation=90,
        ha="center",
        va="bottom",
        fontsize=6.5,
    )


def draw_cross_section(ax, params, layout):
    for s in layout["segments"]:
        w = s["x1"] - s["x0"]
        if w <= 1e-9:
            continue
        ax.add_patch(
            Rectangle(
                (s["x0"], 0.0),
                w,
                s["top"],
                facecolor=s["color"],
                edgecolor="black",
                linewidth=0.8,
                zorder=2,
            )
        )

    for lg in layout["lane_groups"]:
        n = lg["n"]
        if n <= 1:
            continue
        for k in range(1, n):
            x = lg["x0"] + k * params["lebar_lajur"]
            center_line = params["jalur"] == 1 and n % 2 == 0 and k == n // 2
            draw_dashed_vline(
                ax,
                x,
                0.0,
                PAVEMENT_H,
                color="#f5f50a" if center_line else "white",
                lw=1.4 if center_line else 0.9,
            )

    specs = dimension_specs(layout)
    for (x0, x1, label, y, rotated) in specs:
        draw_width_dim(ax, x0, x1, y, label, rotated)

    kerb_dim_x = None
    kl = layout["kerb_left"]
    t = params["tinggi_kerb"]
    if kl is not None and t > 1e-9:
        kerb_dim_x = kl["x0"] - 0.45
        draw_kerb_height_dim(ax, kl, t, kerb_dim_x)

    x_min = min(-0.70, (kerb_dim_x - 0.60) if kerb_dim_x is not None else -0.70)
    x_max = layout["total_width"] + 0.70
    y_min = min(sp[3] for sp in specs) - 0.40
    y_max = layout["max_top"] + 0.55
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal")
    ax.axis("off")

    info = (
        f"{params['lajur']} lajur / {params['jalur']} jalur  |  "
        f"lebar lajur {params['lebar_lajur']:.2f} m  |  "
        f"kerb {params['lebar_kerb']:.2f} x {params['tinggi_kerb']:.2f} m  |  "
        f"tata guna lahan: {params['tata_guna_lahan']}"
    )
    ax.text(
        x_min + 0.15,
        y_max - 0.10,
        info,
        fontsize=7.0,
        va="top",
        ha="left",
        color="#333333",
        style="italic",
    )

    handles = [
        Rectangle(
            (0, 0), 1, 1, facecolor=c, edgecolor="black", label=name
        )
        for name, c in SEGMENT_COLORS.items()
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        fontsize=6.5,
        framealpha=0.9,
        edgecolor="#888888",
        title="Elemen",
        title_fontsize=7,
    )


def create_cross_section_figure(params, layout):
    fig, ax = plt.subplots(figsize=(11.0, 3.4))
    ax.set_title(
        f"Penampang Melintang - {params['project_name']}",
        fontsize=12,
        fontweight="bold",
        pad=10,
    )
    draw_cross_section(ax, params, layout)
    fig.tight_layout()
    return fig


def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except Exception:
            return ImageFont.load_default()


def render_plan_overlay(base_image, markers):
    overlay = base_image.convert("RGBA")
    draw = ImageDraw.Draw(overlay)
    w, h = overlay.size
    r = max(6, int(max(w, h) * 0.012))
    font = load_font(max(10, r))
    for m in markers:
        cx, cy = int(m["x"]), int(m["y"])
        color = MARKER_COLORS_RGB.get(m["type"], (255, 255, 255))
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=color + (210,),
            outline=(0, 0, 0, 255),
            width=2,
        )
        draw.text((cx + r + 2, cy - r - 2), m["type"], fill=(0, 0, 0, 255), font=font)
    return overlay


def marker_legend_html(markers):
    counts = Counter(m["type"] for m in markers)
    parts = []
    for t in MARKER_TYPES:
        parts.append(
            f'<span style="color:{MARKER_COLORS[t]};">&#9679;</span> {t} ({counts.get(t, 0)})'
        )
    return " &nbsp;&nbsp; ".join(parts)


def render_plan_section(uploaded_map):
    if uploaded_map is None:
        st.info(
            "Belum ada peta dasar. Unggah screenshot Google Earth pada sidebar "
            "untuk membuat Tampak Atas (Plan View)."
        )
        return None

    base_image = Image.open(uploaded_map)
    if max(base_image.size) > 2400:
        scale = 2400 / max(base_image.size)
        base_image = base_image.resize(
            (int(base_image.size[0] * scale), int(base_image.size[1] * scale)),
            Image.LANCZOS,
        )

    col_left, col_right = st.columns([1, 2])
    with col_left:
        marker_type = st.radio("Jenis Marker", MARKER_TYPES, index=0)
        st.markdown(marker_legend_html(st.session_state.markers), unsafe_allow_html=True)
        if st.session_state.markers:
            st.caption(f"Total marker: {len(st.session_state.markers)}")
            if st.button("Hapus Semua Marker", use_container_width=True):
                st.session_state.markers.clear()
                st.rerun()

    with col_right:
        overlay = render_plan_overlay(base_image, st.session_state.markers)
        try:
            coords = streamlit_image_coordinates(
                overlay, key="plan_map", use_container_width=True
            )
        except TypeError:
            coords = streamlit_image_coordinates(overlay, key="plan_map")
        if coords is not None and "x" in coords and "y" in coords:
            st.session_state.markers.append(
                {
                    "x": float(coords["x"]),
                    "y": float(coords["y"]),
                    "type": marker_type,
                }
            )
            st.rerun()

    if st.session_state.markers:
        st.markdown("**Daftar Marker**")
        st.dataframe(
            st.session_state.markers, use_container_width=True, hide_index=True
        )
    return overlay


def generate_dxf_bytes(params, layout):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    for name, (layer_name, color) in DXF_LAYER_MAP.items():
        doc.layers.add(layer_name, color=color)
    doc.layers.add("MARKA", color=7)
    doc.layers.add("DIMENSI", color=1)
    doc.layers.add("TEKS", color=4)

    if "DASHED" not in doc.linetypes:
        try:
            doc.linetypes.add(
                "DASHED", description="DASH __ __ __", pattern=[0.25, -0.15]
            )
        except Exception:
            pass

    for s in layout["segments"]:
        w = s["x1"] - s["x0"]
        if w <= 1e-9:
            continue
        layer_name = DXF_LAYER_MAP[s["name"]][0]
        msp.add_lwpolyline(
            [(s["x0"], 0.0), (s["x1"], 0.0), (s["x1"], s["top"]), (s["x0"], s["top"])],
            close=True,
            dxfattribs={"layer": layer_name},
        )

    for lg in layout["lane_groups"]:
        n = lg["n"]
        if n <= 1:
            continue
        for k in range(1, n):
            x = lg["x0"] + k * params["lebar_lajur"]
            center_line = params["jalur"] == 1 and n % 2 == 0 and k == n // 2
            msp.add_line(
                (x, 0.0),
                (x, PAVEMENT_H),
                dxfattribs={
                    "layer": "MARKA",
                    "linetype": "CONTINUOUS" if center_line else "DASHED",
                    "color": 2 if center_line else 7,
                },
            )

    for (x0, x1, label, y, rotated) in dimension_specs(layout):
        try:
            dim = msp.add_linear_dim(
                base=((x0 + x1) / 2.0, y),
                p1=(x0, 0.0),
                p2=(x1, 0.0),
                angle=0.0,
                text=label,
            )
            dim.render()
        except Exception:
            pass

    kl = layout["kerb_left"]
    t = params["tinggi_kerb"]
    if kl is not None and t > 1e-9:
        xd = kl["x0"] - 0.45
        try:
            dim = msp.add_linear_dim(
                base=(xd, (PAVEMENT_H + kl["top"]) / 2.0),
                p1=(kl["x0"], PAVEMENT_H),
                p2=(kl["x0"], kl["top"]),
                angle=90.0,
                text=f"{t:.2f}",
            )
            dim.render()
        except Exception:
            pass

    for s in layout["segments"]:
        w = s["x1"] - s["x0"]
        if w <= 1e-9:
            continue
        msp.add_text(
            s["name"], dxfattribs={"height": 0.16, "layer": "TEKS"}
        ).set_placement(
            ((s["x0"] + s["x1"]) / 2.0, s["top"] + 0.10), align=TextEntityAlignment.MIDDLE_CENTER
        )

    total = layout["total_width"]
    top = layout["max_top"]
    msp.add_text(
        f"ARVI - {params['project_name']}",
        dxfattribs={"height": 0.34, "layer": "TEKS"},
    ).set_placement((total / 2.0, top + 0.75), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text(
        f"Penampang Melintang | Surveyor: {params['surveyor_name']} | "
        f"Tahun: {params['year']} | Tata Guna Lahan: {params['tata_guna_lahan']}",
        dxfattribs={"height": 0.16, "layer": "TEKS"},
    ).set_placement((total / 2.0, top + 0.42), align=TextEntityAlignment.MIDDLE_CENTER)

    buf = io.BytesIO()
    text_buf = io.TextIOWrapper(buf, encoding="utf-8", newline="\n")
    doc.write(text_buf)
    text_buf.flush()
    text_buf.detach()
    return buf.getvalue()


def generate_report_bytes(params, layout, plan_image):
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")

    fig.text(
        0.5, 0.968, "ARVI - Automatic Road Visualization",
        ha="center", va="center", fontsize=10, color="#666666",
    )
    fig.text(
        0.5, 0.938, params["project_name"],
        ha="center", va="center", fontsize=19, fontweight="bold",
    )
    fig.text(
        0.5, 0.912,
        f"Surveyor: {params['surveyor_name']}   |   Tahun: {params['year']}   |   "
        f"Tata Guna Lahan Sekitar: {params['tata_guna_lahan']}",
        ha="center", va="center", fontsize=10,
    )
    fig.text(
        0.5, 0.893,
        f"Penampang Melintang: {params['lajur']} lajur / {params['jalur']} jalur   |   "
        f"Lebar Lajur: {params['lebar_lajur']:.2f} m   |   "
        f"Total Lebar: {layout['total_width']:.2f} m",
        ha="center", va="center", fontsize=8.5, color="#444444",
    )

    ax1 = fig.add_axes([0.05, 0.42, 0.90, 0.44])
    ax1.set_title("Penampang Melintang (Cross-Section)", fontsize=12, fontweight="bold", pad=8)
    draw_cross_section(ax1, params, layout)

    ax2 = fig.add_axes([0.10, 0.045, 0.80, 0.32])
    ax2.set_title("Tampak Atas (Plan View)", fontsize=12, fontweight="bold", pad=8)
    if plan_image is not None:
        ax2.imshow(plan_image)
    else:
        ax2.text(
            0.5, 0.5, "Tidak ada peta dasar yang diunggah.",
            ha="center", va="center", fontsize=12, color="#888888",
        )
    ax2.axis("off")

    fig.text(
        0.5, 0.012, "Dibuat menggunakan ARVI - Ekspor AutoCAD (.DXF), PDF, dan PNG",
        ha="center", va="center", fontsize=7.5, color="#999999",
    )

    pdf_buf = io.BytesIO()
    fig.savefig(pdf_buf, format="pdf")
    png_buf = io.BytesIO()
    fig.savefig(png_buf, format="png", dpi=180)
    plt.close(fig)
    return pdf_buf.getvalue(), png_buf.getvalue()


def render_export_section(params, layout, plan_image):
    st.markdown(
        "Klik tombol di bawah untuk mengunduh hasil akhir. File PDF/PNG berisi "
        "laporan layout (identitas proyek + penampang melintang + tampak atas), "
        "sedangkan file DXF berisi gambar CAD penampang melintang yang kompatibel "
        "dengan AutoCAD."
    )
    pdf_bytes, png_bytes = generate_report_bytes(params, layout, plan_image)
    dxf_bytes = generate_dxf_bytes(params, layout)

    safe_name = (
        re.sub(r"[^A-Za-z0-9_\- ]", "", params["project_name"]).strip().replace(" ", "_")
        or "ARVI"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "Download Laporan (PDF)",
            data=pdf_bytes,
            file_name=f"{safe_name}_Laporan.pdf",
            mime="application/pdf",
            use_container_width=True,
            help="Laporan final: identitas proyek, penampang melintang, dan tampak atas.",
        )
    with col2:
        st.download_button(
            "Download Layout (PNG)",
            data=png_bytes,
            file_name=f"{safe_name}_Layout.png",
            mime="image/png",
            use_container_width=True,
            help="Gambar layout final resolusi tinggi.",
        )
    with col3:
        st.download_button(
            "Download CAD (.DXF)",
            data=dxf_bytes,
            file_name=f"{safe_name}.dxf",
            mime="image/vnd.autocad.dxf",
            use_container_width=True,
            help="Gambar CAD penampang melintang dengan dimensi (AutoCAD-compatible).",
        )

    with st.expander("Info Isi File DXF"):
        st.markdown(
            "- Lapisan (layers): DRAINASE, TROTOAR, KERB, BAHU, LAJUR, MEDIAN, "
            "MARKA, DIMENSI, TEKS.\n"
            "- Dimensi otomatis (linear dim) untuk setiap elemen penampang.\n"
            "- Satuan: meter. Buka langsung di AutoCAD / ZWCAD / LibreCAD."
        )


def main():
    st.set_page_config(page_title="ARVI - Automatic Road Visualization", layout="wide")
    st.title("ARVI - Automatic Road Visualization")
    st.markdown(
        "Aplikasi MVP untuk memvisualisasikan penampang melintang jalan dan "
        "tampak atas berdasarkan data inventaris jalan, lalu mengekspor hasilnya "
        "ke PDF, PNG, dan AutoCAD (.DXF)."
    )

    params, uploaded_map = read_sidebar_inputs()

    if "markers" not in st.session_state:
        st.session_state.markers = []

    upload_key = getattr(uploaded_map, "name", None) if uploaded_map is not None else None
    if st.session_state.get("upload_key") != upload_key:
        st.session_state.upload_key = upload_key
        st.session_state.markers = []

    layout = compute_layout(params)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Lebar (ROW)", f"{layout['total_width']:.2f} m")
    m2.metric("Lajur / Jalur", f"{params['lajur']} / {params['jalur']}")
    m3.metric("Lebar Perkerasan", f"{pavement_width(layout):.2f} m")
    m4.metric("Tata Guna Lahan", params["tata_guna_lahan"])

    st.header("1. Pratinjau Penampang Melintang (Cross-Section)")
    fig = create_cross_section_figure(params, layout)
    st.pyplot(fig)
    st.caption(
        "Gambar skematis penampang melintang jalan. Klik ikon unduh (pojok kanan atas "
        "grafik) untuk menyimpan gambar pratinjau secara terpisah."
    )

    st.header("2. Pratinjau Tampak Atas (Plan View)")
    plan_image = render_plan_section(uploaded_map)

    st.header("3. Export Options")
    render_export_section(params, layout, plan_image)

    st.sidebar.markdown("---")
    st.sidebar.caption("ARVI MVP - Streamlit + matplotlib + Pillow + ezdxf")


if __name__ == "__main__":
    main()
