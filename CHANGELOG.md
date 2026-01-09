# Changelog

Semua perubahan penting pada module ini akan didokumentasikan di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
dan project ini mengikuti [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [17.0.1.0.0] - 2025-01-15

### Added

#### Fase 1-2: Struktur Dasar & Security
- Inisialisasi struktur module untuk Odoo 17
- Manifest file dengan metadata lengkap
- Security groups:
  - `group_export_user`: Akses dasar export
  - `group_export_officer`: Manajemen template
  - `group_export_manager`: Full access
  - `group_sensitive_data`: Akses data sensitif (NPWP, gaji)
  - `group_regulatory_export`: Akses export regulasi
- Model access rights (ir.model.access.csv)
- Record rules untuk pembatasan akses per company

#### Fase 3-4: Export Config & Template
- Model `hr.employee.export.config`:
  - Konfigurasi export yang dapat disimpan
  - Field selection dengan many2many
  - Domain filter untuk filtering karyawan
  - Active/inactive state management
- Model `hr.employee.export.template`:
  - Template export berbasis konfigurasi
  - Header styling options
  - Sharing antar pengguna
- Wizard `hr.employee.export.wizard`:
  - Transient model untuk proses export
  - Multi-format selection
  - Employee selection

#### Fase 5-6: Export Services
- Service `ExportBase`:
  - Base class untuk semua export services
  - Format value helpers
  - Date formatting
  - Security validation integration
- Service `ExportXLSX`:
  - Export ke format Excel (.xlsx)
  - Header styling
  - Auto column width
  - Multiple sheets support
- Service `ExportCSV`:
  - Export ke format CSV
  - Configurable delimiter
  - Encoding options
- Service `ExportJSON`:
  - Export ke format JSON
  - Pretty print option
  - Nested object support
- Service `ExportPDF`:
  - Export ke format PDF
  - QWeb template integration
  - Professional layout

#### Fase 7-8: Regulatory Exports & API
- Service `ExportBPJSKes`:
  - Format sesuai standar BPJS Kesehatan
  - Field mapping untuk nomor BPJS, kelas, dll
- Service `ExportBPJSTK`:
  - Format untuk BPJS Ketenagakerjaan
  - Perhitungan iuran JHT, JP, JKK, JKM
- Service `ExportSPT`:
  - Format untuk pelaporan SPT Tahunan
  - Data NPWP dan penghasilan
- Service `ExportWLK`:
  - Format Wajib Lapor Ketenagakerjaan
  - Sesuai format Disnaker
- REST API Controllers:
  - `/api/v1/employee-export/export` - Export endpoint
  - `/api/v1/employee-export/configs` - Config management
  - `/api/v1/employee-export/templates` - Template management
  - Authentication dengan Bearer token

#### Fase 9-10: Dashboard Analytics
- Model `hr.employee.analytics`:
  - Transient model untuk analytics
  - Method `get_dashboard_data()` untuk semua metrics
  - KPI calculations (total, active, contract, turnover)
  - Distribution calculations (gender, age, department, dll)
- OWL Component `EmployeeDashboard`:
  - Reactive dashboard dengan Chart.js 4.4.1
  - 8 jenis chart interaktif
  - Filter departemen
  - Date range selector
  - Auto-refresh data
- Dashboard Templates:
  - QWeb templates untuk layout
  - Responsive design
  - Dark mode support
- Dashboard CSS:
  - Modern styling
  - Card components
  - Chart containers
  - Loading states
- Controller `DashboardController`:
  - `/api/v1/employee-export/dashboard` endpoint
  - JSON data untuk charts

#### Fase 11-12: Security & Audit
- Model `export.audit.log`:
  - Logging semua aktivitas export
  - User tracking
  - Timestamp
  - Export details (format, count, duration)
  - IP address logging
- Mixin `ExportSecurityMixin`:
  - Validation methods
  - `_check_export_access()`
  - `_filter_sensitive_fields()`
  - `_mask_sensitive_value()`
  - `_check_regulatory_access()`
- Enhanced record rules:
  - Audit log access control
  - Config access per creator
  - Template sharing rules
- Views `audit_log_views.xml`:
  - Tree view untuk log list
  - Form view untuk detail
  - Search filters
  - Dashboard action

#### Fase 13-15: Testing & Documentation
- Unit Tests:
  - `test_export_config.py`: Test model konfigurasi
  - `test_export_service.py`: Test export services (XLSX, CSV, JSON)
  - `test_dashboard.py`: Test analytics dan audit log
  - `test_security.py`: Test security groups, record rules, sensitive data
- Documentation:
  - README.md komprehensif
  - CHANGELOG.md (file ini)
  - USER_GUIDE.md untuk panduan pengguna
  - API Reference

### Technical Details

#### Dependencies
- Python: 3.10+
- Odoo: 17.0
- xlsxwriter: 3.0.0+
- wkhtmltopdf: untuk PDF export

#### Performance Optimizations
- Lazy loading untuk dashboard charts
- Batch processing untuk export besar
- Caching untuk repeated queries
- Pagination untuk audit log

#### Security Measures
- Role-based access control
- Sensitive data masking
- Audit trail
- Input validation
- SQL injection prevention

---

## [Unreleased]

### Planned Features
- Export scheduling (cron jobs)
- Email delivery untuk export results
- Advanced chart customization
- Export to Google Sheets
- Import dari template
- Batch regulatory report generation

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 17.0.1.0.0 | 2025-01-15 | Initial release dengan full features |

---

## Migration Notes

### Dari versi sebelumnya
Ini adalah release pertama, tidak ada migrasi yang diperlukan.

### Untuk upgrade ke versi berikutnya
- Backup database sebelum upgrade
- Run `./odoo-bin -u yhc_employee_export` untuk update
- Review changelog untuk breaking changes

---

## Contributors

- YHC Development Team
- [Contributor names]

## License

LGPL-3 - See LICENSE file for details.
