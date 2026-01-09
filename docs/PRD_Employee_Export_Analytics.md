# Product Requirements Document (PRD)
## HR Employee Export & Analytics Module

---

## 1. Executive Summary

### 1.1 Latar Belakang

Berdasarkan analisis mendalam terhadap custom module `yhc_employee`, modul ini merupakan ekstensi komprehensif dari modul HR bawaan Odoo yang mencakup:

- **Data Identitas Lengkap**: KTP, KK, Akta Kelahiran
- **Data Ketenagakerjaan**: NRP, jabatan, golongan, grade, status kepegawaian
- **Data Keluarga**: Suami/istri, anak, orang tua, mertua
- **Data BPJS**: Kesehatan dan Ketenagakerjaan
- **Data Pendidikan**: Riwayat pendidikan dari SD hingga S3
- **Data Payroll**: Rekening bank, NPWP, EFIN
- **Data Reward & Punishment**: Penghargaan dan sanksi
- **Data Pelatihan**: Sertifikat dan riwayat pelatihan

### 1.2 Tujuan

Membuat custom addon baru bernama `yhc_employee_export` yang menyediakan:
1. Visualisasi data karyawan dalam bentuk grafik/dashboard
2. Fitur export data ke berbagai format standar perusahaan besar
3. Template laporan yang customizable

---

## 2. Analisis Data Model `yhc_employee`

### 2.1 Model Utama

| Model | Deskripsi | Field Kunci untuk Export |
|-------|-----------|--------------------------|
| `hr.employee` | Data utama karyawan | `nrp`, `nik`, `employment_status`, `age`, `service_length`, `golongan_id`, `grade_id` |
| `hr.employee.bpjs` | Data BPJS | `bpjs_type`, `number`, `faskes_tk1` |
| `hr.employee.education` | Riwayat pendidikan | `certificate`, `study_school`, `major` |
| `hr.employee.payroll` | Data payroll | `bank_name`, `bank_account` |
| `hr.employee.reward.punishment` | Reward & Punishment | `type`, `reward_category`, `punishment_category` |
| `hr.training.certificate` | Sertifikat pelatihan | `name`, `jenis_pelatihan`, `metode` |
| `yhc.employee.child` | Data anak | `name`, `birth_date`, `gender` |

### 2.2 Field Kritis untuk Analitik

```
Demografis:
- gender, age, religion, blood_type
- status_kawin, jlh_anggota_keluarga

Ketenagakerjaan:
- department_id, job_id, area_kerja_id
- golongan_id, grade_id, employee_type_id, employee_category_id
- employment_status, first_contract_date, service_length

Geografis:
- kota_asal, provinsi_asal

Pendidikan:
- education_ids.certificate (agregasi level pendidikan)
```

---

## 3. Fitur yang Diusulkan

### 3.1 Dashboard & Grafik

#### 3.1.1 Grafik Demografis
| ID | Nama Grafik | Tipe | Deskripsi |
|----|-------------|------|-----------|
| G01 | Distribusi Gender | Pie Chart | Perbandingan karyawan pria vs wanita |
| G02 | Distribusi Usia | Bar Chart | Pengelompokan usia (20-25, 26-30, dst) |
| G03 | Distribusi Agama | Pie Chart | Komposisi agama karyawan |
| G04 | Status Pernikahan | Pie Chart | Kawin, Lajang, Cerai |
| G05 | Golongan Darah | Pie Chart | Distribusi golongan darah |

#### 3.1.2 Grafik Ketenagakerjaan
| ID | Nama Grafik | Tipe | Deskripsi |
|----|-------------|------|-----------|
| G06 | Karyawan per Departemen | Bar Chart | Jumlah karyawan tiap unit kerja |
| G07 | Karyawan per Area Kerja | Bar Chart | Distribusi berdasarkan area kerja |
| G08 | Distribusi Golongan | Bar Chart | Jumlah per golongan pegawai |
| G09 | Distribusi Grade | Bar Chart | Jumlah per grade/pangkat |
| G10 | Status Kepegawaian | Pie Chart | Aktif, Non-aktif, Pensiun |
| G11 | Jenis Pegawai | Pie Chart | Berdasarkan employee_category_id |
| G12 | Tipe Pegawai | Pie Chart | Berdasarkan employee_type_id |
| G13 | Masa Kerja | Bar Chart | Pengelompokan (0-5th, 6-10th, dst) |
| G14 | Trend Rekrutmen | Line Chart | Jumlah masuk per bulan/tahun |
| G15 | Trend Terminasi | Line Chart | Jumlah keluar per bulan/tahun |

