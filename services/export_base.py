# -*- coding: utf-8 -*-
"""
Base Export Service untuk yhc_employee_export.

Module ini menyediakan base class untuk semua export services
dengan method-method umum yang digunakan bersama.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessDenied
from datetime import datetime, date
import time
import logging

_logger = logging.getLogger(__name__)

# Daftar field sensitif yang memerlukan akses khusus
SENSITIVE_FIELDS = [
    'x_nik', 'x_kk_number', 'identification_id', 'passport_id',
    'x_bpjs_kesehatan', 'x_bpjs_ketenagakerjaan',
    'x_npwp', 'x_bank_account', 'x_bank_name', 'bank_account_id',
    'x_salary', 'x_allowances', 'wage',
]


class EmployeeExportBase:
    """
    Base class untuk semua export services.
    
    Menyediakan method-method umum untuk:
    - Format nilai field
    - Handle relational data
    - Generate filename
    - Validasi data
    - Security validation
    - Audit logging
    """
    
    def __init__(self, env):
        """
        Initialize export service.
        
        Args:
            env: Odoo environment
        """
        self.env = env
        self.date_format = '%d/%m/%Y'
        self.datetime_format = '%d/%m/%Y %H:%M:%S'
        self.empty_value = '-'
        self._start_time = None
        self._include_sensitive = False
    
    # ===== Security Methods =====
    
    def _check_access(self, export_type='basic'):
        """
        Validasi akses user untuk export.
        
        Args:
            export_type: 'basic', 'sensitive', atau 'regulatory'
            
        Raises:
            AccessDenied: Jika tidak memiliki akses
        """
        user = self.env.user
        
        if user._is_superuser():
            return True
        
        # Basic access
        if not user.has_group('yhc_employee_export.group_hr_export_user'):
            raise AccessDenied(_("Anda tidak memiliki akses untuk export data."))
        
        # Sensitive data access
        if export_type == 'sensitive':
            if not user.has_group('yhc_employee_export.group_hr_sensitive_data'):
                raise AccessDenied(_("Anda tidak memiliki akses untuk export data sensitif."))
        
        # Regulatory export access
        elif export_type == 'regulatory':
            if not user.has_group('yhc_employee_export.group_hr_regulatory_export'):
                raise AccessDenied(_("Anda tidak memiliki akses untuk export format regulasi."))
        
        return True
    
    def _has_sensitive_access(self):
        """Cek apakah user memiliki akses data sensitif."""
        return self.env.user.has_group('yhc_employee_export.group_hr_sensitive_data')
    
    def _has_regulatory_access(self):
        """Cek apakah user memiliki akses regulatory export."""
        return self.env.user.has_group('yhc_employee_export.group_hr_regulatory_export')
    
    def _filter_sensitive_fields(self, fields_list):
        """
        Filter field sensitif dari list field.
        
        Args:
            fields_list: List field yang akan di-export
            
        Returns:
            list: Field yang sudah difilter
        """
        if self._has_sensitive_access():
            self._include_sensitive = True
            return fields_list
        
        self._include_sensitive = False
        return [f for f in fields_list if f not in SENSITIVE_FIELDS]
    
    def _mask_sensitive_value(self, value, field_name):
        """
        Mask nilai field sensitif.
        
        Args:
            value: Nilai asli
            field_name: Nama field
            
        Returns:
            Nilai yang sudah di-mask jika tidak ada akses
        """
        if self._has_sensitive_access():
            return value
        
        if field_name in SENSITIVE_FIELDS and value:
            if isinstance(value, str) and len(value) > 4:
                return '*' * (len(value) - 4) + value[-4:]
            return '****'
        
        return value
    
    # ===== Audit Logging Methods =====
    
    def _start_export(self):
        """Mulai tracking waktu export."""
        self._start_time = time.time()
    
    def _log_export(self, export_type, record_count, status='success', **kwargs):
        """
        Log aktivitas export ke audit log.
        
        Args:
            export_type: Tipe export
            record_count: Jumlah record
            status: Status export
            **kwargs: Parameter tambahan
        """
        duration = 0
        if self._start_time:
            duration = time.time() - self._start_time
        
        try:
            AuditLog = self.env['hr.employee.export.audit.log'].sudo()
            AuditLog.create({
                'export_type': export_type,
                'record_count': record_count,
                'status': status,
                'duration': duration,
                'include_sensitive': self._include_sensitive,
                **kwargs
            })
        except Exception as e:
            _logger.error(f"Failed to create audit log: {e}")
    
    def set_date_format(self, date_format):
        """Set format tanggal untuk export."""
        self.date_format = date_format
        return self
    
    def set_empty_value(self, empty_value):
        """Set nilai untuk field kosong."""
        self.empty_value = empty_value
        return self
    
    def generate_filename(self, prefix='export', extension='xlsx'):
        """
        Generate nama file dengan timestamp.
        
        Args:
            prefix (str): Prefix nama file
            extension (str): Extension file
            
        Returns:
            str: Nama file dengan format prefix_YYYYMMDD_HHMMSS.extension
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.{extension}"
    
    def format_value(self, value, field_type=None):
        """
        Format nilai untuk export.
        
        Args:
            value: Nilai yang akan di-format
            field_type (str): Tipe field (optional)
            
        Returns:
            str: Nilai yang sudah di-format
        """
        if value is None or value is False:
            return self.empty_value
        
        if isinstance(value, bool):
            return 'Ya' if value else 'Tidak'
        
        if isinstance(value, datetime):
            return value.strftime(self.datetime_format)
        
        if isinstance(value, date):
            return value.strftime(self.date_format)
        
        if isinstance(value, float):
            # Format dengan 2 desimal jika ada desimal, jika tidak tampilkan integer
            if value == int(value):
                return str(int(value))
            return f"{value:.2f}"
        
        if isinstance(value, (list, tuple)):
            return ', '.join(str(v) for v in value)
        
        return str(value)
    
    def get_field_value(self, record, field_path):
        """
        Mengambil nilai field dari record, support dot notation.
        
        Args:
            record: Odoo record
            field_path (str): Path field dengan dot notation (e.g., 'department_id.name')
            
        Returns:
            Nilai field atau None
        """
        try:
            parts = field_path.split('.')
            value = record
            
            for part in parts:
                if not value:
                    return None
                    
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
                
                # Handle empty recordset
                if hasattr(value, '_name') and len(value) == 0:
                    return None
            
            return value
            
        except Exception as e:
            _logger.warning(f"Error getting field value for {field_path}: {e}")
            return None
    
    def get_formatted_field_value(self, record, field_path):
        """
        Mengambil dan format nilai field dari record.
        
        Args:
            record: Odoo record
            field_path (str): Path field
            
        Returns:
            str: Nilai yang sudah di-format
        """
        value = self.get_field_value(record, field_path)
        
        # Handle recordset (Many2one, One2many, Many2many)
        if hasattr(value, '_name'):
            if len(value) == 0:
                return self.empty_value
            elif len(value) == 1:
                # Single record - return name or display_name
                if hasattr(value, 'name') and value.name:
                    return str(value.name)
                return str(value.display_name)
            else:
                # Multiple records - join names
                names = []
                for rec in value:
                    if hasattr(rec, 'name') and rec.name:
                        names.append(str(rec.name))
                    else:
                        names.append(str(rec.display_name))
                return ', '.join(names)
        
        return self.format_value(value)
    
    def get_selection_label(self, record, field_name):
        """
        Mengambil label dari selection field.
        
        Args:
            record: Odoo record
            field_name (str): Nama field selection
            
        Returns:
            str: Label selection atau empty_value
        """
        try:
            value = getattr(record, field_name, None)
            if not value:
                return self.empty_value
            
            field = record._fields.get(field_name)
            if field and hasattr(field, 'selection'):
                selection = field.selection
                if callable(selection):
                    selection = selection(record)
                selection_dict = dict(selection)
                return selection_dict.get(value, value)
            
            return str(value)
        except Exception as e:
            _logger.warning(f"Error getting selection label for {field_name}: {e}")
            return self.empty_value
    
    def validate_employees(self, employees):
        """
        Validasi recordset employees.
        
        Args:
            employees: hr.employee recordset
            
        Raises:
            UserError: Jika tidak ada data
        """
        if not employees:
            raise UserError(_("Tidak ada data karyawan untuk di-export."))
    
    def get_company_info(self):
        """
        Mengambil informasi perusahaan untuk header laporan.
        
        Returns:
            dict: Informasi perusahaan
        """
        company = self.env.company
        return {
            'name': company.name,
            'street': company.street or '',
            'city': company.city or '',
            'phone': company.phone or '',
            'email': company.email or '',
            'website': company.website or '',
            'logo': company.logo,
        }
    
    def get_export_metadata(self):
        """
        Mengambil metadata export.
        
        Returns:
            dict: Metadata export
        """
        return {
            'exported_at': datetime.now().isoformat(),
            'exported_by': self.env.user.name,
            'company': self.env.company.name,
        }


