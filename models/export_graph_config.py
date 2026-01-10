# -*- coding: utf-8 -*-
"""
Model: hr.employee.export.graph.config
Konfigurasi export grafik dashboard ke PDF.

Model ini menyimpan konfigurasi template export grafik yang dapat
digunakan kembali untuk menghasilkan laporan PDF berbasis chart.
"""

import json
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .graph_registry import GRAPH_REGISTRY, GRAPH_CATEGORIES, get_graph_selection

_logger = logging.getLogger(__name__)


class HrEmployeeExportGraphConfig(models.Model):
    """
    Model konfigurasi export grafik ke PDF.
    
    Menyimpan pengaturan:
    - Grafik mana saja yang akan diekspor
    - Layout PDF (single column, two columns, executive summary)
    - Filter data (departemen, tanggal)
    """
    
    _name = 'hr.employee.export.graph.config'
    _description = 'Konfigurasi Export Grafik'
    _order = 'name'
    
    # ===== Basic Info =====
    name = fields.Char(
        string='Nama Konfigurasi',
        required=True,
        help='Nama untuk identifikasi konfigurasi export',
    )
    
    description = fields.Text(
        string='Deskripsi',
        help='Deskripsi tujuan/penggunaan konfigurasi ini',
    )
    
    active = fields.Boolean(
        string='Aktif',
        default=True,
    )
    
    # ===== Graph Selection =====
    graph_ids = fields.Char(
        string='Grafik Terpilih (JSON)',
        default='[]',
        help='JSON array kode grafik yang dipilih',
    )
    
    # Boolean fields untuk setiap grafik (untuk UI)
    include_g01 = fields.Boolean(string='G01 - Distribusi Gender', default=True)
    include_g02 = fields.Boolean(string='G02 - Distribusi Usia', default=True)
    include_g03 = fields.Boolean(string='G03 - Distribusi Agama', default=False)
    include_g04 = fields.Boolean(string='G04 - Status Pernikahan', default=False)
    include_g06 = fields.Boolean(string='G06 - Karyawan per Departemen', default=True)
    include_g08 = fields.Boolean(string='G08 - Distribusi Golongan', default=False)
    include_g09 = fields.Boolean(string='G09 - Distribusi Grade', default=False)
    include_g10 = fields.Boolean(string='G10 - Status Kepegawaian', default=True)
    include_g13 = fields.Boolean(string='G13 - Masa Kerja', default=True)
    include_g14 = fields.Boolean(string='G14 - Trend Rekrutmen', default=False)
    include_g16 = fields.Boolean(string='G16 - Level Pendidikan', default=True)
    include_g20 = fields.Boolean(string='G20 - Pelatihan per Jenis', default=False)
    include_g21 = fields.Boolean(string='G21 - Pelatihan per Metode', default=False)
    
    # ===== Layout Options =====
    layout_type = fields.Selection(
        selection=[
            ('single_column', 'Satu Kolom (1 grafik per halaman)'),
            ('two_columns', 'Dua Kolom (2 grafik per halaman)'),
            ('executive_summary', 'Executive Summary (ringkasan + grafik)'),
        ],
        string='Layout PDF',
        default='two_columns',
        required=True,
        help='Tata letak grafik dalam PDF',
    )
    
    include_summary = fields.Boolean(
        string='Sertakan Ringkasan',
        default=True,
        help='Tambahkan halaman ringkasan angka di awal PDF',
    )
    
    include_cover = fields.Boolean(
        string='Sertakan Cover',
        default=True,
        help='Tambahkan halaman cover di awal PDF',
    )
    
    # ===== Filter Options =====
    filter_department_ids = fields.Many2many(
        comodel_name='hr.department',
        relation='export_graph_config_department_rel',
        column1='config_id',
        column2='department_id',
        string='Filter Departemen',
        help='Kosongkan untuk semua departemen',
    )
    
    date_from = fields.Date(
        string='Dari Tanggal',
        help='Filter data mulai tanggal ini',
    )
    
    date_to = fields.Date(
        string='Sampai Tanggal',
        help='Filter data sampai tanggal ini',
    )
    
    # ===== Report Options =====
    report_title = fields.Char(
        string='Judul Laporan',
        default='Laporan Analytics Karyawan',
    )
    
    page_orientation = fields.Selection(
        selection=[
            ('portrait', 'Portrait'),
            ('landscape', 'Landscape'),
        ],
        string='Orientasi',
        default='landscape',
    )
    
    # ===== Computed Fields =====
    graph_count = fields.Integer(
        string='Jumlah Grafik',
        compute='_compute_graph_count',
        store=True,
    )
    
    selected_graphs_display = fields.Char(
        string='Grafik Terpilih',
        compute='_compute_selected_graphs_display',
    )
    
    # ===== Constraints =====
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Nama konfigurasi harus unik!'),
    ]
    
    # ===== Compute Methods =====
    
    @api.depends(
        'include_g01', 'include_g02', 'include_g03', 'include_g04',
        'include_g06', 'include_g08', 'include_g09', 'include_g10',
        'include_g13', 'include_g14', 'include_g16', 'include_g20', 'include_g21'
    )
    def _compute_graph_count(self):
        """Menghitung jumlah grafik yang dipilih."""
        for record in self:
            record.graph_count = len(record.get_selected_graph_codes())
    
    @api.depends(
        'include_g01', 'include_g02', 'include_g03', 'include_g04',
        'include_g06', 'include_g08', 'include_g09', 'include_g10',
        'include_g13', 'include_g14', 'include_g16', 'include_g20', 'include_g21'
    )
    def _compute_selected_graphs_display(self):
        """Menampilkan daftar grafik terpilih."""
        for record in self:
            codes = record.get_selected_graph_codes()
            names = [GRAPH_REGISTRY.get(code, {}).get('name', code) for code in codes]
            record.selected_graphs_display = ', '.join(names) if names else 'Tidak ada grafik dipilih'
    
    # ===== Validation =====
    
    @api.constrains(
        'include_g01', 'include_g02', 'include_g03', 'include_g04',
        'include_g06', 'include_g08', 'include_g09', 'include_g10',
        'include_g13', 'include_g14', 'include_g16', 'include_g20', 'include_g21'
    )
    def _check_graph_selection(self):
        """Validasi minimal 1 grafik harus dipilih."""
        for record in self:
            if not record.get_selected_graph_codes():
                raise ValidationError(_('Minimal 1 grafik harus dipilih!'))
    
    @api.constrains('graph_count')
    def _check_max_graphs(self):
        """Validasi maksimal 8 grafik per export."""
        for record in self:
            if record.graph_count > 8:
                raise ValidationError(_('Maksimal 8 grafik dapat dipilih untuk satu export!'))
    
    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        """Validasi range tanggal."""
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise ValidationError(_('Tanggal mulai tidak boleh lebih besar dari tanggal akhir!'))
    
    # ===== Helper Methods =====
    
    def get_selected_graph_codes(self):
        """
        Mendapatkan list kode grafik yang dipilih.
        
        Returns:
            list: List kode grafik (misal: ['G01', 'G02', 'G06'])
        """
        self.ensure_one()
        codes = []
        
        graph_fields = {
            'include_g01': 'G01',
            'include_g02': 'G02',
            'include_g03': 'G03',
            'include_g04': 'G04',
            'include_g06': 'G06',
            'include_g08': 'G08',
            'include_g09': 'G09',
            'include_g10': 'G10',
            'include_g13': 'G13',
            'include_g14': 'G14',
            'include_g16': 'G16',
            'include_g20': 'G20',
            'include_g21': 'G21',
        }
        
        for field_name, graph_code in graph_fields.items():
            if getattr(self, field_name, False):
                codes.append(graph_code)
        
        return codes
    
    def get_selected_graphs(self):
        """
        Mendapatkan list definisi grafik yang dipilih.
        
        Returns:
            list: List dict definisi grafik
        """
        self.ensure_one()
        codes = self.get_selected_graph_codes()
        return [GRAPH_REGISTRY[code] for code in codes if code in GRAPH_REGISTRY]
    
    def get_filter_domain(self):
        """
        Mendapatkan domain filter berdasarkan konfigurasi.
        
        Returns:
            list: Domain untuk filter employees
        """
        self.ensure_one()
        domain = [('active', '=', True)]
        
        if self.filter_department_ids:
            domain.append(('department_id', 'in', self.filter_department_ids.ids))
        
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        
        return domain
    
    # ===== Action Methods =====
    
    def action_open_export_wizard(self):
        """Membuka wizard export dengan konfigurasi ini."""
        self.ensure_one()
        return {
            'name': _('Export Grafik ke PDF'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.export.graph.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_config_id': self.id,
            },
        }
    
    def action_preview(self):
        """Preview grafik yang akan diekspor."""
        self.ensure_one()
        # TODO: Implementasi preview
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Preview'),
                'message': _('Preview akan menampilkan %s grafik') % self.graph_count,
                'type': 'info',
                'sticky': False,
            }
        }
