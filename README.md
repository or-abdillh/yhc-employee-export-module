# YHC Employee Export & Analytics

[![Odoo Version](https://img.shields.io/badge/Odoo-17.0-purple.svg)](https://www.odoo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL%20v3-green.svg)](https://www.gnu.org/licenses/lgpl-3.0)

Modul custom Odoo 17 untuk ekspor data karyawan dengan fitur analytics dashboard, multiple format export, dan regulatory compliance. Terintegrasi dengan module `yhc_employee`.

## 📋 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Persyaratan Sistem](#-persyaratan-sistem)
- [Instalasi](#-instalasi)
- [Konfigurasi](#️-konfigurasi)
- [Penggunaan](#-penggunaan)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Struktur Modul](#-struktur-modul)
- [Changelog](#-changelog)

## ✨ Fitur Utama

### 1. Dashboard Analytics
- **KPI Cards**: Total karyawan, aktif, kontrak, turnover rate
- **Charts Interaktif**: 
  - Distribusi gender (Pie Chart)
  - Karyawan per departemen (Bar Chart)
  - Trend rekrutmen (Line Chart)
  - Status kontrak (Doughnut Chart)
  - Distribusi usia (Bar Chart)
  - Sebaran gaji (Histogram)
  - Masa kerja (Horizontal Bar)
  - Top departemen (Radar Chart)
- **Filter & Date Range**: Filter berdasarkan departemen dan periode

### 2. Multi-Format Export
- **Excel (XLSX)**: Format spreadsheet dengan styling
- **CSV**: Format comma-separated untuk integrasi
- **JSON**: Format data terstruktur untuk API
- **PDF**: Laporan dengan format printable

### 3. Template Export Kustom
- Buat template dengan field yang dipilih
- Simpan konfigurasi untuk penggunaan berulang
- Share template antar pengguna

### 4. Regulatory Exports
- **BPJS Kesehatan**: Format sesuai standar BPJS Kesehatan
- **BPJS Ketenagakerjaan**: Format untuk BPJS TK
- **SPT Tahunan**: Format untuk laporan pajak
- **WLK (Wajib Lapor Ketenagakerjaan)**: Format Disnaker

### 5. Security & Audit
- **Role-based Access Control**: 
  - Export User (basic export)
  - Export Officer (template management)
  - Export Manager (full access)
  - Sensitive Data Access (NPWP, Salary)
  - Regulatory Export Access
- **Audit Trail**: Log semua aktivitas export
- **Record Rules**: Pembatasan akses per user/company

### 6. Workforce Report Engine (NEW)

**Official Workforce Structural Report** - Sistem laporan resmi berbasis snapshot untuk pelaporan struktur SDM.

#### Karakteristik Utama:
- **Snapshot-based**: Data diambil dari snapshot akhir bulan (immutable)
- **Fixed Structure**: Struktur laporan dikunci oleh sistem
- **Audit-ready**: Angka stabil dan dapat direkonsiliasi
- **PDF Output**: Dokumen resmi siap cetak (Landscape A4, 300 DPI)

#### Komponen Laporan:
1. **Tabel Payroll vs Non-Payroll per Unit**
   - Breakdown per gender (L/P)
   - Total per unit dan keseluruhan

2. **Grafik Payroll vs Non-Payroll per Unit**
   - Bar chart dengan data identik dengan tabel

3. **Grafik Total Karyawan per Unit**
   - Jumlah = Payroll + Non-Payroll + HJU + PNS DPK
   - Grafik utama laporan eksekutif

4. **Snapshot Bulanan per Unit**
   - Tabel historis Jan-Des
   - Data langsung dari snapshot

5. **Distribusi Status Kepegawaian**
   - Kategori: Tetap, PKWT, SPK, THL, HJU, PNS DPK
   - Pie chart dengan total terrekonsiliasi

#### Employment Classification (System-owned):
| Kategori | Keterangan |
|----------|------------|
| Payroll | Karyawan payroll |
| Non Payroll | Karyawan non-payroll |
| Tetap | Pegawai tetap |
| PKWT | Perjanjian Kerja Waktu Tertentu |
| SPK | Surat Perjanjian Kerja |
| THL | Tenaga Harian Lepas |
| HJU | Honorer Jasa Umum |
| PNS DPK | PNS Diperbantukan |

> ⚠️ **Penting**: Kategori ini TIDAK BOLEH diubah atau digabung karena merupakan sumber kebenaran untuk audit.

## 💻 Persyaratan Sistem

### Software Requirements
- Odoo 17.0 (Community atau Enterprise)
- Python 3.10 atau lebih tinggi
- PostgreSQL 14+

### Python Dependencies
```
xlsxwriter>=3.0.0
matplotlib>=3.7.0
numpy>=1.24.0
wkhtmltopdf (untuk PDF export)
```

### Module Dependencies
- `yhc_employee` (custom employee module)
- `hr` (Odoo HR module)
- `web` (Odoo web module)
- `mail` (untuk notifikasi)

## 📦 Instalasi

### 1. Clone Repository
```bash
cd /path/to/odoo/custom-addons
git clone https://github.com/your-org/yhc_employee_export.git
```

### 2. Install Dependencies
```bash
pip install xlsxwriter
sudo apt install wkhtmltopdf  # Untuk PDF export
```

### 3. Update Module List
```bash
./odoo-bin -c odoo.conf -d your_database -u base --stop-after-init
```

### 4. Install Module
Melalui Odoo:
1. Buka menu **Apps**
2. Klik **Update Apps List**
3. Cari "YHC Employee Export"
4. Klik **Install**

Atau via command line:
```bash
./odoo-bin -c odoo.conf -d your_database -i yhc_employee_export --stop-after-init
```

## ⚙️ Konfigurasi

### 1. Assign Security Groups
1. Buka **Settings > Users & Companies > Users**
2. Pilih user yang akan dikonfigurasi
3. Di tab **Access Rights**, section **Employee Export**:
   - Pilih level akses (User/Officer/Manager)
   - Centang "Sensitive Data Access" jika diperlukan
   - Centang "Regulatory Export" untuk akses BPJS/SPT

### 2. Konfigurasi Export
1. Buka menu **Employees > Export > Configuration**
2. Buat konfigurasi baru:
   - **Name**: Nama konfigurasi
   - **Description**: Deskripsi penggunaan
   - **Format**: Pilih format default (XLSX/CSV/JSON/PDF)
   - **Fields**: Pilih field yang akan di-export
   - **Filters**: Tambahkan filter domain jika diperlukan

### 3. Buat Template Export
1. Buka menu **Employees > Export > Templates**
2. Klik **Create**:
   - **Template Name**: Nama template
   - **Based On Config**: Pilih konfigurasi
   - **Custom Fields**: Override field selection
   - **Header Style**: Kustomisasi header (XLSX/PDF)

## 📖 Penggunaan

### Dashboard Analytics
1. Buka menu **Employees > Export > Dashboard**
2. Gunakan filter departemen di dropdown
3. Pilih date range untuk analisis periode tertentu
4. Klik pada chart untuk detail lebih lanjut

### Export Data Karyawan
1. Dari daftar karyawan, pilih record yang akan di-export
2. Klik **Action > Export Employees**
3. Pilih konfigurasi atau template
4. Pilih format output
5. Klik **Export**
6. File akan otomatis di-download

### Regulatory Export
1. Buka menu **Employees > Export > Regulatory**
2. Pilih jenis laporan:
   - BPJS Kesehatan
   - BPJS Ketenagakerjaan
   - SPT Tahunan
   - WLK
3. Pilih periode laporan
4. Klik **Generate Report**

### Workforce Report (Official Report)
Laporan resmi struktur SDM berbasis snapshot.

#### Generate Snapshot Data
Sebelum membuat laporan, pastikan snapshot tersedia:
1. Buka menu **Employees > Export & Analytics > Workforce Report**
2. Pilih bulan dan tahun
3. Jika snapshot belum tersedia, klik **Generate Snapshot**
4. Tunggu proses selesai

#### Generate Report PDF
1. Buka menu **Employees > Export & Analytics > Workforce Report**
2. Pilih **Bulan** dan **Tahun**
3. Sistem akan memvalidasi ketersediaan snapshot
4. Jika tersedia, klik **Generate Report**
5. PDF akan di-download otomatis

#### Alur Penggunaan
```
Menu: Workforce Report
        ↓
  Pilih Bulan & Tahun
        ↓
  Validasi Snapshot
        ↓
    Generate Report
        ↓
  PDF Terbentuk (Read-only)
```

> ⚠️ **Catatan**: 
> - Tidak ada pilihan grafik (struktur fixed)
> - Tidak ada filter bebas
> - Laporan identik jika di-generate ulang (reproducible)

## 🔌 API Reference

### REST Endpoints

#### Dashboard Data
```http
GET /api/v1/employee-export/dashboard
Authorization: Bearer {token}
Content-Type: application/json

Query Parameters:
- department_id: Filter by department (optional)
- date_from: Start date YYYY-MM-DD (optional)
- date_to: End date YYYY-MM-DD (optional)

Response:
{
  "status": "success",
  "data": {
    "kpi": { ... },
    "gender_distribution": [ ... ],
    "department_distribution": [ ... ]
  }
}
```

#### Export Data
```http
POST /api/v1/employee-export/export
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "config_id": 1,
  "format": "xlsx",
  "employee_ids": [1, 2, 3]
}

Response:
{
  "status": "success",
  "file_name": "export_20240115.xlsx",
  "file_data": "base64_encoded_content",
  "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

#### Audit Logs
```http
GET /api/v1/employee-export/audit-logs
Authorization: Bearer {token}
Content-Type: application/json

Query Parameters:
- user_id: Filter by user (optional)
- limit: Number of records (default: 100)

Response:
{
  "status": "success",
  "data": {
    "logs": [ ... ],
    "total": 150
  }
}
```

### Python API

#### Export Service
```python
from odoo.addons.yhc_employee_export.services import ExportXLSX

# Initialize service
export_service = ExportXLSX(env, config)

# Export employees
file_data, filename = export_service.export(employees)
```

#### Dashboard Analytics
```python
analytics = env['hr.employee.analytics']

# Get dashboard data
data = analytics.get_dashboard_data(
    department_id=1,
    date_from='2024-01-01',
    date_to='2024-12-31'
)
```

#### Workforce Report Service
```python
# Get service instance
service = env['workforce.report.service'].get_service()

# Validate snapshot exists
service.validate_snapshot_exists(year=2025, month=1)

# Get payroll vs non-payroll table
table_data = service.get_payroll_vs_non_payroll_table(2025, 1)

# Get total workforce per unit
workforce_data = service.get_total_workforce_per_unit(2025, 1)

# Get employment status distribution
status_data = service.get_employment_status_distribution(2025, 1)

# Get monthly snapshot trend
trend_data = service.get_monthly_workforce_snapshot(2025)

# Generate complete report data
report_data = service.generate_complete_report_data(2025, 1)
```

#### Snapshot Management
```python
Snapshot = env['hr.employee.snapshot']

# Check if snapshot exists
exists = Snapshot.check_snapshot_exists(2025, 1)

# Generate snapshot for a period
Snapshot.generate_snapshot(2025, 1)

# Get snapshot data
snapshots = Snapshot.search([
    ('snapshot_year', '=', 2025),
    ('snapshot_month', '=', 1),
    ('is_active', '=', True),
])
```

## 🧪 Testing

### Run All Tests
```bash
./odoo-bin -c odoo.conf -d testdb \
    --test-tags yhc_export \
    -i yhc_employee_export \
    --stop-after-init
```

### Run Specific Test
```bash
# Test export config
./odoo-bin -c odoo.conf -d testdb \
    --test-tags yhc_export \
    --test-file tests/test_export_config.py \
    --stop-after-init
```

### Test Coverage
| Module | Coverage |
|--------|----------|
| Export Config | ✅ Full |
| Export Services | ✅ Full |
| Dashboard Analytics | ✅ Full |
| Security & Access | ✅ Full |
| REST API | ✅ Basic |
| Workforce Report | ✅ Full |
| Employee Snapshot | ✅ Full |

## 📁 Struktur Modul

```
yhc_employee_export/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   ├── dashboard_controller.py
│   └── export_controller.py
├── data/
│   └── export_template_data.xml
├── docs/
│   ├── PRD_Employee_Export_Analytics.md
│   ├── PRD_Workforce_Report_Engine.md    # NEW
│   ├── Prompt_Master.md
│   └── USER_GUIDE.md
├── models/
│   ├── __init__.py
│   ├── export_audit_log.py
│   ├── export_config.py
│   ├── export_graph_config.py
│   ├── export_security_mixin.py
│   ├── export_template.py
│   ├── graph_registry.py
│   ├── hr_employee_analytics.py
│   ├── hr_employee_snapshot.py           # NEW - Snapshot data model
│   └── workforce_report_service.py       # NEW - Report service wrapper
├── reports/
│   ├── bpjs_report.xml
│   ├── employee_export_report.xml
│   ├── workforce_analytics_report.xml
│   └── workforce_official_report.xml     # NEW - Official report template
├── security/
│   ├── export_security.xml
│   ├── ir.model.access.csv
│   ├── snapshot_security.xml             # NEW
│   └── workforce_report_security.xml     # NEW
├── services/
│   ├── __init__.py
│   ├── advanced_graph_renderer.py        # NEW - Matplotlib renderer
│   ├── employee_analytics_service.py
│   ├── export_base.py
│   ├── export_bpjs_kes.py
│   ├── export_bpjs_tk.py
│   ├── export_csv.py
│   ├── export_graph_pdf.py
│   ├── export_json.py
│   ├── export_pdf.py
│   ├── export_regulatory.py
│   ├── export_xlsx.py
│   └── workforce_report_service.py       # NEW - Core report service
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       ├── css/
│       │   └── dashboard.css
│       ├── js/
│       │   └── dashboard.js
│       └── xml/
│           └── dashboard_templates.xml
├── tests/
│   ├── __init__.py
│   ├── test_dashboard.py
│   ├── test_export_config.py
│   ├── test_export_service.py
│   ├── test_security.py
│   ├── test_workforce_analytics.py       # NEW
│   └── test_workforce_report.py          # NEW
├── views/
│   ├── audit_log_views.xml
│   ├── export_graph_views.xml
│   ├── export_wizard_views.xml
│   ├── export_workforce_views.xml
│   ├── menu_views.xml
│   ├── seed_wizard_views.xml
│   └── workforce_report_views.xml        # NEW
└── wizards/
    ├── __init__.py
    ├── export_graph_wizard.py
    ├── export_wizard.py
    ├── export_workforce_wizard.py
    ├── seed_wizard.py
    └── workforce_report_wizard.py        # NEW - Report wizard
```

## 📝 Changelog

Lihat [CHANGELOG.md](CHANGELOG.md) untuk detail perubahan setiap versi.

## 👥 Author

YHC Development Team

## 📄 License

LGPL-3