# Field mapping untuk berbagai kategori data
FIELD_MAPPINGS = {
    'identity': [
        ('nrp', 'NRP'),
        ('name', 'Nama Lengkap'),
        ('gelar', 'Gelar'),
        ('nama_ktp', 'Nama KTP'),
        ('nik', 'NIK'),
        ('no_kk', 'No. KK'),
        ('no_akta_lahir', 'No. Akta Lahir'),
        ('alamat_ktp', 'Alamat KTP'),
        ('place_of_birth', 'Tempat Lahir'),
        ('birthday', 'Tanggal Lahir'),
        ('age', 'Usia'),
        ('gender', 'Jenis Kelamin'),
        ('blood_type', 'Golongan Darah'),
        ('religion', 'Agama'),
        ('status_kawin', 'Status Pernikahan'),
    ],
    'employment': [
        ('nrp', 'NRP'),
        ('name', 'Nama'),
        ('department_id.name', 'Unit Kerja'),
        ('job_id.name', 'Jabatan'),
        ('area_kerja_id.name', 'Area Kerja'),
        ('golongan_id.name', 'Golongan'),
        ('grade_id.name', 'Grade'),
        ('employee_type_id.name', 'Tipe Pegawai'),
        ('employee_category_id.name', 'Jenis Pegawai'),
        ('employment_status', 'Status Kepegawaian'),
        ('first_contract_date', 'Tanggal Masuk'),
        ('service_length', 'Masa Kerja (Tahun)'),
    ],
    'family': [
        ('nrp', 'NRP'),
        ('name', 'Nama Karyawan'),
        ('status_kawin', 'Status Pernikahan'),
        ('spouse_name', 'Nama Pasangan'),
        ('spouse_nik', 'NIK Pasangan'),
        ('spouse_birthday', 'Tgl Lahir Pasangan'),
        ('jlh_anggota_keluarga', 'Jml Anggota Keluarga'),
    ],
    'bpjs': [
        ('nrp', 'NRP'),
        ('name', 'Nama'),
        ('nik', 'NIK'),
    ],
    'education': [
        ('nrp', 'NRP'),
        ('name', 'Nama'),
    ],
    'payroll': [
        ('nrp', 'NRP'),
        ('name', 'Nama'),
        ('nik', 'NIK'),
    ],
    'training': [
        ('nrp', 'NRP'),
        ('name', 'Nama'),
        ('department_id.name', 'Unit Kerja'),
    ],
    'reward_punishment': [
        ('nrp', 'NRP'),
        ('name', 'Nama'),
        ('department_id.name', 'Unit Kerja'),
    ],
}
