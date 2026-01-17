# -*- coding: utf-8 -*-
# Module: yhc_employee_export
# Manifest file untuk module export dan analytics data karyawan.
#
# Module ini menyediakan fitur:
# - Dashboard visualisasi data karyawan
# - Export data ke berbagai format (Excel, CSV, PDF, JSON)
# - Template laporan yang customizable
# - Format export sesuai regulasi (BPJS, Pajak)
# - Workforce Analytics dengan snapshot data (PRD v1.1)
{
    'name': 'YHC Employee Export & Analytics',
    'version': '17.0.1.1.0',
    'category': 'Human Resources/Employees',
    'summary': 'Export data karyawan dan dashboard analytics dengan workforce analytics',
    'description': """
        YHC Employee Export & Analytics
        ================================
        
        Module ini menyediakan fitur lengkap untuk:
        
        **Dashboard & Grafik:**
        - Visualisasi distribusi gender, usia, agama
        - Grafik karyawan per departemen dan area kerja
        - Trend rekrutmen dan terminasi
        - Statistik pendidikan dan pelatihan
        
        **Export Data:**
        - Export ke Excel (.xlsx) dengan multiple sheets
        - Export ke CSV
        - Export ke PDF dengan template profesional
        - Export ke JSON untuk integrasi API
        
        **Template Laporan:**
        - Laporan demografi karyawan
        - Laporan kepegawaian
        - Laporan BPJS
        - Laporan pendidikan dan pelatihan
        - Dan banyak lagi...
        
        **Format Regulasi:**
        - Format BPJS Kesehatan
        - Format BPJS Ketenagakerjaan
        - Format pelaporan pajak
        
        **Workforce Analytics (PRD v1.1):**
        - Snapshot data karyawan per bulan
        - Grafik Payroll vs Non-Payroll per Unit (WA01)
        - Grafik Total Karyawan per Unit (WA02)
        - Trend Workforce Bulanan (WA03)
        - Distribusi Status Kepegawaian (WA04)
        - Export PDF untuk Executive Summary
        
        **Workforce Report Engine (PRD v1.1):**
        - Official Workforce Structural Report
        - Snapshot-based reporting (end-of-month)
        - Fixed structure PDF output
        - Audit-ready with reconciliation validation
        - Unit-centric aggregation
        
        Module ini terintegrasi dengan module yhc_employee.
    """,
    'author': 'Oka Rajeb Abdillah - Digitaliz',
    'website': 'https://github.com/or-abdillh/yhc-employee-export-module',
    'license': 'LGPL-3',
    'depends': [
        'yhc_employee',
        'hr',
        'web',
        'mail',
    ],
    'external_dependencies': {
        'python': ['matplotlib', 'numpy'],
    },
    'data': [
        # Security
        'security/export_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/export_template_data.xml',
        # Reports
        'reports/employee_export_report.xml',
        'reports/bpjs_report.xml',
        'reports/workforce_analytics_report.xml',
        'reports/workforce_official_report.xml',
        # Views - wizard harus sebelum menu karena menu mereferensikan action wizard
        'views/export_wizard_views.xml',
        'views/export_graph_views.xml',
        'views/export_workforce_views.xml',
        'views/workforce_report_views.xml',
        'views/seed_wizard_views.xml',
        'views/audit_log_views.xml',
        'views/menu_views.xml',
        # Security rules for new models (loaded after models are registered)
        'security/snapshot_security.xml',
        'security/workforce_report_security.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'yhc_employee_export/static/src/css/dashboard.css',
            'yhc_employee_export/static/src/js/dashboard.js',
            'yhc_employee_export/static/src/xml/dashboard_templates.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 10,
    'images': ['static/description/icon.png'],
}