#### 3.1.3 Grafik Pendidikan
| ID | Nama Grafik | Tipe | Deskripsi |
|----|-------------|------|-----------|
| G16 | Level Pendidikan | Bar Chart | Distribusi SD-S3 |
| G17 | Top Universitas | Horizontal Bar | 10 universitas terbanyak |

#### 3.1.4 Grafik Geografis
| ID | Nama Grafik | Tipe | Deskripsi |
|----|-------------|------|-----------|
| G18 | Karyawan per Provinsi | Map/Bar | Distribusi berdasarkan provinsi asal |
| G19 | Karyawan per Kota | Bar Chart | Top 10 kota asal |

#### 3.1.5 Grafik Pelatihan & Reward
| ID | Nama Grafik | Tipe | Deskripsi |
|----|-------------|------|-----------|
| G20 | Pelatihan per Jenis | Pie Chart | Internal, Eksternal, Teknis, Nonteknis |
| G21 | Pelatihan per Metode | Pie Chart | Tatap Muka, Daring, Blended |
| G22 | Trend Pelatihan | Line Chart | Jumlah pelatihan per bulan |
| G23 | Reward vs Punishment | Stacked Bar | Perbandingan per periode |

### 3.2 Format Export

#### 3.2.1 Export Standar
| ID | Format | Deskripsi | Use Case |
|----|--------|-----------|----------|
| E01 | Excel (.xlsx) | Export lengkap dengan multiple sheets | Analisis HR, audit |
| E02 | CSV | Export sederhana | Import ke sistem lain |
| E03 | PDF | Laporan formal | Dokumentasi, presentasi |
| E04 | JSON | Data terstruktur | Integrasi API |

#### 3.2.2 Template Laporan Perusahaan
| ID | Template | Deskripsi |
|----|----------|-----------|
| T01 | Laporan Demografi Karyawan | Ringkasan demografis (gender, usia, agama, status) |
| T02 | Laporan Kepegawaian | Status, golongan, grade, masa kerja |
| T03 | Laporan BPJS | Daftar kepesertaan BPJS |
| T04 | Laporan Pendidikan | Riwayat pendidikan seluruh karyawan |
| T05 | Laporan Payroll | Data rekening untuk kebutuhan payroll |
| T06 | Laporan Keluarga | Data tanggungan untuk asuransi/pajak |
| T07 | Laporan Pelatihan | Rekap pelatihan per karyawan/departemen |
| T08 | Laporan Reward & Punishment | Rekap R&P per periode |
| T09 | Laporan Masa Kerja | Proyeksi pensiun, anniversary |
| T10 | Laporan Karyawan Lengkap | Master data seluruh karyawan |

#### 3.2.3 Export Khusus Regulasi
| ID | Template | Deskripsi |
|----|----------|-----------|
| R01 | Format BPJS Kesehatan | Sesuai format upload BPJS Kesehatan |
| R02 | Format BPJS Ketenagakerjaan | Sesuai format upload BPJS TK |
| R03 | Format Pajak (1721-A1) | Data untuk pelaporan pajak |
| R04 | Format Wajib Lapor Ketenagakerjaan | Sesuai format Disnaker |

---

## 4. Spesifikasi Teknis

### 4.1 Struktur Addon

