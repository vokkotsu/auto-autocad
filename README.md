# ARVI - Automatic Road Visualization

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.45+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**ARVI (Automatic Road Visualization)** adalah aplikasi MVP (Minimum Viable Product) berbasis web untuk visualisasi dan ekspor desain penampang melintang jalan. Dibangun dengan **Streamlit** dan dirancang **mobile-first** untuk kemudahan penggunaan di lapangan.

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **📝 Input Data** | Form terstruktur untuk parameter jalan (lajur, lebar, kerb, trotoar, drainase, bahu, tata guna lahan) |
| **🛣️ Potongan Melintang** | Visualisasi schematic penampang melintang jalan real-time (Matplotlib) |
| **🗺️ Tampak Atas (Plan View)** | Upload screenshot Google Earth + penempatan marker interaktif (Rambu, PJU, APILL, Halte, Marka) |
| **💾 Ekspor Multi-Format** | **DXF** (AutoCAD-compatible), **PDF** (Laporan), **PNG** (Layout) |
| **📱 Mobile-First** | UI berbasis tab, full-width buttons, responsive charts, touch-friendly image clicker |

---

## 🚀 Quick Start

### Prasyarat
- Python 3.8+
- pip

### Instalasi

```bash
# Clone repository
git clone https://github.com/vokkotsu/auto-autocad.git
cd auto-autocad/arvi_app

# Install dependencies
pip install -r requirements.txt

# Jalankan aplikasi
streamlit run app.py
```

Aplikasi akan terbuka di: **http://localhost:8501**

---

## 📦 Dependencies

```
streamlit               # Web framework
matplotlib              # Cross-section plotting
Pillow                  # Image processing (Plan View)
streamlit-image-coordinates  # Interactive image clicker
ezdxf                   # DXF generation for AutoCAD
```

---

## 🏗️ Arsitektur Modular

```
arvi_app/
├── app.py                    # Main orchestration (tab-based UI)
├── requirements.txt
├── README.md
└── modules/
    ├── __init__.py           # Package initialization
    ├── ui_inputs.py          # Input form rendering (expanders, columns)
    ├── preview_engine.py     # Matplotlib cross-section & plan view overlay
    └── cad_engine.py         # DXF generation (ezdxf) + shared geometry logic
```

**Prinsip desain:**
- **Separation of concerns**: UI, Preview, CAD terpisah
- **Shared geometry**: `cross_section_segments()` digunakan oleh preview & CAD agar konsisten
- **Type hints**: Semua fungsi publik memiliki type annotations

---

## 📱 Panduan Penggunaan Mobile

1. **Tab "📝 Input Data"** — Isi parameter proyek & dimensi jalan. Gunakan *expander* untuk menghemat ruang layar.
2. **Tab "🛣️ Potongan Melintang"** — Lihat pratinjau cross-section real-time. Chart menyesuaikan lebar layar otomatis.
3. **Tab "🗺️ Tampak Atas"** — Upload foto Google Earth → tap pada gambar untuk tempatkan marker → pilih jenis (Rambu/PJU/APILL/Halte/Marka).
4. **Tab "💾 Export"** — Unduh **PDF**, **PNG**, atau **DXF** dengan satu tap (tombol full-width).

---

## 📐 Parameter Jalan yang Didukung

| Parameter | Keterangan | Default |
|-----------|------------|---------|
| `lajur` / `jalur` | Jumlah lajur & jalur (format: `2/1`, `4/2`) | `2/1` |
| `lebar_lajur` | Lebar per lajur (m) | `3.5` |
| `lebar_kerb` / `tinggi_kerb` | Dimensi trotoar/kerb (m) | `0.25` / `0.15` |
| `lebar_trotoar` | Lebar trotoar (m) | `1.5` |
| `drainase_type` | Tipe drainase | `Open Channel` |
| `lebar_drainase` | Lebar drainase (m) | `0.5` |
| `lebar_bahu` | Lebar bahu jalan (m) | `1.5` |
| `tata_guna_lahan` | Klasifikasi lahan sekitar | `Pemukiman` |

---

## 📤 Format Ekspor

| Format | Kegunaan |
|--------|----------|
| **.DXF** | Buka di AutoCAD / LibreCAD / QGIS untuk detail engineering |
| **.PDF** | Laporan siap cetak (header proyek + cross-section + plan view) |
| **.PNG** | Gambar layout untuk presentasi / dokumen |

---

## 🔧 Development

### Menjalankan Test Internal
```bash
python -c "
import sys; sys.path.insert(0, '.')
from modules.cad_engine import generate_dxf, cross_section_segments
from modules.preview_engine import draw_cross_section
params = {'project_name':'Test','surveyor_name':'Dev','year':2026,'lajur':4,'jalur':2,'lebar_lajur':3.5,'lebar_kerb':0.25,'tinggi_kerb':0.15,'lebar_trotoar':1.5,'drainase_type':'Open Channel','lebar_drainase':0.5,'lebar_bahu':1.5,'tata_guna_lahan':'Komersial'}
print('Segments:', len(cross_section_segments(params)))
fig = draw_cross_section(params); print('Figure OK:', fig)
import io; buf = generate_dxf(params); print('DXF bytes:', len(buf.getvalue()))
"
```

### Menambah Tipe Marker Baru
Edit `MARKER_TYPES` di `app.py` dan `MARKER_COLORS` di `modules/preview_engine.py`.

---

## 📄 Lisensi

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan.

---

## 🤝 Kontribusi

1. Fork repository
2. Buat branch fitur (`git checkout -b fitur/awesome-fitur`)
3. Commit perubahan (`git commit -m 'feat: tambah fitur awesome'`)
4. Push ke branch (`git push origin fitur/awesome-fitur`)
5. Buka Pull Request

---

## 📞 Kontak

**Repository:** https://github.com/vokkotsu/auto-autocad

---
*Dibangun dengan ❤️ menggunakan Streamlit untuk kebutuhan survey & desain jalan di lapangan.*