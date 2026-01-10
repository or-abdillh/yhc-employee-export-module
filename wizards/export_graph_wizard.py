# -*- coding: utf-8 -*-
"""
Wizard: hr.employee.export.graph.wizard
Wizard untuk export grafik dashboard ke PDF.

Wizard ini menyediakan antarmuka untuk:
- Memilih grafik yang akan diekspor
- Mengatur filter dan layout
- Preview dan generate PDF
"""

import base64
import logging
from datetime import date, datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from ..models.graph_registry import GRAPH_REGISTRY, GRAPH_CATEGORIES

_logger = logging.getLogger(__name__)


class HrEmployeeExportGraphWizard(models.TransientModel):
    """
    Wizard untuk export grafik ke PDF.
    
    Memungkinkan user untuk:
    - Memilih grafik dari registry
    - Mengatur filter (departemen, tanggal)
    - Memilih layout PDF
    - Export atau preview hasilnya
    """
    
    _name = 'hr.employee.export.graph.wizard'
    _description = 'Wizard Export Grafik ke PDF'
    
    # ===== Config Selection =====
    use_config = fields.Boolean(
        string='Gunakan Konfigurasi Tersimpan',
        default=False,
    )
    
    config_id = fields.Many2one(
        comodel_name='hr.employee.export.graph.config',
        string='Konfigurasi',
        domain="[('active', '=', True)]",
    )
    
    # ===== Graph Selection (Custom) =====
    # Demografis
    include_g01 = fields.Boolean(string='Distribusi Gender', default=True)
    include_g02 = fields.Boolean(string='Distribusi Usia', default=True)
    include_g03 = fields.Boolean(string='Distribusi Agama', default=False)
    include_g04 = fields.Boolean(string='Status Pernikahan', default=False)
    
    # Ketenagakerjaan
    include_g06 = fields.Boolean(string='Karyawan per Departemen', default=True)
    include_g08 = fields.Boolean(string='Distribusi Golongan', default=False)
    include_g09 = fields.Boolean(string='Distribusi Grade', default=False)
    include_g10 = fields.Boolean(string='Status Kepegawaian', default=True)
    include_g13 = fields.Boolean(string='Masa Kerja', default=True)
    include_g14 = fields.Boolean(string='Trend Rekrutmen', default=False)
    
    # Pendidikan & Pelatihan
    include_g16 = fields.Boolean(string='Level Pendidikan', default=True)
    include_g20 = fields.Boolean(string='Pelatihan per Jenis', default=False)
    include_g21 = fields.Boolean(string='Pelatihan per Metode', default=False)
    
    # ===== Filter Options =====
    department_ids = fields.Many2many(
        comodel_name='hr.department',
        relation='export_graph_wizard_department_rel',
        column1='wizard_id',
        column2='department_id',
        string='Filter Departemen',
        help='Kosongkan untuk semua departemen',
    )
    
    date_from = fields.Date(
        string='Dari Tanggal',
        default=lambda self: date.today().replace(month=1, day=1),
    )
    
    date_to = fields.Date(
        string='Sampai Tanggal',
        default=fields.Date.today,
    )
    
    # ===== Layout Options =====
    layout_type = fields.Selection(
        selection=[
            ('single_column', 'Satu Kolom (1 grafik per halaman)'),
            ('two_columns', 'Dua Kolom (2 grafik per halaman)'),
            ('executive_summary', 'Executive Summary'),
        ],
        string='Layout PDF',
        default='two_columns',
        required=True,
    )
    
    include_summary = fields.Boolean(
        string='Sertakan Ringkasan KPI',
        default=True,
    )
    
    include_cover = fields.Boolean(
        string='Sertakan Halaman Cover',
        default=True,
    )
    
    report_title = fields.Char(
        string='Judul Laporan',
        default='Laporan Analytics Karyawan',
    )
    
    # ===== Output =====
    state = fields.Selection(
        selection=[
            ('config', 'Konfigurasi'),
            ('done', 'Selesai'),
        ],
        string='Status',
        default='config',
    )
    
    output_file = fields.Binary(
        string='File PDF',
        readonly=True,
    )
    
    output_filename = fields.Char(
        string='Nama File',
        readonly=True,
    )
    
    # ===== Computed Fields =====
    graph_count = fields.Integer(
        string='Jumlah Grafik',
        compute='_compute_graph_count',
    )
    
    preview_info = fields.Text(
        string='Info Preview',
        compute='_compute_preview_info',
    )
    
    # ===== Compute Methods =====
    
    @api.depends(
        'use_config', 'config_id',
        'include_g01', 'include_g02', 'include_g03', 'include_g04',
        'include_g06', 'include_g08', 'include_g09', 'include_g10',
        'include_g13', 'include_g14', 'include_g16', 'include_g20', 'include_g21'
    )
    def _compute_graph_count(self):
        """Menghitung jumlah grafik yang dipilih."""
        for record in self:
            if record.use_config and record.config_id:
                record.graph_count = record.config_id.graph_count
            else:
                record.graph_count = len(record._get_selected_graph_codes())
    
    @api.depends('graph_count', 'department_ids', 'date_from', 'date_to')
    def _compute_preview_info(self):
        """Generate info preview."""
        for record in self:
            lines = []
            lines.append(f"📊 {record.graph_count} grafik akan diekspor")
            
            if record.department_ids:
                lines.append(f"📁 Filter: {', '.join(record.department_ids.mapped('name'))}")
            else:
                lines.append("📁 Filter: Semua departemen")
            
            if record.date_from and record.date_to:
                lines.append(f"📅 Periode: {record.date_from} - {record.date_to}")
            
            record.preview_info = '\n'.join(lines)
    
    # ===== Onchange Methods =====
    
    @api.onchange('use_config', 'config_id')
    def _onchange_config(self):
        """Load settings dari konfigurasi terpilih."""
        if self.use_config and self.config_id:
            config = self.config_id
            self.include_g01 = config.include_g01
            self.include_g02 = config.include_g02
            self.include_g03 = config.include_g03
            self.include_g04 = config.include_g04
            self.include_g06 = config.include_g06
            self.include_g08 = config.include_g08
            self.include_g09 = config.include_g09
            self.include_g10 = config.include_g10
            self.include_g13 = config.include_g13
            self.include_g14 = config.include_g14
            self.include_g16 = config.include_g16
            self.include_g20 = config.include_g20
            self.include_g21 = config.include_g21
            self.layout_type = config.layout_type
            self.include_summary = config.include_summary
            self.include_cover = config.include_cover
            self.report_title = config.report_title or 'Laporan Analytics Karyawan'
            self.department_ids = config.filter_department_ids
            self.date_from = config.date_from
            self.date_to = config.date_to
    
    # ===== Helper Methods =====
    
    def _get_selected_graph_codes(self):
        """Mendapatkan list kode grafik yang dipilih."""
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
    
    def _get_selected_graphs(self):
        """Mendapatkan list definisi grafik yang dipilih."""
        self.ensure_one()
        codes = self._get_selected_graph_codes()
        return [GRAPH_REGISTRY[code] for code in codes if code in GRAPH_REGISTRY]
    
    def _get_filter_domain(self):
        """Mendapatkan domain filter."""
        self.ensure_one()
        domain = [('active', '=', True)]
        
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        
        return domain
    
    # ===== Validation =====
    
    def _validate_export(self):
        """Validasi sebelum export."""
        self.ensure_one()
        
        graph_codes = self._get_selected_graph_codes()
        
        if not graph_codes:
            raise ValidationError(_('Minimal 1 grafik harus dipilih!'))
        
        if len(graph_codes) > 8:
            raise ValidationError(_('Maksimal 8 grafik dapat dipilih!'))
        
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Tanggal mulai tidak boleh lebih besar dari tanggal akhir!'))
    
    # ===== Action Methods =====
    
    def action_export_pdf(self):
        """Export grafik ke PDF."""
        self.ensure_one()
        self._validate_export()
        
        try:
            from ..services.export_graph_pdf import EmployeeExportGraphPdf
            
            # Get selected graphs
            graphs = self._get_selected_graphs()
            
            # Get filtered employees
            domain = self._get_filter_domain()
            employees = self.env['hr.employee'].sudo().search(domain)
            
            if not employees:
                raise UserError(_('Tidak ada data karyawan yang sesuai dengan filter!'))
            
            # Prepare export options
            options = {
                'layout_type': self.layout_type,
                'include_summary': self.include_summary,
                'include_cover': self.include_cover,
                'report_title': self.report_title,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'department_names': ', '.join(self.department_ids.mapped('name')) if self.department_ids else 'Semua',
            }
            
            # Initialize service and export
            service = EmployeeExportGraphPdf(self.env)
            pdf_content, filename = service.export(employees, graphs, options)
            
            # Save output
            self.write({
                'output_file': base64.b64encode(pdf_content),
                'output_filename': filename,
                'state': 'done',
            })
            
            # Return download action
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content?model={self._name}&id={self.id}&field=output_file&filename={filename}&download=true',
                'target': 'self',
            }
            
        except ImportError as e:
            _logger.error(f"Import error: {str(e)}")
            raise UserError(_('Module export tidak tersedia. Hubungi administrator.'))
        except Exception as e:
            _logger.error(f"Error exporting graph PDF: {str(e)}")
            raise UserError(_('Gagal membuat PDF: %s') % str(e))
    
    def action_preview(self):
        """Preview data yang akan diekspor."""
        self.ensure_one()
        self._validate_export()
        
        graphs = self._get_selected_graphs()
        domain = self._get_filter_domain()
        employees = self.env['hr.employee'].sudo().search(domain)
        
        message = _(
            "Preview Export Grafik:\n\n"
            "📊 Grafik: %s\n"
            "👥 Total Karyawan: %s\n"
            "📐 Layout: %s\n"
            "📅 Periode: %s - %s"
        ) % (
            ', '.join([g['name'] for g in graphs]),
            len(employees),
            dict(self._fields['layout_type'].selection).get(self.layout_type),
            self.date_from or 'Awal',
            self.date_to or 'Sekarang',
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Preview Export'),
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
    
    def action_save_config(self):
        """Simpan pengaturan sebagai konfigurasi baru."""
        self.ensure_one()
        self._validate_export()
        
        return {
            'name': _('Simpan Konfigurasi'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.export.graph.config',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_include_g01': self.include_g01,
                'default_include_g02': self.include_g02,
                'default_include_g03': self.include_g03,
                'default_include_g04': self.include_g04,
                'default_include_g06': self.include_g06,
                'default_include_g08': self.include_g08,
                'default_include_g09': self.include_g09,
                'default_include_g10': self.include_g10,
                'default_include_g13': self.include_g13,
                'default_include_g14': self.include_g14,
                'default_include_g16': self.include_g16,
                'default_include_g20': self.include_g20,
                'default_include_g21': self.include_g21,
                'default_layout_type': self.layout_type,
                'default_include_summary': self.include_summary,
                'default_include_cover': self.include_cover,
                'default_report_title': self.report_title,
                'default_filter_department_ids': [(6, 0, self.department_ids.ids)],
                'default_date_from': self.date_from,
                'default_date_to': self.date_to,
            }
        }
    
    def action_back(self):
        """Kembali ke state config."""
        self.ensure_one()
        self.write({
            'state': 'config',
            'output_file': False,
            'output_filename': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
