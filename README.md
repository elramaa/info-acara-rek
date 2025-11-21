# 🎭 Info Acara Rek – Aplikasi Manajemen Acara Jawa Timur Berbasis CLI

Aplikasi ini adalah sistem manajemen acara berbasis terminal yang memungkinkan **visitor** dan **organizer** mengelola, mencari, serta memantau acara — khususnya untuk memudahkan akses informasi acara di Jawa Timur.

Aplikasi ini mendukung:
- ✔ Multi-bahasa (Indonesia, Inggris, Jawa)
- ✔ Role-based menu (Visitor & Organizer)
- ✔ Penyimpanan data permanen (JSON)
- ✔ Review & attendance system
- ✔ Filtering lengkap berdasarkan banyak kriteria
- ✔ Tampilan tabel rapi
- ✔ Warna terminal
- ✔ Auto-update status acara ketika waktunya lewat

---

## 🧩 Fitur Utama

### 👥 1. Sistem Login & Role
- **Visitor:** melihat acara, hadir, memberi review, melakukan filter.
- **Organizer:** menambah, mengedit, menghapus acara, update status.

### 📅 2. Manajemen Acara
- Tambah, edit, hapus acara
- Status: *scheduled, finished, postponed, cancelled*
- Informasi acara lengkap: nama, waktu, lokasi, alamat, penyelenggara, kategori, deskripsi, HTM
- Auto-status update jika tanggal sudah lewat

### 🧍 3. Attendance & Review
- Visitor hadir tanpa input nama (menggunakan username login)
- Review hanya untuk event berstatus *finished*

### 🔎 4. Filtering Lengkap
Filter berdasarkan:
- tanggal
- minggu
- bulan
- lokasi
- kategori
- status
- range tanggal
- keyword
- multi-filter kolom

Hasil filter dapat dipilih untuk melihat detail event langsung.

### 📊 5. Statistik
Menampilkan statistik berdasarkan:
- kategori
- bulan
- lokasi

### 🌐 6. Multi Bahasa
Bahasa dapat diganti kapan saja:
- Indonesia
- Inggris
- Jawa

### 🖼️ 7. Tampilan CLI Rapi
- Warna terminal
- `clear_screen()` untuk membersihkan layar dan menghindari spam teks
- Tabel event rapi tanpa menampilkan ID internal

---

## 📁 Struktur Penyimpanan Data

Aplikasi menggunakan **JSON** (builtin module `json`) untuk menyimpan data:

- `events.json`  
  Menyimpan semua daftar event, attendees, dan review.

- `settings.json`  
  Menyimpan pengaturan seperti bahasa dan lokasi.

Tidak membutuhkan database eksternal.

---

## ▶️ Cara Menjalankan Program

1. Pastikan Python 3.8+ terpasang.
2. Jalankan:
   ```bash
   python main.py
	 ```
