# Master Prompt: Pengembangan Module yhc_employee_export

## 🎯 KONTEKS PROYEK

Kamu adalah seorang Senior Odoo Developer yang ahli dalam pengembangan custom module Odoo 17. Kamu ditugaskan untuk membuat module baru bernama `yhc_employee_export` yang terintegrasi dengan module `yhc_employee` yang sudah ada.

### Informasi Proyek:
- **Nama Module**: `yhc_employee_export`
- **Versi Odoo**: 17.0
- **Lokasi**: `/home/or-abdillh/Desktop/Work/Odoo/custom-addons/yhc_employee_export/`
- **Dependency Utama**: `yhc_employee`, `hr`, `web`
- **Bahasa**: Python 3.10+, JavaScript (OWL), XML

### Module Referensi (`yhc_employee`):
Module ini meng-extend `hr.employee` dengan field tambahan:
- Data Identitas: `nrp`, `nik`, `nama_ktp`, `alamat_ktp`, `no_kk`, `no_akta_lahir`
- Data Demografis: `gender`, `age`, `religion`, `blood_type`, `status_kawin`
- Data Kepegawaian: `golongan_id`, `grade_id`, `employee_type_id`, `employee_category_id`, `area_kerja_id`, `employment_status`, `first_contract_date`, `service_length`
- Data Geografis: `kota_asal`, `provinsi_asal`
- Relasi: `bpjs_ids`, `education_ids`, `payroll_id`, `child_ids`, `training_certificate_ids`, `reward_punishment_ids`

---

## 📋 INSTRUKSI UMUM

1. **Ikuti standar Odoo 17**: Gunakan OWL framework untuk frontend, gunakan konvensi penamaan Odoo
2. **Kode harus production-ready**: Lengkap dengan error handling, logging, dan validasi
3. **Gunakan bahasa Indonesia** untuk label UI dan komentar kode
4. **Setiap file harus memiliki docstring** yang menjelaskan fungsinya
5. **Implementasi bertahap**: Fokus pada satu fitur sebelum pindah ke fitur lain
6. **Testing**: Sertakan unit test untuk setiap model dan method penting

---

## 🏗️ FASE PENGEMBANGAN

### FASE 1: Setup Struktur Dasar
**Prompt:**
```
Buatkan struktur dasar module yhc_employee_export dengan:
1. File __manifest__.py dengan metadata lengkap
2. File __init__.py untuk semua package
3. Struktur folder sesuai best practice Odoo 17
4. Security groups dan access rights dasar
5. Menu items untuk mengakses fitur

Pastikan module dapat diinstall tanpa error.
```

### FASE 2: Model Export Configuration
**Prompt:**
```
Buatkan model hr.employee.export.config dengan fitur:
1. Field untuk nama konfigurasi dan format export (xlsx, csv, pdf, json)
2. Boolean fields untuk memilih kategori data yang akan di-export:
   - include_identity (Data Identitas)
   - include_employment (Data Kepegawaian)
   - include_family (Data Keluarga)
   - include_bpjs (Data BPJS)
   - include_education (Data Pendidikan)
   - include_payroll (Data Payroll)
   - include_training (Data Pelatihan)
   - include_reward_punishment (Data Reward & Punishment)
3. Filter fields: department_ids (Many2many), employment_status, date_from, date_to
4. Method untuk menyimpan dan memuat konfigurasi
5. Views: form, tree, dan action
```

### FASE 3: Model Export Template
**Prompt:**
```
Buatkan model hr.employee.export.template untuk menyimpan template laporan:
1. Fields: name, code, template_type (selection), field_mapping (JSON)
2. Template types: demographic, employment, bpjs, education, payroll, family, training, reward_punishment, complete, regulatory
3. Pre-defined templates untuk setiap tipe (data XML)
4. Method untuk generate export berdasarkan template
5. Views dan menu untuk manajemen template
```

### FASE 4: Export Wizard
**Prompt:**
```
Buatkan wizard hr.employee.export.wizard dengan fitur:
1. Inherit dari TransientModel
2. Field untuk memilih:
   - Format export (xlsx, csv, pdf, json)
   - Template atau konfigurasi kustom
   - Filter departemen, status, tanggal
3. Method action_export() yang:
   - Mengumpulkan data karyawan sesuai filter
   - Memanggil service export sesuai format
   - Mengembalikan file untuk di-download
4. Button untuk preview data sebelum export
5. Opsi untuk menyimpan konfigurasi sebagai template baru
```