```
yhc_employee_export/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── export_controller.py          # API endpoint untuk export
├── models/
│   ├── __init__.py
│   ├── export_config.py              # Konfigurasi export
│   ├── export_template.py            # Template laporan
│   └── hr_employee_analytics.py      # Model untuk agregasi data
├── wizards/
│   ├── __init__.py
│   ├── export_wizard.py              # Wizard export data
│   └── report_wizard.py              # Wizard generate laporan
├── reports/
│   ├── employee_demographic_report.xml
│   ├── employee_payroll_report.xml
│   ├── employee_bpjs_report.xml
│   └── ...
├── security/
│   ├── ir.model.access.csv
│   └── export_security.xml
├── static/
│   ├── src/
│   │   ├── js/
│   │   │   └── dashboard.js          # Dashboard component
│   │   ├── css/
│   │   │   └── dashboard.css
│   │   └── xml/
│   │       └── dashboard_templates.xml
│   └── description/
│       └── icon.png
├── views/
│   ├── dashboard_views.xml           # Dashboard utama
│   ├── export_config_views.xml       # Konfigurasi
│   ├── export_wizard_views.xml       # Wizard
│   └── menu_views.xml                # Menu items
└── data/
    └── export_template_data.xml      # Default templates
```

### 4.2 Model Baru

#### 4.2.1 `hr.employee.export.config`
```python
class HrEmployeeExportConfig(models.Model):
    _name = 'hr.employee.export.config'
    _description = 'Konfigurasi Export Karyawan'

    name = fields.Char(string='Nama Konfigurasi', required=True)
    export_type = fields.Selection([
        ('xlsx', 'Excel (.xlsx)'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
    ], string='Format Export', required=True, default='xlsx')
    
    # Field selection untuk export
    include_identity = fields.Boolean('Data Identitas', default=True)
    include_employment = fields.Boolean('Data Kepegawaian', default=True)
    include_family = fields.Boolean('Data Keluarga', default=False)
    include_bpjs = fields.Boolean('Data BPJS', default=False)
    include_education = fields.Boolean('Data Pendidikan', default=False)
    include_payroll = fields.Boolean('Data Payroll', default=False)
    include_training = fields.Boolean('Data Pelatihan', default=False)
    include_reward_punishment = fields.Boolean('Data Reward & Punishment', default=False)
    
    # Filter
    department_ids = fields.Many2many('hr.department', string='Departemen')
    employment_status = fields.Selection([...], string='Status Kepegawaian')
    date_from = fields.Date('Dari Tanggal')
    date_to = fields.Date('Sampai Tanggal')
```

#### 4.2.2 `hr.employee.export.template`
```python
class HrEmployeeExportTemplate(models.Model):
    _name = 'hr.employee.export.template'
    _description = 'Template Export Karyawan'

    name = fields.Char(string='Nama Template', required=True)
    code = fields.Char(string='Kode Template', required=True)
    template_type = fields.Selection([
        ('demographic', 'Demografi'),
        ('employment', 'Kepegawaian'),
        ('bpjs', 'BPJS'),
        ('education', 'Pendidikan'),
        ('payroll', 'Payroll'),
        ('family', 'Keluarga'),
        ('training', 'Pelatihan'),
        ('reward_punishment', 'Reward & Punishment'),
        ('complete', 'Lengkap'),
        ('regulatory', 'Regulasi'),
    ], string='Tipe Template', required=True)
    
    field_ids = fields.Many2many('ir.model.fields', string='Fields')
    header_mapping = fields.Text('Header Mapping (JSON)')
    active = fields.Boolean(default=True)
```

### 4.3 Dashboard Component

```javascript
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class HrEmployeeDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            demographicData: {},
            employmentData: {},
            trainingData: {},
            loading: true,
        });
        
        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }
    
    async loadDashboardData() {
        // Load aggregated data dari server
        const data = await this.orm.call(
            "hr.employee",
            "get_dashboard_data",
            []
        );
        this.state.demographicData = data.demographic;
        this.state.employmentData = data.employment;
        this.state.trainingData = data.training;
        this.state.loading = false;
    }
}
```

### 4.4 Export Service

```python
class EmployeeExportService:
    """Service untuk handle export data karyawan"""
    
    def export_to_xlsx(self, employees, config):
        """Export ke format Excel dengan multiple sheets"""
        workbook = xlsxwriter.Workbook(output)
        
        if config.include_identity:
            self._write_identity_sheet(workbook, employees)
        if config.include_employment:
            self._write_employment_sheet(workbook, employees)
        if config.include_bpjs:
            self._write_bpjs_sheet(workbook, employees)
        # ... dst
        
        return workbook
    
    def export_to_pdf(self, employees, template):
        """Export ke format PDF menggunakan QWeb report"""
        pass
    
    def export_regulatory_format(self, employees, format_type):
        """Export sesuai format regulasi (BPJS, Pajak, dll)"""
        pass
```

