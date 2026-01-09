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

## 💻 Persyaratan Sistem

### Software Requirements
- Odoo 17.0 (Community atau Enterprise)
- Python 3.10 atau lebih tinggi
- PostgreSQL 14+

### Python Dependencies
```
xlsxwriter>=3.0.0
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

## 📁 Struktur Modul

```
yhc_employee_export/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   ├── main.py
│   └── dashboard_controller.py
├── data/
│   └── export_data.xml
├── docs/
│   ├── PRD_Employee_Export_Analytics.md
│   ├── Prompt_Master.md
│   └── USER_GUIDE.md
├── models/
│   ├── __init__.py
│   ├── hr_employee_export_config.py
│   ├── hr_employee_export_template.py
│   ├── hr_employee_analytics.py
│   ├── export_audit_log.py
│   └── export_security_mixin.py
├── security/
│   ├── ir.model.access.csv
│   └── export_security.xml
├── services/
│   ├── __init__.py
│   ├── export_base.py
│   ├── export_xlsx.py
│   ├── export_csv.py
│   ├── export_json.py
│   ├── export_pdf.py
│   ├── export_bpjs_kes.py
│   ├── export_bpjs_tk.py
│   ├── export_spt.py
│   └── export_wlk.py
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       ├── js/
│       │   └── dashboard.js
│       └── css/
│           └── dashboard.css
├── tests/
│   ├── __init__.py
│   ├── test_export_config.py
│   ├── test_export_service.py
│   ├── test_dashboard.py
│   └── test_security.py
├── views/
│   ├── export_config_views.xml
│   ├── export_template_views.xml
│   ├── export_wizard_views.xml
│   ├── dashboard_templates.xml
│   ├── audit_log_views.xml
│   └── menu_views.xml
└── wizard/
    ├── __init__.py
    └── export_wizard.py
```

## 📝 Changelog

Lihat [CHANGELOG.md](CHANGELOG.md) untuk detail perubahan setiap versi.

## 👥 Author

YHC Development Team

## 📄 License

LGPL-3