### FASE 5: Export Service - Excel
**Prompt:**
```
Buatkan service class EmployeeExportXlsx di file services/export_xlsx.py:
1. Gunakan library xlsxwriter
2. Method export_to_xlsx(employees, config) yang menghasilkan file xlsx
3. Multiple sheets berdasarkan kategori data:
   - Sheet "Identitas": NRP, Nama, NIK, TTL, Gender, Agama, dll
   - Sheet "Kepegawaian": Dept, Jabatan, Golongan, Grade, Status, Masa Kerja
   - Sheet "BPJS": Tipe BPJS, Nomor, Faskes
   - Sheet "Pendidikan": Jenjang, Institusi, Jurusan, Tahun
   - Sheet "Payroll": Bank, Rekening, NPWP
   - Sheet "Keluarga": Data pasangan dan anak
   - Sheet "Pelatihan": Nama, Jenis, Metode, Tanggal
   - Sheet "Reward & Punishment": Tipe, Nama, Tanggal, Keterangan
4. Formatting: header bold, auto-width columns, borders
5. Handle relational fields (One2many, Many2one)
```

### FASE 6: Export Service - CSV & JSON
**Prompt:**
```
Buatkan service untuk export CSV dan JSON:

1. EmployeeExportCsv (services/export_csv.py):
   - Method export_to_csv(employees, config)
   - Flatten nested data untuk format CSV
   - Handle encoding UTF-8 dengan BOM
   - Option untuk delimiter (comma, semicolon, tab)

2. EmployeeExportJson (services/export_json.py):
   - Method export_to_json(employees, config)
   - Struktur nested untuk relational data
   - Pretty print option
   - Date serialization ke ISO format
```

### FASE 7: Export Service - PDF
**Prompt:**
```
Buatkan fitur export PDF menggunakan QWeb report:
1. Report template XML untuk setiap tipe laporan:
   - report_employee_demographic.xml
   - report_employee_employment.xml
   - report_employee_bpjs.xml
   - report_employee_complete.xml
2. Controller untuk generate PDF
3. Styling yang profesional dengan:
   - Header perusahaan
   - Tanggal cetak
   - Pagination
   - Summary statistics
4. Landscape orientation untuk data yang lebar
```

### FASE 8: Format Regulasi
**Prompt:**
```
Buatkan export khusus untuk format regulasi Indonesia:

1. Format BPJS Kesehatan (services/export_bpjs_kes.py):
   - Sesuai format upload e-Dabu BPJS Kesehatan
   - Fields: NIK, Nama, TTL, JK, No BPJS, Kode Faskes, Kelas
   - Format CSV dengan delimiter pipe (|)

2. Format BPJS Ketenagakerjaan (services/export_bpjs_tk.py):
   - Sesuai format SIPP Online
   - Fields: NIK, Nama, TTL, No KPJ, Upah, Tanggal Masuk
   - Format CSV dengan delimiter semicolon

3. Validasi data sebelum export (NIK 16 digit, dll)
```

### FASE 9: Dashboard Analytics - Backend
**Prompt:**
```
Extend model hr.employee untuk menambahkan method analytics:

1. Method get_dashboard_data() yang mengembalikan:
   - Statistik demografis: gender_distribution, age_distribution, religion_distribution, marital_status_distribution
   - Statistik kepegawaian: department_distribution, grade_distribution, status_distribution, tenure_distribution
   - Statistik pendidikan: education_level_distribution, top_universities
   - Statistik pelatihan: training_by_type, training_by_method, training_trend
   - Summary: total_employees, active_employees, avg_age, avg_tenure

2. Method untuk setiap chart dengan parameter filter (department_id, date_range)

3. Optimasi query menggunakan read_group() untuk performa
```

### FASE 10: Dashboard Analytics - Frontend
**Prompt:**
```
Buatkan dashboard OWL component di static/src/:

1. File js/dashboard.js:
   - Component HrEmployeeDashboard extends Component
   - State untuk menyimpan data charts
   - Method loadDashboardData() memanggil backend
   - Method untuk render setiap chart menggunakan Chart.js

2. File xml/dashboard_templates.xml:
   - Template dengan layout grid
   - KPI cards di bagian atas (Total, Aktif, Avg Usia, Avg Masa Kerja)
   - 6 chart containers dalam 2 kolom
   - Filter dropdown untuk departemen
   - Button export dashboard ke PDF/image

3. File css/dashboard.css:
   - Styling modern dan responsif
   - Warna sesuai branding Odoo
   - Animation untuk loading state

4. Registry action di views/dashboard_views.xml
```

