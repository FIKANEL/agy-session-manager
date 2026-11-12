# AGENT_CONTEXT.md

## Framework & Tech Stack
- **Application**: Agy Session Manager for Windows
- **GUI Engine**: PySide6 (Qt for Python 6.5+)
- **OS**: Windows 11 / Windows 10 (64-bit)
- **Architecture**: 3-panel modular desktop application (`sidebar`, `session_list`, `chat_viewer`)

---

## Brand DNA (Linear x Raycast)

### 1. Primary Brand: Linear
- **Philosophy**: Deep dark product canvas, high information density, hairline 1px borders, lavender-blue signature accent (`#5e6ad2`) used with strict intent.
- **Surface Ladder**:
  - `canvas`: `#08090a`
  - `sidebar`: `#0d0e11`
  - `surface-panel`: `#111216`
  - `surface-card`: `#14151a`
  - `surface-selected`: `#1c1f2b`
  - `hairline`: `#23252a`
  - `hairline-strong`: `#34363f`

### 2. Secondary Brand: Raycast
- **Philosophy**: Precision developer tool ergonomics, keyboard-friendly metadata presentation, monospace command blocks, clean badge chips.
- **Accent & Semantics**:
  - `accent-primary`: `#5e6ad2` (CTA / Resume)
  - `accent-success`: `#22c55e` (Agy CLI Ready / Connected)
  - `accent-warning`: `#f59e0b` (Skip Permissions Caution)
  - `accent-danger`: `#ef4444` (Killed / Error)

---

## Design Recipe & UI Audit Resolutions

| Masalah Teridentifikasi | Resolusi Desain (Linear x Raycast) |
| :--- | :--- |
| **Judul panjang di list kiri menimpa baris bawah** | Gunakan `QFontMetrics.elidedText` dengan single/two-line clamp terukur, tinggi item konsisten 74px, padding 10px 12px, gap vertikal stabil. |
| **Tombol biru refresh kosong** | Ganti dari emoji raw `🔄` ke SVG/QIcon vector refresh icon dengan label jelas atau icon toolbar bergaya Raycast (`border: 1px solid #34363f`, hover state lembut). |
| **Bobot tombol aksi header seragam** | **Hierarki 3 level**:<br>• **Primary**: Resume Session (`#5e6ad2`, white text, glow focus).<br>• **Secondary**: Copy ID & Copy Command (`#1c1e24`, border `#34363f`, hover `#252831`).<br>• **Tertiary/Ghost**: Open Folder (minimal border, ghost hover). |
| **Teks command panjang di header wrap berantakan** | Pindahkan ke **Dedicated Monospace Command Block** di bawah action bar: kotak terminal compact (`#0a0b0e`, border `#23252a`, monospace font `Consolas`/`Cascadia Code`, single-line horizontal scroll/elide + tombol Copy Command instan). |
| **Emoji campur-campur tidak konsisten** | Standarisasi ke unified monochrome vector glyphs (SVG/Qt vector painting) untuk sidebar, action bar, status badge, dan metadata. |
| **Item session terpilih kurang kontras** | Background `#1c1f2b`, left indicator bar 3px `#5e6ad2`, title color `#ffffff` (vs `#a6abb8` unselected), time & step badge highlight. |
| **Bubble chat User vs Assistant mirip** | • **User**: Rata kanan/docked dengan background indigo-tinted `#161a29`, border `#2c3554`, avatar badge "YOU".<br>• **Assistant**: Background `#121318`, border `#23252a`, avatar badge "AGY".<br>• **Metadata**: Token & tool call chips dengan styling monospace chip (`#191b22`, border `#2e303a`). |
| **Spacing & typography tidak konsisten** | Terapkan Design Tokens terpusat di `src/theme.py` (`Colors`, `Typography`, `Spacing`, `Radius`). |
| **Skip Permissions terlalu mencolok/mentah** | Styled Warning Chip (`#261906` bg, `#d97706` border, `#f59e0b` text) dengan icon warning rapi dan tooltip eksplisit. |
