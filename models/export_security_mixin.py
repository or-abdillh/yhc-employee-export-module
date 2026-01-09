# -*- coding: utf-8 -*-

"""
Security Mixin untuk yhc_employee_export

Mixin class yang menyediakan method-method untuk
validasi akses dan proteksi data sensitif.
"""

import logging

from odoo import api, fields, models
from odoo.exceptions import AccessDenied, UserError

_logger = logging.getLogger(__name__)


# Field-field yang dikategorikan sensitif
SENSITIVE_FIELDS = [
    # Data Identitas
    'x_nik',
    'x_kk_number',
    'identification_id',
    'passport_id',
    
    # Data BPJS
    'x_bpjs_kesehatan',
    'x_bpjs_ketenagakerjaan',
    'bpjs_kesehatan',
    'bpjs_ketenagakerjaan',
    
    # Data Keuangan
    'x_npwp',
    'x_bank_account',
    'x_bank_name',
    'bank_account_id',
    
    # Data Payroll
    'x_salary',
    'x_allowances',
    'wage',
    
    # Data Reward & Punishment
    'x_reward_ids',
    'x_punishment_ids',
]

# Field yang hanya bisa diakses dengan regulatory access
REGULATORY_FIELDS = [
    'x_bpjs_kesehatan',
    'x_bpjs_ketenagakerjaan',
    'x_npwp',
    'x_tax_status',
    'x_ptkp_status',
]


class ExportSecurityMixin(models.AbstractModel):
    """
    Mixin untuk validasi keamanan export.
    
    Menyediakan method-method untuk:
    - Cek akses user ke fitur export
    - Filter field sensitif berdasarkan group
    - Validasi akses regulatory export
    - Logging aktivitas export
    """
    
    _name = 'export.security.mixin'
    _description = 'Export Security Mixin'
    
    # ===== Access Check Methods =====
    
    def _check_export_access(self, export_type='basic'):
        """
        Cek apakah user memiliki akses untuk melakukan export.
        
        Args:
            export_type: Tipe export ('basic', 'sensitive', 'regulatory')
            
        Returns:
            bool: True jika memiliki akses
            
        Raises:
            AccessDenied: Jika tidak memiliki akses
        """
        user = self.env.user
        
        # Superuser always has access
        if user._is_superuser():
            return True
        
        # Check basic export access
        if not user.has_group('yhc_employee_export.group_hr_export_user'):
            raise AccessDenied("Anda tidak memiliki akses untuk export data.")
        
        # Check sensitive data access
        if export_type == 'sensitive':
            if not user.has_group('yhc_employee_export.group_hr_sensitive_data'):
                raise AccessDenied("Anda tidak memiliki akses untuk export data sensitif.")
        
        # Check regulatory export access
        elif export_type == 'regulatory':
            if not user.has_group('yhc_employee_export.group_hr_regulatory_export'):
                raise AccessDenied("Anda tidak memiliki akses untuk export format regulasi.")
        
        return True
    
    def _has_sensitive_access(self):
        """
        Cek apakah user memiliki akses data sensitif.
        
        Returns:
            bool: True jika memiliki akses
        """
        return self.env.user.has_group('yhc_employee_export.group_hr_sensitive_data')
    
    def _has_regulatory_access(self):
        """
        Cek apakah user memiliki akses regulatory export.
        
        Returns:
            bool: True jika memiliki akses
        """
        return self.env.user.has_group('yhc_employee_export.group_hr_regulatory_export')
    
    def _has_manager_access(self):
        """
        Cek apakah user adalah HR Export Manager.
        
        Returns:
            bool: True jika manager
        """
        return self.env.user.has_group('yhc_employee_export.group_hr_export_manager')
    
    # ===== Field Filtering Methods =====
    
    def _filter_sensitive_fields(self, fields_list):
        """
        Filter field sensitif dari list field.
        
        Args:
            fields_list: List field yang akan di-export
            
        Returns:
            list: Field yang sudah difilter (tanpa sensitif jika tidak ada akses)
        """
        if self._has_sensitive_access():
            return fields_list
        
        return [f for f in fields_list if f not in SENSITIVE_FIELDS]
    
    def _mask_sensitive_data(self, data, fields_to_mask=None):
        """
        Mask data sensitif dalam dict.
        
        Args:
            data: Dict data karyawan
            fields_to_mask: List field yang akan di-mask (default: SENSITIVE_FIELDS)
            
        Returns:
            dict: Data dengan field sensitif di-mask
        """
        if self._has_sensitive_access():
            return data
        
        fields_to_mask = fields_to_mask or SENSITIVE_FIELDS
        masked_data = data.copy()
        
        for field in fields_to_mask:
            if field in masked_data:
                value = masked_data[field]
                if value:
                    # Mask dengan asterisk, tampilkan 4 karakter terakhir
                    if isinstance(value, str) and len(value) > 4:
                        masked_data[field] = '*' * (len(value) - 4) + value[-4:]
                    else:
                        masked_data[field] = '****'
        
        return masked_data
    
    def _get_allowed_fields(self, requested_fields):
        """
        Mendapatkan list field yang diizinkan untuk di-export.
        
        Args:
            requested_fields: List field yang diminta
            
        Returns:
            tuple: (allowed_fields, denied_fields)
        """
        allowed = []
        denied = []
        
        has_sensitive = self._has_sensitive_access()
        has_regulatory = self._has_regulatory_access()
        
        for field in requested_fields:
            if field in REGULATORY_FIELDS and not has_regulatory:
                denied.append(field)
            elif field in SENSITIVE_FIELDS and not has_sensitive:
                denied.append(field)
            else:
                allowed.append(field)
        
        return allowed, denied
    
    # ===== Audit Logging Methods =====
    
    def _log_export_activity(self, export_type, record_count, **kwargs):
        """
        Log aktivitas export ke audit log.
        
        Args:
            export_type: Tipe export
            record_count: Jumlah record
            **kwargs: Parameter tambahan
        """
        AuditLog = self.env['hr.employee.export.audit.log']
        return AuditLog.log_export(export_type, record_count, **kwargs)
    
    # ===== Data Validation Methods =====
    
    def _validate_export_data(self, employees, export_type='basic'):
        """
        Validasi data sebelum export.
        
        Args:
            employees: Recordset hr.employee
            export_type: Tipe export
            
        Returns:
            recordset: Employee yang valid untuk di-export
            
        Raises:
            UserError: Jika validasi gagal
        """
        if not employees:
            raise UserError("Tidak ada data karyawan untuk di-export.")
        
        # Check department access (for non-managers)
        if not self._has_manager_access():
            user = self.env.user
            employee = user.employee_id
            
            if employee and employee.department_id:
                # User hanya bisa export dari departemennya
                user_dept = employee.department_id
                allowed_depts = user_dept | user_dept.child_ids
                
                employees = employees.filtered(
                    lambda e: e.department_id in allowed_depts
                )
        
        return employees
    
    def _get_export_summary(self, employees, export_type, include_sensitive=False):
        """
        Mendapatkan summary untuk logging.
        
        Args:
            employees: Recordset yang di-export
            export_type: Tipe export
            include_sensitive: Apakah include data sensitif
            
        Returns:
            dict: Summary data
        """
        return {
            'export_type': export_type,
            'record_count': len(employees),
            'include_sensitive': include_sensitive,
            'department_ids': [(6, 0, employees.mapped('department_id').ids)],
        }


