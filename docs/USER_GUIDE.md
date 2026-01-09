# Panduan Pengguna - YHC Employee Export & Analytics

Panduan lengkap untuk menggunakan module YHC Employee Export & Analytics di Odoo 17.

## Daftar Isi

1. [Pendahuluan](#1-pendahuluan)
2. [Memulai](#2-memulai)
3. [Dashboard Analytics](#3-dashboard-analytics)
4. [Export Data Karyawan](#4-export-data-karyawan)
5. [Konfigurasi Export](#5-konfigurasi-export)
6. [Template Export](#6-template-export)
7. [Export Format Regulasi](#7-export-format-regulasi)
8. [Audit Log](#8-audit-log)
9. [API Integration](#9-api-integration)
10. [FAQ & Troubleshooting](#10-faq--troubleshooting)

---

## 1. Pendahuluan

### Tentang Module

YHC Employee Export & Analytics adalah module Odoo 17 yang menyediakan:

- **Dashboard interaktif** untuk visualisasi data karyawan
- **Export multi-format** (Excel, CSV, JSON, PDF)
- **Template export** yang dapat dikustomisasi
- **Format regulasi** untuk BPJS, SPT, dan WLK
- **Audit trail** untuk tracking aktivitas export

### Hak Akses

Module ini memiliki beberapa level akses:

| Level | Kemampuan |
|-------|-----------|
| **Export User** | Lihat dashboard, export basic |
| **Export Officer** | + Kelola konfigurasi dan template |
| **Export Manager** | + Full access, hapus konfigurasi |
| **Sensitive Data** | + Akses data sensitif (NPWP, gaji) |
| **Regulatory Export** | + Export format BPJS, SPT, WLK |

Hubungi administrator untuk mendapatkan akses yang sesuai.

---

## 2. Memulai

### Akses Menu

1. Login ke Odoo
2. Buka menu **Employees** (Karyawan)
3. Pilih submenu **Export & Analytics**

![Menu Location](images/menu_location.png)

### Struktur Menu

```
Employees
└── Export & Analytics
    ├── Dashboard          # Visualisasi data
    ├── Export Data        # Wizard export
    │   ├── Export Karyawan
    │   └── Export Regulasi
    ├── Configuration      # Pengaturan
    │   ├── Export Config
    │   └── Export Template
    └── Audit Log          # Log aktivitas
```

---

## 3. Dashboard Analytics

### Membuka Dashboard

1. Buka menu **Employees > Export & Analytics > Dashboard**
2. Dashboard akan menampilkan visualisasi data karyawan

### Komponen Dashboard

#### KPI Cards
Bagian atas menampilkan 4 KPI utama:

| KPI | Deskripsi |
|-----|-----------|
| Total Karyawan | Jumlah seluruh karyawan |
| Karyawan Aktif | Karyawan dengan status aktif |
| Kontrak Aktif | Karyawan dengan kontrak berlaku |
| Turnover Rate | Persentase turnover (keluar/total × 100) |

#### Charts

1. **Distribusi Gender** (Pie Chart)
   - Menampilkan proporsi laki-laki dan perempuan
   - Klik pada segment untuk filter

2. **Karyawan per Departemen** (Bar Chart)
   - Jumlah karyawan tiap departemen
   - Urut dari terbanyak

3. **Trend Rekrutmen** (Line Chart)
   - Grafik rekrutmen bulanan
   - Periode 12 bulan terakhir

4. **Status Kontrak** (Doughnut Chart)
   - Distribusi jenis kontrak
   - PKWTT, PKWT, Outsource, dll

5. **Distribusi Usia** (Bar Chart)
   - Kelompok usia karyawan
   - Range 5 tahun

6. **Sebaran Gaji** (Histogram)
   - Distribusi range gaji
   - Memerlukan akses sensitive data

7. **Masa Kerja** (Horizontal Bar)
   - Kelompok berdasarkan lama bekerja
   - < 1 tahun, 1-3 tahun, 3-5 tahun, > 5 tahun

8. **Top Departemen** (Radar Chart)
   - Perbandingan 5 departemen terbesar
   - Berdasarkan jumlah karyawan

### Filter Data

#### Filter Departemen
1. Klik dropdown "Departemen" di atas dashboard
2. Pilih departemen yang diinginkan
3. Charts akan diperbarui otomatis

#### Filter Tanggal
1. Klik ikon kalender pada date range
2. Pilih tanggal mulai dan akhir
3. Klik "Apply" untuk menerapkan filter

### Export Dashboard

1. Klik tombol **Export** di pojok kanan atas
2. Pilih format (PDF atau PNG)
3. File akan di-download

---

## 4. Export Data Karyawan

### Quick Export

Untuk export cepat dari daftar karyawan:

1. Buka **Employees** (daftar karyawan)
2. Pilih karyawan yang akan di-export (checkbox)
3. Klik **Action > Export Employees**
4. Pilih format (XLSX, CSV, JSON, PDF)
5. Klik **Export**

### Export dengan Wizard

Untuk export dengan opsi lengkap:

1. Buka menu **Employees > Export & Analytics > Export Data > Export Karyawan**
2. Wizard export akan terbuka

#### Langkah 1: Pilih Konfigurasi
- Pilih konfigurasi export yang sudah dibuat
- Atau biarkan kosong untuk semua field default

#### Langkah 2: Filter Karyawan
- **Departemen**: Filter berdasarkan departemen
- **Status**: Aktif/Non-aktif
- **Tanggal Bergabung**: Range tanggal join

#### Langkah 3: Pilih Format
| Format | Deskripsi | Penggunaan |
|--------|-----------|------------|
| XLSX | Excel dengan styling | Laporan formal |
| CSV | Comma-separated | Import ke sistem lain |
| JSON | Data terstruktur | API integration |
| PDF | Dokumen printable | Arsip fisik |

#### Langkah 4: Opsi Tambahan
- **Include Header**: Sertakan baris header
- **Date Format**: Format tanggal (DD/MM/YYYY, dll)
- **Encoding**: UTF-8 (default) atau lainnya

#### Langkah 5: Export
1. Review pilihan
2. Klik **Export**
3. File akan di-download otomatis

### Hasil Export

#### Format XLSX
- Header dengan styling (bold, background color)
- Auto-fit column width
- Format tanggal dan angka

#### Format CSV
```csv
"Name","NIK","Department","Position","Join Date"
"John Doe","EMP001","IT","Developer","2023-01-15"
```

#### Format JSON
```json
{
  "employees": [
    {
      "name": "John Doe",
      "nik": "EMP001",
      "department": "IT",
      "position": "Developer",
      "join_date": "2023-01-15"
    }
  ],
  "export_date": "2024-01-15T10:30:00",
  "total_records": 1
}
```

---

## 5. Konfigurasi Export

### Membuat Konfigurasi

1. Buka **Employees > Export & Analytics > Configuration > Export Config**
2. Klik **Create**

#### Field Konfigurasi

| Field | Deskripsi | Wajib |
|-------|-----------|-------|
| Name | Nama konfigurasi | ✓ |
| Description | Deskripsi penggunaan | |
| Active | Status aktif/non-aktif | |
| Fields | Field yang akan di-export | ✓ |
| Domain Filter | Filter karyawan (JSON domain) | |
| Default Format | Format default | |

#### Memilih Fields

1. Klik tab **Fields**
2. Klik **Add a line**
3. Pilih field dari daftar
4. Drag untuk mengatur urutan

**Field yang tersedia:**
- **Personal**: Name, NIK, Gender, Birth Date, dll
- **Employment**: Department, Position, Join Date, dll
- **Contact**: Email, Phone, Address
- **Sensitive**: NPWP, Salary (memerlukan akses khusus)

#### Domain Filter

Contoh domain filter:

```python
# Hanya karyawan aktif
[('active', '=', True)]

# Departemen tertentu
[('department_id.name', '=', 'IT')]

# Bergabung tahun 2024
[('date_join', '>=', '2024-01-01'), ('date_join', '<=', '2024-12-31')]

# Kombinasi
[('active', '=', True), ('department_id.name', 'in', ['IT', 'HR'])]
```

### Mengelola Konfigurasi

#### Edit Konfigurasi
1. Buka konfigurasi dari daftar
2. Klik **Edit**
3. Ubah field yang diperlukan
4. Klik **Save**

#### Duplicate Konfigurasi
1. Buka konfigurasi
2. Klik **Action > Duplicate**
3. Edit nama dan field
4. Klik **Save**

#### Archive Konfigurasi
1. Buka konfigurasi
2. Klik **Action > Archive**
3. Konfigurasi tidak akan muncul di dropdown export

---

## 6. Template Export

### Membuat Template

Template adalah konfigurasi export yang siap pakai:

1. Buka **Configuration > Export Template**
2. Klik **Create**

#### Field Template

| Field | Deskripsi |
|-------|-----------|
| Name | Nama template |
| Based on Config | Konfigurasi dasar |
| Header Style | Styling header (XLSX/PDF) |
| Footer Text | Teks footer |
| Include Logo | Sertakan logo perusahaan |
| Shared | Template bisa dipakai semua user |

#### Header Style Options

```json
{
  "bold": true,
  "bg_color": "#4A90D9",
  "font_color": "#FFFFFF",
  "border": 1,
  "align": "center"
}
```

### Menggunakan Template

1. Saat export, pilih template dari dropdown
2. Template akan override konfigurasi default
3. Hasil export sesuai dengan pengaturan template

---

## 7. Export Format Regulasi

### BPJS Kesehatan

Export data untuk pelaporan BPJS Kesehatan:

1. Buka **Export Data > Export Regulasi**
2. Pilih **BPJS Kesehatan**
3. Pilih periode
4. Klik **Generate**

**Format output:**
- Nomor BPJS
- Nama Peserta
- NIK
- Kelas Rawat
- Gaji
- Iuran

### BPJS Ketenagakerjaan

Export untuk BPJS TK:

1. Pilih **BPJS Ketenagakerjaan**
2. Pilih program (JHT, JP, JKK, JKM)
3. Generate file

**Includes:**
- Data peserta
- Perhitungan iuran per program
- Summary total

### SPT Tahunan

Export data untuk pelaporan pajak:

1. Pilih **SPT Tahunan**
2. Pilih tahun pajak
3. Generate

**Data yang di-export:**
- NPWP
- Penghasilan bruto
- Potongan
- PPh 21

### WLK (Wajib Lapor Ketenagakerjaan)

Format untuk Disnaker:

1. Pilih **WLK**
2. Pilih periode laporan
3. Generate sesuai format Disnaker

---

## 8. Audit Log

### Melihat Log

1. Buka **Employees > Export & Analytics > Audit Log**
2. Daftar log akan ditampilkan

#### Informasi Log

| Field | Deskripsi |
|-------|-----------|
| Timestamp | Waktu export |
| User | Pengguna yang export |
| Type | Jenis export |
| Format | Format file |
| Record Count | Jumlah record |
| Duration | Lama proses |
| Status | Success/Failed |
| IP Address | Alamat IP |

### Filter Log

Gunakan filter untuk mencari log:

- **By User**: Filter berdasarkan pengguna
- **By Date**: Filter berdasarkan tanggal
- **By Type**: Filter berdasarkan jenis export
- **By Status**: Filter success/failed

### Export Log

1. Pilih log yang diinginkan
2. Klik **Action > Export**
3. Pilih format (XLSX/CSV)

---

## 9. API Integration

### Authentication

API menggunakan Bearer token:

```bash
curl -X POST \
  https://your-odoo.com/api/v1/auth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "login": "admin",
    "password": "admin"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "expires_in": 3600
}
```

### Dashboard API

```bash
curl -X GET \
  'https://your-odoo.com/api/v1/employee-export/dashboard?department_id=1' \
  -H 'Authorization: Bearer {token}'
```

### Export API

```bash
curl -X POST \
  https://your-odoo.com/api/v1/employee-export/export \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/json' \
  -d '{
    "config_id": 1,
    "format": "xlsx",
    "employee_ids": [1, 2, 3]
  }'
```

Response berisi file dalam base64:
```json
{
  "status": "success",
  "file_name": "export_20240115.xlsx",
  "file_data": "UEsDBBQAAAgAA...",
  "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

---

## 10. FAQ & Troubleshooting

### FAQ

**Q: Mengapa saya tidak bisa melihat data gaji di export?**

A: Data gaji termasuk data sensitif. Anda memerlukan akses "Sensitive Data Access" untuk melihat dan mengexport data tersebut. Hubungi administrator.

**Q: Bagaimana cara menambahkan field baru ke export?**

A: Buat konfigurasi baru atau edit konfigurasi existing. Tambahkan field yang diinginkan di tab "Fields".

**Q: Export PDF tidak berjalan, apa yang salah?**

A: Pastikan `wkhtmltopdf` sudah terinstall di server. Hubungi administrator sistem.

**Q: Bisakah saya schedule export otomatis?**

A: Fitur ini akan tersedia di versi mendatang. Saat ini export harus dilakukan manual.

### Troubleshooting

#### Error: "Access Denied"
- Pastikan Anda memiliki akses yang sesuai
- Logout dan login kembali
- Hubungi administrator

#### Error: "No employees found"
- Periksa filter konfigurasi
- Pastikan domain filter benar
- Coba export tanpa filter

#### Error: "Export failed"
- Cek ukuran data (terlalu besar?)
- Cek log server untuk detail error
- Hubungi administrator

#### Charts tidak muncul di Dashboard
- Clear browser cache (Ctrl+Shift+Delete)
- Refresh halaman (Ctrl+F5)
- Pastikan JavaScript enabled
- Coba browser lain

#### Export file kosong
- Pastikan ada data yang match dengan filter
- Periksa akses ke field yang dipilih
- Cek audit log untuk error message

---

## Kontak Support

Jika mengalami masalah yang tidak tercakup di panduan ini:

- **Email**: support@your-company.com
- **Internal Ticket**: [Link ke sistem ticketing]
- **Admin Odoo**: [Nama admin]

---

*Dokumentasi ini berlaku untuk YHC Employee Export & Analytics versi 17.0.1.0.0*

*Terakhir diupdate: Januari 2025*