---

## 5. User Stories

### 5.1 HR Manager
| ID | User Story | Priority |
|----|------------|----------|
| US01 | Sebagai HR Manager, saya ingin melihat dashboard demografi karyawan agar dapat memahami komposisi SDM | High |
| US02 | Sebagai HR Manager, saya ingin export data karyawan ke Excel untuk analisis lebih lanjut | High |
| US03 | Sebagai HR Manager, saya ingin melihat trend rekrutmen dan terminasi | Medium |
| US04 | Sebagai HR Manager, saya ingin generate laporan BPJS sesuai format resmi | High |

### 5.2 HR Staff
| ID | User Story | Priority |
|----|------------|----------|
| US05 | Sebagai HR Staff, saya ingin export data payroll untuk proses penggajian | High |
| US06 | Sebagai HR Staff, saya ingin export data pelatihan per departemen | Medium |
| US07 | Sebagai HR Staff, saya ingin menyimpan konfigurasi export yang sering digunakan | Medium |

### 5.3 Management
| ID | User Story | Priority |
|----|------------|----------|
| US08 | Sebagai Management, saya ingin melihat ringkasan jumlah karyawan per departemen | High |
| US09 | Sebagai Management, saya ingin laporan PDF yang rapi untuk presentasi | Medium |

---

## 6. Wireframe & Mockup

### 6.1 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  HR Employee Analytics Dashboard                          [⚙️]  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ Total       │ │ Aktif       │ │ Rata-rata   │ │ Avg Masa   │ │
│  │ Karyawan    │ │             │ │ Usia        │ │ Kerja      │ │
│  │    245      │ │    230      │ │   32 thn    │ │  5.2 thn   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────┐  ┌───────────────────────────┐   │
│  │   Gender Distribution     │  │   Age Distribution        │   │
│  │      [PIE CHART]          │  │     [BAR CHART]           │   │
│  │   ● Pria: 150 (61%)       │  │  20-25 ████░░ 45          │   │
│  │   ● Wanita: 95 (39%)      │  │  26-30 ██████ 78          │   │
│  │                           │  │  31-35 ████░░ 52          │   │
│  └───────────────────────────┘  └───────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────┐  ┌───────────────────────────┐   │
│  │   Karyawan per Dept       │  │   Status Kepegawaian      │   │
│  │     [BAR CHART]           │  │      [PIE CHART]          │   │
│  │  IT      ██████████ 45    │  │   ● Aktif: 230            │   │
│  │  HR      ████░░░░░░ 20    │  │   ● Non-aktif: 10         │   │
│  │  Finance ██████░░░░ 30    │  │   ● Pensiun: 5            │   │
│  └───────────────────────────┘  └───────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  [📊 Export Dashboard] [📄 Generate Report] [⚙️ Settings]       │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Export Wizard