### FASE 11: Controller API
**Prompt:**
```
Buatkan controller di controllers/export_controller.py:

1. Route /hr/employee/export untuk download file
2. Route /hr/employee/dashboard/data untuk AJAX data
3. Route /hr/employee/export/preview untuk preview data
4. Authentication dan authorization check
5. Streaming response untuk file besar
6. Error handling dengan proper HTTP status codes
```

### FASE 12: Security & Access Rights
**Prompt:**
```
Implementasikan security lengkap:

1. Groups di security/export_security.xml:
   - group_hr_export_user: Akses dashboard dan export basic
   - group_hr_export_officer: + Export data sensitif
   - group_hr_export_manager: + Export format regulasi

2. Access rights di security/ir.model.access.csv untuk semua model baru

3. Record rules untuk membatasi akses berdasarkan department

4. Field-level security untuk data sensitif (NIK, NPWP, rekening)
```

### FASE 13: Data Default & Demo
**Prompt:**
```
Buatkan data default di folder data/:

1. export_template_data.xml:
   - 10 template laporan default sesuai PRD
   - Mapping field untuk setiap template

2. export_config_demo.xml (hanya untuk mode demo):
   - Contoh konfigurasi export
   - Sample data untuk testing
```

### FASE 14: Testing
**Prompt:**
```
Buatkan unit tests di folder tests/:

1. test_export_config.py:
   - Test create/read/update/delete config
   - Test filter functionality

2. test_export_service.py:
   - Test export xlsx dengan berbagai konfigurasi
   - Test export csv dan json
   - Test format regulasi

3. test_dashboard.py:
   - Test method get_dashboard_data
   - Test agregasi data

4. test_security.py:
   - Test access rights per group
```

### FASE 15: Documentation
**Prompt:**
```
Buatkan dokumentasi lengkap:

1. README.md:
   - Deskripsi module
   - Cara instalasi
   - Konfigurasi
   - Panduan penggunaan
   - Screenshots

2. CHANGELOG.md:
   - Version history

3. Inline documentation:
   - Docstring untuk semua class dan method
   - Komentar untuk logic kompleks
```

### FASE 16: Export Grafik Dashboard ke PDF (Graph-based PDF Export)
**Prompt**
```
Fase ini tidak menggantikan export PDF berbasis tabel (FASE 7), tetapi melengkapinya.

🎯 Tujuan Fase

1. Menyediakan fitur export PDF berbasis grafik (chart) yang:

2. Menggunakan data & visual yang sama dengan dashboard

3. Memungkinkan user memilih grafik apa saja

4. Memungkinkan user mengatur data scope & filter

5. Menghasilkan PDF siap presentasi / laporan eksekutif
```

#### 16.1 Model: Export Graph Configuration
**Prompt**
```
Tambahkan fitur baru: Export Grafik Dashboard ke PDF
sebagai bagian dari module yhc_employee_export.

Fokus utama:
- Export PDF berbasis grafik (chart), bukan tabel
- Grafik diambil dari data analytics dashboard
- User dapat memilih grafik & dataset secara fleksibel

Implementasikan dengan spesifikasi berikut:

Buatkan model baru hr.employee.export.graph.config:

Fields:
1. name (Char) - Nama konfigurasi export grafik
2. graph_ids (Many2many ke graph definition)
3. export_format (Selection) default: pdf
4. layout_type (Selection):
   - single_column
   - two_columns
   - executive_summary
5. include_summary (Boolean):
   - Ringkasan angka di awal PDF
6. filter_department_ids (Many2many hr.department)
7. date_from, date_to
8. active (Boolean)

Tambahkan validasi:
- Minimal 1 grafik harus dipilih
- Maksimal 8 grafik per PDF (default)
```

#### 16.2 Graph Definition Registry
**Prompt**
```
Buatkan registry grafik terpusat (Python):

GRAPH_REGISTRY = {
  'G01': {
    'name': 'Distribusi Gender',
    'chart_type': 'pie',
    'method': 'get_gender_distribution',
    'description': 'Komposisi gender karyawan'
  },
  'G02': {
    'name': 'Distribusi Usia',
    'chart_type': 'bar',
    'method': 'get_age_distribution'
  },
  ...
}

Registry ini harus:
- Digunakan oleh dashboard
- Digunakan oleh export PDF grafik
- Single source of truth
```