class ExportSecurityService:
    """
    Service class untuk security validation.
    
    Digunakan oleh export services untuk validasi akses.
    """
    
    def __init__(self, env):
        self.env = env
        self.user = env.user
    
    def check_access(self, export_type='basic'):
        """
        Validasi akses user.
        
        Args:
            export_type: 'basic', 'sensitive', atau 'regulatory'
            
        Raises:
            AccessDenied: Jika tidak memiliki akses
        """
        if self.user._is_superuser():
            return True
        
        group_mapping = {
            'basic': 'yhc_employee_export.group_hr_export_user',
            'sensitive': 'yhc_employee_export.group_hr_sensitive_data',
            'regulatory': 'yhc_employee_export.group_hr_regulatory_export',
            'manager': 'yhc_employee_export.group_hr_export_manager',
        }
        
        required_group = group_mapping.get(export_type, group_mapping['basic'])
        
        if not self.user.has_group(required_group):
            raise AccessDenied(f"Akses ditolak untuk export tipe '{export_type}'")
        
        return True
    
    def filter_fields(self, fields_list):
        """
        Filter field berdasarkan akses user.
        
        Returns:
            list: Field yang diizinkan
        """
        if self.user._is_superuser():
            return fields_list
        
        has_sensitive = self.user.has_group('yhc_employee_export.group_hr_sensitive_data')
        has_regulatory = self.user.has_group('yhc_employee_export.group_hr_regulatory_export')
        
        filtered = []
        for field in fields_list:
            if field in REGULATORY_FIELDS and not has_regulatory:
                continue
            if field in SENSITIVE_FIELDS and not has_sensitive:
                continue
            filtered.append(field)
        
        return filtered
    
    def mask_value(self, value, field_name):
        """
        Mask nilai field sensitif.
        
        Args:
            value: Nilai asli
            field_name: Nama field
            
        Returns:
            Nilai yang sudah di-mask jika tidak ada akses
        """
        if self.user._is_superuser():
            return value
        
        has_sensitive = self.user.has_group('yhc_employee_export.group_hr_sensitive_data')
        
        if field_name in SENSITIVE_FIELDS and not has_sensitive:
            if value and isinstance(value, str) and len(value) > 4:
                return '*' * (len(value) - 4) + value[-4:]
            return '****' if value else value
        
        return value
    
    def log_activity(self, export_type, record_count, **kwargs):
        """
        Log aktivitas export.
        """
        AuditLog = self.env['hr.employee.export.audit.log']
        return AuditLog.log_export(export_type, record_count, **kwargs)