```
┌─────────────────────────────────────────────────────────────────┐
│  Export Data Karyawan                                     [X]   │
├─────────────────────────────────────────────────────────────────┤
│  Format Export:  [Excel ▼]                                      │
│                                                                 │
│  ┌─ Data yang diekspor ────────────────────────────────────┐    │
│  │  ☑ Data Identitas (KTP, KK, Akta)                       │    │
│  │  ☑ Data Kepegawaian (NRP, Jabatan, Golongan)            │    │
│  │  ☐ Data Keluarga (Suami/Istri, Anak)                    │    │
│  │  ☐ Data BPJS                                            │    │
│  │  ☐ Data Pendidikan                                      │    │
│  │  ☑ Data Payroll                                         │    │
│  │  ☐ Data Pelatihan                                       │    │
│  │  ☐ Data Reward & Punishment                             │    │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─ Filter ────────────────────────────────────────────────┐    │
│  │  Departemen:      [Semua ▼]                             │    │
│  │  Status:          [Aktif ▼]                             │    │
│  │  Area Kerja:      [Semua ▼]                             │    │
│  │  Tanggal Masuk:   [01/01/2020] s/d [31/12/2024]         │    │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ☐ Simpan sebagai template                                      │
│  Nama template: [_____________________________]                 │
│                                                                 │
│              [Batal]  [Preview]  [Export]                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Acceptance Criteria

### 7.1 Dashboard

| ID | Kriteria | Status |
|----|----------|--------|
| AC01 | Dashboard menampilkan minimal 6 grafik berbeda | ⬜ |
| AC02 | Data grafik real-time dari database | ⬜ |
| AC03 | Grafik dapat di-filter berdasarkan departemen | ⬜ |
| AC04 | Dashboard load dalam waktu < 3 detik | ⬜ |
| AC05 | Grafik responsif di berbagai ukuran layar | ⬜ |

### 7.2 Export

| ID | Kriteria | Status |
|----|----------|--------|
| AC06 | Export ke Excel dengan multiple sheets berfungsi | ⬜ |
| AC07 | Export ke CSV berfungsi | ⬜ |
| AC08 | Export ke PDF dengan format rapi | ⬜ |
| AC09 | Filter export berfungsi dengan benar | ⬜ |
| AC10 | Template export dapat disimpan dan digunakan kembali | ⬜ |
| AC11 | Export data > 1000 karyawan dalam < 30 detik | ⬜ |

### 7.3 Laporan Regulasi

| ID | Kriteria | Status |
|----|----------|--------|
| AC12 | Format BPJS Kesehatan sesuai standar | ⬜ |
| AC13 | Format BPJS TK sesuai standar | ⬜ |
| AC14 | Format dapat diupload langsung ke sistem terkait | ⬜ |

---

## 8. Dependencies

### 8.1 Module Dependencies

```python
"depends": [
    "yhc_employee",      # Custom module yang sudah ada
    "hr",                # Odoo HR base
    "web",               # Untuk dashboard
    "report_xlsx",       # Untuk export Excel (OCA)
]
```

### 8.2 Python Dependencies

```
xlsxwriter>=3.0.0
pandas>=1.3.0
openpyxl>=3.0.0
```

### 8.3 JavaScript Dependencies

```
Chart.js (sudah include di Odoo)
```

---

## 9. Security & Access Rights

### 9.1 Groups

| Group | Akses Dashboard | Export Basic | Export Sensitive | Export Regulatory |
|-------|-----------------|--------------|------------------|-------------------|
| HR User | ✅ | ✅ | ❌ | ❌ |
| HR Officer | ✅ | ✅ | ✅ | ❌ |
| HR Manager | ✅ | ✅ | ✅ | ✅ |
| System Admin | ✅ | ✅ | ✅ | ✅ |

### 9.2 Sensitive Data

Data berikut dikategorikan sebagai sensitif:
- NIK, No. KK
- Data BPJS
- Data Payroll (rekening bank, NPWP)
- Data Reward & Punishment

---

## 10. Timeline & Milestones

| Phase | Deliverable | Durasi | Target |
|-------|-------------|--------|--------|
| 1 | Setup struktur addon & model dasar | 3 hari | Week 1 |
| 2 | Dashboard dengan 6 grafik utama | 5 hari | Week 2 |
| 3 | Export Excel & CSV | 4 hari | Week 3 |
| 4 | Export PDF & template laporan | 5 hari | Week 4 |
| 5 | Format regulasi (BPJS, Pajak) | 4 hari | Week 5 |
| 6 | Testing & bug fixing | 3 hari | Week 5-6 |
| 7 | Documentation & deployment | 2 hari | Week 6 |

**Total Estimasi: 26 hari kerja (± 6 minggu)**

---

## 11. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performa lambat untuk data besar | High | Medium | Implementasi pagination, caching |
| Format regulasi berubah | Medium | Low | Desain template yang flexible |
| Integrasi dengan yhc_employee | Medium | Low | Unit testing komprehensif |
| Browser compatibility | Low | Medium | Testing di Chrome, Firefox, Edge |

---

## 12. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Dashboard load time | < 3 detik | Performance monitoring |
| Export success rate | > 99% | Error logging |
| User adoption | 80% HR team | Usage analytics |
| Report accuracy | 100% | Manual verification |

---

## 13. Appendix

### 13.1 Mapping Field yhc_employee ke Export Columns

```python
EXPORT_FIELD_MAPPING = {
    'identity': {
        'nrp': 'NRP',
        'name': 'Nama Lengkap',
        'gelar': 'Gelar',
        'nama_ktp': 'Nama KTP',
        'nik': 'NIK',
        'alamat_ktp': 'Alamat KTP',
        'place_of_birth': 'Tempat Lahir',
        'birthday': 'Tanggal Lahir',
        'age': 'Usia',
        'gender': 'Jenis Kelamin',
        'blood_type': 'Golongan Darah',
        'religion': 'Agama',
    },
    'employment': {
        'department_id.name': 'Unit Kerja',
        'job_id.name': 'Jabatan',
        'area_kerja_id.name': 'Area Kerja',
        'golongan_id.name': 'Golongan',
        'grade_id.name': 'Grade',
        'employee_type_id.name': 'Tipe Pegawai',
        'employee_category_id.name': 'Jenis Pegawai',
        'employment_status': 'Status',
        'first_contract_date': 'Tanggal Masuk',
        'service_length': 'Masa Kerja (Tahun)',
    },
    'family': {
        'spouse_name': 'Nama Pasangan',
        'spouse_nik': 'NIK Pasangan',
        'spouse_birthday': 'Tanggal Lahir Pasangan',
        'jlh_anggota_keluarga': 'Jumlah Anggota Keluarga',
        'child_ids': 'Data Anak',
    },
    'bpjs': {
        'bpjs_ids.bpjs_type': 'Jenis BPJS',
        'bpjs_ids.number': 'Nomor BPJS',
        'bpjs_ids.faskes_tk1': 'Faskes Tingkat 1',
    },
    'education': {
        'education_ids.certificate': 'Jenjang',
        'education_ids.study_school': 'Institusi',
        'education_ids.major': 'Jurusan',
        'education_ids.date_start': 'Tahun Masuk',
        'education_ids.date_end': 'Tahun Lulus',
    },
    'payroll': {
        'payroll_id.bank_name': 'Nama Bank',
        'payroll_id.bank_account': 'Nomor Rekening',
        'payroll_id.npwp': 'NPWP',
        'payroll_id.efin': 'EFIN',
    },
    'training': {
        'training_certificate_ids.name': 'Nama Pelatihan',
        'training_certificate_ids.jenis_pelatihan': 'Jenis Pelatihan',
        'training_certificate_ids.metode': 'Metode',
        'training_certificate_ids.date_start': 'Tanggal Mulai',
        'training_certificate_ids.date_end': 'Tanggal Selesai',
    },
    'reward_punishment': {
        'reward_punishment_ids.type': 'Tipe',
        'reward_punishment_ids.name': 'Nama',
        'reward_punishment_ids.date': 'Tanggal',
        'reward_punishment_ids.description': 'Keterangan',
    },
}
```

### 13.2 Format Export Regulasi

#### Format BPJS Kesehatan
| No | Field | Panjang | Keterangan |
|----|-------|---------|------------|
| 1 | NIK | 16 | Nomor Induk Kependudukan |
| 2 | Nama | 50 | Nama Lengkap |
| 3 | Tanggal Lahir | 10 | Format DD-MM-YYYY |
| 4 | Jenis Kelamin | 1 | L/P |
| 5 | No. BPJS | 13 | Nomor Kepesertaan |
| 6 | Faskes | 8 | Kode Faskes TK1 |
| 7 | Kelas | 1 | 1/2/3 |

#### Format BPJS Ketenagakerjaan
| No | Field | Panjang | Keterangan |
|----|-------|---------|------------|
| 1 | NIK | 16 | Nomor Induk Kependudukan |
| 2 | Nama | 50 | Nama Lengkap |
| 3 | Tanggal Lahir | 10 | Format DD-MM-YYYY |
| 4 | No. KPJ | 11 | Nomor Kepesertaan |
| 5 | Gaji Pokok | 15 | Dalam Rupiah |
| 6 | Tanggal Masuk | 10 | Format DD-MM-YYYY |

---

## 14. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-09 | Development Team | Initial PRD |

---

**Dokumen ini dibuat sebagai panduan pengembangan module `yhc_employee_export`.**

*Version: 1.0*  
*Last Updated: 2026-01-09*  
*Author: Development Team*
