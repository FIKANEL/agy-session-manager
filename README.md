# Agy Session Manager for Windows ⚡

[![Release](https://img.shields.io/github/v/release/FIKANEL/agy-session-manager?color=5e6ad2&label=release)](https://github.com/FIKANEL/agy-session-manager/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%20(64--bit)-blue)](https://github.com/FIKANEL/agy-session-manager)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt%20for%20Python)-brightgreen)](https://wiki.qt.io/Qt_for_Python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Style](https://img.shields.io/badge/Brand%20DNA-Linear%20%C3%97%20Raycast-5e6ad2)](AGENT_CONTEXT.md)

Aplikasi desktop Windows modern berbasis **PySide6 (Qt for Python)** untuk mengelola, menelusuri riwayat percakapan, dan melanjutkan (*resume*) session **Agy CLI** tanpa perlu menghafal UUID atau mengetik command panjang di terminal secara manual.

Desain antarmuka dirancang presisi dengan **Brand DNA Linear × Raycast** (deep dark canvas `#08090a`, signature accent `#5e6ad2`, zero emoji dependency, dan typography Cascadia/Segoe UI).

---

## 📥 Download & Instalasi

Unduh versi rilis terbaru di halaman **[GitHub Releases](https://github.com/FIKANEL/agy-session-manager/releases)**:

| Format Unduhan | Keterangan | Rekomendasi Pengguna |
| :--- | :--- | :--- |
| **`AgySessionManager-v1.0.0-windows-x64-installer.exe`** | Setup Wizard lengkap, otomatis buat shortcut Desktop & Start Menu, ada fitur Uninstall. | ⭐ Pengguna Umum & Pemula |
| **`AgySessionManager-v1.0.0-windows-x64-portable.zip`** | Portable tanpa instalasi. Cukup ekstrak di folder mana pun lalu jalankan `AgySessionManager.exe`. | 💻 Developer / Power User |

> **Catatan Windows SmartScreen**: Karena aplikasi ini didistribusikan secara independen tanpa sertifikat EV berbayar Microsoft, Windows SmartScreen mungkin menampilkan layar biru *"Windows protected your PC"*. Cukup klik **More info** lalu pilih **Run anyway**. Seluruh kode sumber 100% open-source dan dapat diverifikasi via checksum SHA-256 di `SHA256SUMS.txt`.

---

## 📸 Fitur Utama

### 1. 🔍 Session Explorer & Filter Pintar
- **Deteksi Otomatis Session Asli**: Membaca database internal Agy CLI (`conversation_summaries.db`, `conversations/*.db`, dan folder `brain/`).
- **Informasi Lengkap**: Menampilkan Conversation ID (UUID), judul preview, jumlah step interaksi, timestamp terakhir diubah, workspace directory, status, dan depth sub-agent.
- **Pencarian Multi-Kriteria**: Cari berdasarkan potongan UUID, judul sesi, folder proyek, nama agent, atau kata kunci.
- **Filter & Sorting**:
  - Filter sub-agent (tampilkan/sembunyikan percakapan turunan).
  - Urutkan berdasarkan: Terakhir Digunakan, Terlama, Judul (A-Z), atau Jumlah Step.
- **Bintang (Pin to Top) & Custom Rename**: Sematkan sesi favorit ke bagian paling atas dan beri nama kustom yang lebih mudah diingat tanpa merusak metadata aslinya.

### 2. 🌿 Fork Session (Cabangkan Percakapan)
- Duplikasi percakapan aktif ke sesi baru yang terisolasi sempurna secara atomik.
- Menjaga trajectory meta, cascade ID, serta riwayat transcript tanpa merusak sesi induk.
- Memungkinkan Anda bereksperimen dengan instruksi baru dari checkpoint yang sama.

### 3. 💬 Chat History Viewer & Performance Engine
- **Tampilan Percakapan Interaktif**: Desain chat bubbles modern membedakan pesan `User`, `Assistant`, dan `System`.
- **Virtual Paginated Window**: Mampu memuat puluhan ribu baris log pesan dalam 92ms (<100ms) tanpa lag layouting.
- **Ekstraksi Bersih**: Otomatis membersihkan tag metadata internal (seperti `<USER_REQUEST>`, `<ADDITIONAL_METADATA>`, dll) untuk kenyamanan membaca.
- **Pencarian Dalam Chat**: Filter percakapan langsung per pesan secara instan.
- **Safety Read-Only**: Viewer membaca transcript secara read-only tanpa risiko mengubah database asli.

### 4. 🚀 Resume Session & Integrasi Terminal
- **Peluncuran Terpadu**: Jalankan kembali sesi di terminal hanya dengan satu klik:
  ```powershell
  agy --conversation=<UUID>
  ```
- **Terminal Terpadu**: Otomatis mendeteksi terminal terbaik di Windows:
  1. **Windows Terminal (`wt.exe`)** (disertai tab PowerShell dengan flag `-NoExit`).
  2. **PowerShell 7 (`pwsh.exe`)**.
  3. **Windows PowerShell (`powershell.exe`)**.
  4. **Command Prompt (`cmd.exe`)**.
- **Working Directory Otomatis**: Menyesuaikan direktori kerja dengan path workspace asli dari sesi tersebut.

### 5. 🛡️ Permission Mode Selector
- **Mode 1 — Default Permissions (Aman)**:
  - Command: `agy --conversation=<UUID>`
  - Menjalankan Agy CLI dengan konfirmasi izin interaktif normal.
- **Mode 2 — Skip Permissions (⚠️ Risiko)**:
  - Command: `agy --conversation=<UUID> --dangerously-skip-permissions`
  - Dilengkapi dialog konfirmasi eksplisit sebelum peluncuran untuk mencegah eksekusi aksi berisiko secara tidak sengaja.
  - Dinonaktifkan otomatis jika versi Agy CLI yang terpasang tidak mendukung flag tersebut.

---

## 📂 Struktur Proyek

```
C:\BOT\agy-session-manager\
├── .github/
│   └── workflows/
│       └── release.yml          # GitHub Actions auto-build & release CI/CD
├── assets/
│   ├── icon.ico                 # Multi-resolution application icon (16px - 256px)
│   ├── icon.png                 # 512x512 high-res logo
│   └── screenshot_after.png     # Tangkapan layar antarmuka
├── installer/
│   └── setup.iss                # Script compiler Inno Setup 6
├── scripts/
│   └── generate_app_icon.py     # Generator icon vector Qt & Pillow
├── src/
│   ├── agy_detector.py          # Deteksi instalasi, path, versi & kapabilitas Agy CLI
│   ├── delete_dialog.py         # Modal konfirmasi hapus / tong sampah
│   ├── fork_dialog.py           # Modal konfigurasi percabangan session (Fork)
│   ├── history_reader.py        # Parser transcript.jsonl & caching pesan
│   ├── icons.py                 # SVG vector icon renderer (zero emoji)
│   ├── main_window.py           # Tampilan utama 3-panel modular
│   ├── rename_dialog.py         # Modal ganti nama sesi
│   ├── session_deletion.py      # Logika pemindahan ke tong sampah & hapus permanen
│   ├── session_discovery.py     # Scanner SQLite conversation_summaries.db
│   ├── session_fork.py          # Engine percabangan sesi atomik
│   ├── session_launcher.py      # Builder argument CLI & Windows process runner
│   ├── session_search.py        # Algoritma pencarian, filter, dan sorting
│   ├── settings.py              # Manajemen konfigurasi JSON & preferensi user
│   ├── settings_dialog.py       # Modal dialog pengaturan Agy CLI & terminal
│   ├── styles.py                # Stylesheet generator
│   └── theme.py                 # Design tokens Linear x Raycast
├── tests/
│   ├── test_all.py              # Unit & integration test suite inti
│   ├── test_fork_feature.py     # Test suite percabangan session
│   ├── test_star_rename.py      # Test suite pin bintang & kustom judul
│   └── test_ui_features.py      # Test suite komponen interaktif UI
├── build_release.ps1            # Script 1-klik untuk build & packaging rilis
├── AgySessionManager.spec       # Konfigurasi build PyInstaller
├── main.py                      # Entry point aplikasi
├── LICENSE                      # Lisensi MIT
└── requirements.txt             # Dependensi Python
```

---

## 🛠️ Menjalankan dari Source Code (Development)

1. **Clone repository**:
   ```powershell
   git clone https://github.com/FIKANEL/agy-session-manager.git
   cd agy-session-manager
   ```

2. **Pasang dependency**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Jalankan aplikasi**:
   ```powershell
   python main.py
   ```

---

## 🧪 Menjalankan Test Suite

Proyek dilengkapi test suite lengkap untuk memverifikasi fungsionalitas, zero-emoji validation, serta keamanan data:

```powershell
python tests\test_all.py
python tests\test_ui_features.py
python tests\test_star_rename.py
python tests\test_fork_feature.py
```

---

## 📦 Membangun Paket Rilis Sendiri (Build Release)

Cukup jalankan script packaging otomatis di PowerShell:

```powershell
.\build_release.ps1
```

Script akan otomatis:
1. Memverifikasi kelengkapan icon `icon.ico` & `icon.png`.
2. Menjalankan seluruh test suite otomatis.
3. Mengompilasi aplikasi menjadi binary mandiri via PyInstaller.
4. Mengompres paket ke `release\AgySessionManager-v1.0.0-windows-x64-portable.zip`.
5. Mengompilasi Installer Inno Setup jika `iscc.exe` terpasang.
6. Menghasilkan daftar checksum SHA-256 di `release\SHA256SUMS.txt`.

---

## ❓ FAQ & Troubleshooting

1. **Agy CLI tidak terdeteksi otomatis (`❌ Tidak ditemukan`)**:
   - Buka menu **Pengaturan (⚙️)** di pojok kiri bawah sidebar.
   - Klik tombol **Browse...** lalu arahkan ke lokasi file `agy.exe` Anda (biasanya di `C:\Users\<Username>\AppData\Local\agy\bin\agy.exe`).
   - Klik **OK**. Pengaturan akan tersimpan permanen di `%APPDATA%\AgySessionManager\settings.json`.

2. **Daftar session kosong**:
   - Pastikan Anda pernah menjalankan Agy CLI minimal satu kali di komputer ini.
   - Klik tombol **Refresh** di samping kolom pencarian.

3. **Terminal langsung tertutup setelah resume**:
   - Secara default, aplikasi menggunakan Windows Terminal (`wt.exe`) yang mengeksekusi PowerShell dengan parameter `-NoExit`, sehingga terminal tetap terbuka meskipun proses Agy CLI telah selesai.

---

## 📄 Lisensi

Didistribusikan di bawah lisensi **MIT**. Lihat [LICENSE](LICENSE) untuk informasi lebih lanjut.
