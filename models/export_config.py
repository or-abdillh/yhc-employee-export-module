# -*- coding: utf-8 -*-
"""
Model: hr.employee.export.config
Konfigurasi untuk export data karyawan.

Model ini menyimpan konfigurasi yang dapat digunakan kembali
untuk proses export data karyawan.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class HrEmployeeExportConfig(models.Model):
    """
    Model untuk menyimpan konfigurasi export data karyawan.
    
    Konfigurasi ini dapat disimpan dan digunakan kembali untuk
    proses export yang berulang dengan parameter yang sama.
    """
    _name = 'hr.employee.export.config'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Konfigurasi Export Karyawan'
    _order = 'name'

    # ==================== Basic Information ====================
    name = fields.Char(
        string='Nama Konfigurasi',
        required=True,
        tracking=True,
        help='Nama untuk mengidentifikasi konfigurasi ini'
    )
    active = fields.Boolean(
        string='Aktif',
        default=True,
        help='Jika tidak aktif, konfigurasi tidak akan muncul di daftar pilihan'
    )
    description = fields.Text(
        string='Deskripsi',
        help='Deskripsi tambahan tentang konfigurasi ini'
    )
    is_default = fields.Boolean(
        string='Konfigurasi Default',
        default=False,
        help='Tandai sebagai konfigurasi default'
    )

    # ==================== Export Format ====================
    export_type = fields.Selection(
        selection=[
            ('xlsx', 'Excel (.xlsx)'),
            ('csv', 'CSV'),
            ('pdf', 'PDF'),
            ('json', 'JSON'),
        ],
        string='Format Export',
        required=True,
        default='xlsx',
        help='Format file yang akan dihasilkan'
    )

    # ==================== Data Category Selection ====================
    # Boolean fields untuk memilih kategori data yang akan di-export
    include_identity = fields.Boolean(
        string='Data Identitas',
        default=True,
        help='Sertakan data identitas (NRP, NIK, Nama, TTL, Gender, Agama, dll)'
    )
    include_employment = fields.Boolean(
        string='Data Kepegawaian',
        default=True,
        help='Sertakan data kepegawaian (Dept, Jabatan, Golongan, Grade, Status, Masa Kerja)'
    )
    include_family = fields.Boolean(
        string='Data Keluarga',
        default=False,
        help='Sertakan data keluarga (Pasangan, Anak, Orang Tua)'
    )
    include_bpjs = fields.Boolean(
        string='Data BPJS',
        default=False,
        help='Sertakan data BPJS (Kesehatan dan Ketenagakerjaan)'
    )
    include_education = fields.Boolean(
        string='Data Pendidikan',
        default=False,
        help='Sertakan riwayat pendidikan (Jenjang, Institusi, Jurusan)'
    )
    include_payroll = fields.Boolean(
        string='Data Payroll',
        default=False,
        help='Sertakan data payroll (Bank, Rekening, NPWP)'
    )
    include_training = fields.Boolean(
        string='Data Pelatihan',
        default=False,
        help='Sertakan data pelatihan dan sertifikasi'
    )
    include_reward_punishment = fields.Boolean(
        string='Data Reward & Punishment',
        default=False,
        help='Sertakan data penghargaan dan sanksi'
    )

    # ==================== Filter Fields ====================
    department_ids = fields.Many2many(
        comodel_name='hr.department',
        relation='hr_export_config_department_rel',
        column1='config_id',
        column2='department_id',
        string='Departemen',
        help='Filter berdasarkan departemen. Kosongkan untuk semua departemen.'
    )
    employment_status = fields.Selection(
        selection=[
            ('all', 'Semua Status'),
            ('active', 'Aktif'),
            ('inactive', 'Tidak Aktif'),
            ('pensiun', 'Pensiun'),
            ('resign', 'Resign'),
            ('phk', 'PHK'),
        ],
        string='Status Kepegawaian',
        default='all',
        help='Filter berdasarkan status kepegawaian'
    )
    date_from = fields.Date(
        string='Tanggal Masuk Dari',
        help='Filter karyawan dengan tanggal masuk mulai dari tanggal ini'
    )
    date_to = fields.Date(
        string='Tanggal Masuk Sampai',
        help='Filter karyawan dengan tanggal masuk sampai tanggal ini'
    )

    # ==================== Additional Options ====================
    include_inactive = fields.Boolean(
        string='Termasuk Karyawan Tidak Aktif',
        default=False,
        help='Sertakan karyawan yang sudah tidak aktif'
    )
    csv_delimiter = fields.Selection(
        selection=[
            (',', 'Koma (,)'),
            (';', 'Semicolon (;)'),
            ('\t', 'Tab'),
            ('|', 'Pipe (|)'),
        ],
        string='Delimiter CSV',
        default=',',
        help='Delimiter untuk format CSV'
    )

    # ==================== Computed Fields ====================
    selected_categories_count = fields.Integer(
        string='Jumlah Kategori',
        compute='_compute_selected_categories_count',
        help='Jumlah kategori data yang dipilih'
    )
    filter_summary = fields.Char(
        string='Ringkasan Filter',
        compute='_compute_filter_summary',
        help='Ringkasan filter yang diterapkan'
    )

    # ==================== Constraints ====================
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Nama konfigurasi harus unik!'),
    ]

    # ==================== Compute Methods ====================
    @api.depends('include_identity', 'include_employment', 'include_family',
                 'include_bpjs', 'include_education', 'include_payroll',
                 'include_training', 'include_reward_punishment')
    def _compute_selected_categories_count(self):
        """Menghitung jumlah kategori data yang dipilih untuk di-export."""
        for record in self:
            count = sum([
                record.include_identity,
                record.include_employment,
                record.include_family,
                record.include_bpjs,
                record.include_education,
                record.include_payroll,
                record.include_training,
                record.include_reward_punishment,
            ])
            record.selected_categories_count = count

    @api.depends('department_ids', 'employment_status', 'date_from', 'date_to')
    def _compute_filter_summary(self):
        """Membuat ringkasan filter yang diterapkan."""
        for record in self:
            parts = []
            
            # Department filter
            if record.department_ids:
                dept_names = record.department_ids.mapped('name')
                if len(dept_names) > 2:
                    parts.append(f"{len(dept_names)} Departemen")
                else:
                    parts.append(', '.join(dept_names))
            else:
                parts.append('Semua Dept')
            
            # Status filter
            if record.employment_status and record.employment_status != 'all':
                status_dict = dict(record._fields['employment_status'].selection)
                parts.append(status_dict.get(record.employment_status, ''))
            
            # Date filter
            if record.date_from or record.date_to:
                date_str = ''
                if record.date_from:
                    date_str += record.date_from.strftime('%d/%m/%Y')
                date_str += ' - '
                if record.date_to:
                    date_str += record.date_to.strftime('%d/%m/%Y')
                parts.append(date_str)
            
            record.filter_summary = ' | '.join(parts) if parts else 'Tanpa Filter'

    # ==================== Validation Methods ====================
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validasi tanggal: date_from harus lebih kecil dari date_to."""
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise ValidationError(_(
                        "Tanggal 'Dari' tidak boleh lebih besar dari tanggal 'Sampai'."
                    ))

    @api.constrains('include_identity', 'include_employment', 'include_family',
                    'include_bpjs', 'include_education', 'include_payroll',
                    'include_training', 'include_reward_punishment')
    def _check_at_least_one_category(self):
        """Validasi: minimal satu kategori data harus dipilih."""
        for record in self:
            if record.selected_categories_count == 0:
                raise ValidationError(_(
                    "Minimal satu kategori data harus dipilih untuk di-export."
                ))

    # ==================== Action Methods ====================
    def action_set_default(self):
        """Set konfigurasi ini sebagai default dan unset yang lain."""
        self.ensure_one()
        # Unset semua konfigurasi default lainnya
        self.search([('is_default', '=', True), ('id', '!=', self.id)]).write({
            'is_default': False
        })
        self.write({'is_default': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Berhasil'),
                'message': _('Konfigurasi "%s" ditetapkan sebagai default.') % self.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_duplicate_config(self):
        """Duplikasi konfigurasi ini dengan nama baru."""
        self.ensure_one()
        new_name = _("%s (Copy)") % self.name
        # Pastikan nama unik
        counter = 1
        while self.search_count([('name', '=', new_name)]) > 0:
            counter += 1
            new_name = _("%s (Copy %d)") % (self.name, counter)
        
        new_config = self.copy({'name': new_name, 'is_default': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.export.config',
            'res_id': new_config.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_preview_employees(self):
        """Preview karyawan yang akan di-export berdasarkan filter."""
        self.ensure_one()
        domain = self._build_employee_domain()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Preview Karyawan - %s') % self.name,
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False},
            'target': 'current',
        }

    def action_export_now(self):
        """
        Langsung export dengan konfigurasi ini.
        Akan membuka wizard export dengan konfigurasi yang sudah terisi.
        """
        self.ensure_one()
        # TODO: Implementasi di Fase 4 (Export Wizard)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Info'),
                'message': _('Fitur export akan tersedia setelah Fase 4 selesai.'),
                'type': 'info',
                'sticky': False,
            }
        }

    # ==================== Helper Methods ====================
    def _build_employee_domain(self):
        """
        Membangun domain filter untuk query karyawan.
        
        Returns:
            list: Domain filter untuk hr.employee
        """
        self.ensure_one()
        domain = []
        
        # Filter departemen
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        
        # Filter status kepegawaian
        if self.employment_status and self.employment_status != 'all':
            domain.append(('employment_status', '=', self.employment_status))
        
        # Filter tanggal masuk
        if self.date_from:
            domain.append(('first_contract_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('first_contract_date', '<=', self.date_to))
        
        # Filter karyawan aktif/tidak aktif
        if not self.include_inactive:
            domain.append(('active', '=', True))
        
        return domain

    def _get_selected_categories(self):
        """
        Mendapatkan list kategori data yang dipilih.
        
        Returns:
            list: List string nama kategori yang dipilih
        """
        self.ensure_one()
        categories = []
        
        if self.include_identity:
            categories.append('identity')
        if self.include_employment:
            categories.append('employment')
        if self.include_family:
            categories.append('family')
        if self.include_bpjs:
            categories.append('bpjs')
        if self.include_education:
            categories.append('education')
        if self.include_payroll:
            categories.append('payroll')
        if self.include_training:
            categories.append('training')
        if self.include_reward_punishment:
            categories.append('reward_punishment')
        
        return categories

    def _get_config_as_dict(self):
        """
        Mengkonversi konfigurasi ke dictionary.
        Berguna untuk serialisasi atau passing ke service.
        
        Returns:
            dict: Dictionary berisi semua konfigurasi
        """
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'export_type': self.export_type,
            'categories': self._get_selected_categories(),
            'filters': {
                'department_ids': self.department_ids.ids,
                'employment_status': self.employment_status,
                'date_from': self.date_from.isoformat() if self.date_from else None,
                'date_to': self.date_to.isoformat() if self.date_to else None,
                'include_inactive': self.include_inactive,
            },
            'options': {
                'csv_delimiter': self.csv_delimiter,
            },
        }

    @api.model
    def get_default_config(self):
        """
        Mendapatkan konfigurasi default.
        
        Returns:
            recordset: Record konfigurasi default atau False
        """
        return self.search([('is_default', '=', True)], limit=1)

    @api.model
    def load_config_from_dict(self, config_dict):
        """
        Membuat atau update konfigurasi dari dictionary.
        
        Args:
            config_dict (dict): Dictionary berisi konfigurasi
            
        Returns:
            recordset: Record konfigurasi yang dibuat/diupdate
        """
        vals = {
            'name': config_dict.get('name', _('Konfigurasi Baru')),
            'export_type': config_dict.get('export_type', 'xlsx'),
            'include_identity': 'identity' in config_dict.get('categories', []),
            'include_employment': 'employment' in config_dict.get('categories', []),
            'include_family': 'family' in config_dict.get('categories', []),
            'include_bpjs': 'bpjs' in config_dict.get('categories', []),
            'include_education': 'education' in config_dict.get('categories', []),
            'include_payroll': 'payroll' in config_dict.get('categories', []),
            'include_training': 'training' in config_dict.get('categories', []),
            'include_reward_punishment': 'reward_punishment' in config_dict.get('categories', []),
        }
        
        filters = config_dict.get('filters', {})
        if filters.get('department_ids'):
            vals['department_ids'] = [(6, 0, filters['department_ids'])]
        if filters.get('employment_status'):
            vals['employment_status'] = filters['employment_status']
        if filters.get('date_from'):
            vals['date_from'] = filters['date_from']
        if filters.get('date_to'):
            vals['date_to'] = filters['date_to']
        if 'include_inactive' in filters:
            vals['include_inactive'] = filters['include_inactive']
        
        options = config_dict.get('options', {})
        if options.get('csv_delimiter'):
            vals['csv_delimiter'] = options['csv_delimiter']
        
        return self.create(vals)

    def toggle_active(self):
        """Toggle status aktif konfigurasi."""
        for record in self:
            record.active = not record.active
