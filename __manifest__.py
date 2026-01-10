# -*- coding: utf-8 -*-
# Module: yhc_employee_export
# Manifest file untuk module export dan analytics data karyawan.
#
# Module ini menyediakan fitur:
# - Dashboard visualisasi data karyawan
# - Export data ke berbagai format (Excel, CSV, PDF, JSON)
# - Template laporan yang customizable
# - Format export sesuai regulasi (BPJS, Pajak)
{
    'name': 'YHC Employee Export & Analytics',
    'version': '17.0.1.0.0',
    'category': 'Human Resources/Employees',
    'summary': 'Export data karyawan dan dashboard analytics',
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
        
        Module ini terintegrasi dengan module yhc_employee.
    """,
    'author': 'Oka Rajeb Abdillah - Digitaliz',
    'website': 'https://www.digitaliz.id',
    'license': 'LGPL-3',
    'depends': [
        'yhc_employee',
        'hr',
        'web',
        'mail',
    ],
    'data': [
        # Security
        'security/export_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/export_template_data.xml',
        # Reports
        'reports/employee_export_report.xml',
        'reports/bpjs_report.xml',
        # Views - wizard harus sebelum menu karena menu mereferensikan action wizard
        'views/export_wizard_views.xml',
        'views/export_graph_views.xml',
        'views/audit_log_views.xml',
        'views/menu_views.xml',
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