#### 16.3 Wizard: Export Graph to PDF
**Prompt**
```
Buatkan wizard hr.employee.export.graph.wizard:

Fitur:
1. Checklist pilihan grafik (dari GRAPH_REGISTRY)
2. Preview mini chart (thumbnail / label info)
3. Filter data:
   - Departemen
   - Status kepegawaian
   - Range tanggal
4. Pilihan layout PDF
5. Opsi simpan sebagai template konfigurasi

Button:
- Preview PDF
- Export PDF
```

#### 16.4 Chart Rendering Service (Image-based)
**Prompt**
```
Buatkan service services/export_graph_pdf.py:

Flow:
1. Ambil data analytics dari hr.employee
2. Render grafik ke image (PNG/SVG):
   - Gunakan Chart.js headless / rendering backend
   - Atau matplotlib sebagai fallback
3. Simpan grafik sementara (in-memory / temp)
4. Inject grafik ke QWeb PDF template

Output:
- PDF dengan grafik resolusi tinggi
- Siap dicetak (A4 / Landscape)
```

#### 16.5 QWeb PDF Template – Graph Report
**Prompt**
```
Buatkan QWeb report baru:

report_employee_graph_analytics.xml

Struktur:
1. Cover Page
   - Judul laporan
   - Periode data
   - Filter aktif
2. Executive Summary
   - Total karyawan
   - Aktif vs non-aktif
   - Rata-rata usia & masa kerja
3. Section Grafik
   - Judul grafik
   - Deskripsi singkat
   - Gambar chart
4. Footer
   - Generated by system
   - Tanggal & user
```

#### 16.6 Security & Performance
**Prompt**
```
Pastikan:
1. Akses hanya untuk group_hr_export_manager ke atas
2. Cache data analytics selama proses export
3. Pagination grafik jika > batas maksimal
4. Error handling jika grafik gagal dirender
```

#### 16.7 Testing
**Prompt**
```
Tambahkan test:
1. test_export_graph_pdf.py
   - Validasi pilihan grafik
   - Validasi filter
   - Validasi file PDF terbentuk
2. Test konsistensi data:
   - Dashboard vs PDF harus sama
```
---

## 🔧 PANDUAN TEKNIS

### Konvensi Penamaan:
- Model: `hr.employee.export.config`, `hr.employee.export.template`
- Wizard: `hr.employee.export.wizard`
- Views: `view_hr_employee_export_config_form`, `view_hr_employee_export_config_tree`
- Actions: `action_hr_employee_export_config`, `action_hr_employee_dashboard`
- Menu: `menu_hr_employee_export`, `menu_hr_employee_dashboard`

### Import Pattern:
```python
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
```

### Error Handling:
```python
try:
    # operation
except Exception as e:
    _logger.error(f"Error during export: {str(e)}")
    raise UserError(_("Gagal melakukan export: %s") % str(e))
```

### Chart.js Usage:
```javascript
new Chart(ctx, {
    type: 'pie', // atau 'bar', 'line', 'doughnut'
    data: {
        labels: [...],
        datasets: [{
            data: [...],
            backgroundColor: [...]
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { position: 'bottom' }
        }
    }
});
```

---

## ✅ CHECKLIST DELIVERABLES

Setelah semua fase selesai, pastikan:

- [ ] Module dapat diinstall tanpa error
- [ ] Semua menu dan action dapat diakses
- [ ] Dashboard menampilkan 6+ grafik dengan benar
- [ ] Export Excel menghasilkan file dengan multiple sheets
- [ ] Export CSV dan JSON berfungsi
- [ ] Export PDF menghasilkan laporan yang rapi
- [ ] Format BPJS sesuai standar
- [ ] Security groups berfungsi sesuai level akses
- [ ] Unit tests passed
- [ ] Dokumentasi lengkap

---

## 📞 CATATAN PENTING

1. **Jangan modifikasi module yhc_employee** - Semua perubahan harus di module baru
2. **Gunakan _inherit untuk extend** - Jika perlu menambah method di hr.employee
3. **Performa adalah prioritas** - Gunakan read_group, batch processing untuk data besar
4. **Backward compatible** - Pastikan tidak break existing functionality
5. **Translate-ready** - Gunakan _() untuk semua string yang akan ditampilkan

---

*Gunakan prompt ini secara bertahap sesuai fase pengembangan. Setiap fase harus di-test sebelum lanjut ke fase berikutnya.*