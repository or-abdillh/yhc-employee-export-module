# -*- coding: utf-8 -*-

"""
Model Audit Log untuk yhc_employee_export

Model ini mencatat semua aktivitas export untuk keperluan audit.
Setiap export yang dilakukan akan tercatat di log ini.
"""

import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployeeExportAuditLog(models.Model):
    """
    Model untuk mencatat audit log aktivitas export.
    
    Mencatat:
    - Siapa yang melakukan export
    - Kapan export dilakukan
    - Tipe export (format, template)
    - Data apa yang di-export (jumlah record, filter)
    - Status export (sukses/gagal)
    """
    
    _name = 'hr.employee.export.audit.log'
    _description = 'Export Audit Log'
    _order = 'create_date desc'
    _rec_name = 'display_name'
    
    # ===== Field Definitions =====
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        index=True,
    )
    
    export_date = fields.Datetime(
        string='Export Date',
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    
    export_type = fields.Selection([
        ('xlsx', 'Excel (XLSX)'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
        ('bpjs_kes', 'BPJS Kesehatan'),
        ('bpjs_tk', 'BPJS Ketenagakerjaan'),
        ('spt', 'SPT 1721-A1'),
        ('wlk', 'WLK'),
        ('other', 'Other'),
    ], string='Export Type', required=True, readonly=True)
    
    template_id = fields.Many2one(
        'hr.employee.export.template',
        string='Template Used',
        readonly=True,
    )
    
    record_count = fields.Integer(
        string='Records Exported',
        readonly=True,
        default=0,
    )
    
    department_ids = fields.Many2many(
        'hr.department',
        'export_audit_log_department_rel',
        'audit_log_id',
        'department_id',
        string='Departments',
        readonly=True,
    )
    
    filter_domain = fields.Text(
        string='Filter Domain',
        readonly=True,
        help='Domain yang digunakan untuk filter data',
    )
    
    include_sensitive = fields.Boolean(
        string='Include Sensitive Data',
        readonly=True,
        default=False,
    )
    
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ], string='Status', required=True, default='success', readonly=True)
    
    error_message = fields.Text(
        string='Error Message',
        readonly=True,
    )
    
    ip_address = fields.Char(
        string='IP Address',
        readonly=True,
    )
    
    file_size = fields.Integer(
        string='File Size (bytes)',
        readonly=True,
    )
    
    duration = fields.Float(
        string='Duration (seconds)',
        readonly=True,
        digits=(10, 3),
    )
    
    notes = fields.Text(
        string='Notes',
        readonly=True,
    )
    
    # ===== Computed Fields =====
    
    @api.depends('user_id', 'export_date', 'export_type')
    def _compute_display_name(self):
        for record in self:
            date_str = record.export_date.strftime('%Y-%m-%d %H:%M') if record.export_date else ''
            type_label = dict(self._fields['export_type'].selection).get(record.export_type, '')
            record.display_name = f"{record.user_id.name} - {type_label} - {date_str}"
    
    # ===== CRUD Methods =====
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create untuk menambahkan IP address."""
        for vals in vals_list:
            if not vals.get('ip_address'):
                try:
                    from odoo.http import request
                    if request and hasattr(request, 'httprequest'):
                        vals['ip_address'] = request.httprequest.remote_addr
                except Exception:
                    pass
        return super().create(vals_list)
    
    # ===== Helper Methods =====
    
    @api.model
    def log_export(self, export_type, record_count, **kwargs):
        """
        Helper method untuk mencatat export.
        
        Args:
            export_type: Tipe export (xlsx, csv, pdf, json, bpjs_kes, dll)
            record_count: Jumlah record yang di-export
            **kwargs: Parameter tambahan (template_id, status, error_message, dll)
            
        Returns:
            hr.employee.export.audit.log record
        """
        vals = {
            'export_type': export_type,
            'record_count': record_count,
            'export_date': datetime.now(),
        }
        vals.update(kwargs)
        
        try:
            return self.sudo().create(vals)
        except Exception as e:
            _logger.error(f"Failed to create audit log: {e}")
            return self.browse()
    
    @api.model
    def get_user_export_history(self, user_id=None, limit=50):
        """
        Mendapatkan history export user.
        
        Args:
            user_id: ID user (default: current user)
            limit: Maksimal record
            
        Returns:
            List of dict dengan history export
        """
        if not user_id:
            user_id = self.env.user.id
        
        logs = self.search([
            ('user_id', '=', user_id)
        ], limit=limit, order='export_date desc')
        
        return [{
            'id': log.id,
            'export_type': log.export_type,
            'export_date': log.export_date.isoformat() if log.export_date else None,
            'record_count': log.record_count,
            'status': log.status,
            'template': log.template_id.name if log.template_id else None,
        } for log in logs]
    
    @api.model
    def get_export_statistics(self, date_from=None, date_to=None):
        """
        Mendapatkan statistik export.
        
        Args:
            date_from: Tanggal mulai
            date_to: Tanggal akhir
            
        Returns:
            Dict dengan statistik export
        """
        domain = []
        if date_from:
            domain.append(('export_date', '>=', date_from))
        if date_to:
            domain.append(('export_date', '<=', date_to))
        
        logs = self.search(domain)
        
        # Group by type
        by_type = {}
        for log in logs:
            by_type[log.export_type] = by_type.get(log.export_type, 0) + 1
        
        # Group by user
        by_user = {}
        for log in logs:
            user_name = log.user_id.name
            by_user[user_name] = by_user.get(user_name, 0) + 1
        
        # Group by status
        by_status = {}
        for log in logs:
            by_status[log.status] = by_status.get(log.status, 0) + 1
        
        return {
            'total_exports': len(logs),
            'total_records': sum(logs.mapped('record_count')),
            'by_type': by_type,
            'by_user': by_user,
            'by_status': by_status,
            'sensitive_exports': len(logs.filtered('include_sensitive')),
        }
