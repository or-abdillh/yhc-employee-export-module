# -*- coding: utf-8 -*-
"""
Wizard: Workforce Report Wizard
Official Workforce Report Generator (PRD v1.1 - Workforce Report Engine).

CRITICAL RULES:
1. Snapshot-based ONLY - No real-time data
2. Fixed structure - NOT configurable
3. User can only select: Month + Year
4. No chart selection
5. No free filters
6. Report structure is LOCKED by system
"""

import base64
import logging
from datetime import date, datetime
from calendar import monthrange
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


# Month options for selection
MONTH_SELECTION = [
    (1, 'Januari'),
    (2, 'Februari'),
    (3, 'Maret'),
    (4, 'April'),
    (5, 'Mei'),
    (6, 'Juni'),
    (7, 'Juli'),
    (8, 'Agustus'),
    (9, 'September'),
    (10, 'Oktober'),
    (11, 'November'),
    (12, 'Desember'),
]


class WorkforceReportWizard(models.TransientModel):
    """
    Wizard for generating Official Workforce Report.
    
    This wizard provides a STRICT interface:
    - User selects Month and Year ONLY
    - System validates snapshot availability
    - System generates fixed-structure PDF
    
    NO OPTIONS ALLOWED:
    - No chart selection
    - No layout options
    - No filter options
    - No field selection
    """
    
    _name = 'workforce.report.wizard'
    _description = 'Workforce Report Wizard'
    
    # ===== Period Selection (ONLY ALLOWED INPUT) =====
    
    report_month = fields.Selection(
        selection=[(str(m[0]), m[1]) for m in MONTH_SELECTION],
        string='Bulan',
        required=True,
        default=lambda self: str(self._default_month()),
        help='Pilih bulan untuk laporan.',
    )
    
    report_year = fields.Integer(
        string='Tahun',
        required=True,
        default=lambda self: self._default_year(),
        help='Pilih tahun untuk laporan.',
    )
    
    # ===== Snapshot Validation =====
    
    snapshot_available = fields.Boolean(
        string='Snapshot Tersedia',
        compute='_compute_snapshot_status',
    )
    
    snapshot_count = fields.Integer(
        string='Jumlah Data Snapshot',
        compute='_compute_snapshot_status',
    )
    
    snapshot_message = fields.Char(
        string='Status Snapshot',
        compute='_compute_snapshot_status',
    )
    
    # ===== State & Output =====
    
    state = fields.Selection(
        selection=[
            ('select', 'Pilih Periode'),
            ('ready', 'Siap Generate'),
            ('done', 'Selesai'),
        ],
        string='Status',
        default='select',
    )
    
    output_file = fields.Binary(
        string='File Laporan',
        readonly=True,
    )
    
    output_filename = fields.Char(
        string='Nama File',
        readonly=True,
    )
    
    # ===== Display Info =====
    
    period_display = fields.Char(
        string='Periode',
        compute='_compute_period_display',
    )
    
    company_name = fields.Char(
        string='Organisasi',
        compute='_compute_company_info',
    )
    
    company_logo = fields.Binary(
        string='Logo',
        compute='_compute_company_info',
    )
    
    # ===== Default Methods =====
    
    @api.model
    def _default_month(self):
        """Get default month (previous month)."""
        today = date.today()
        if today.month == 1:
            return 12
        return today.month - 1
    
    @api.model
    def _default_year(self):
        """Get default year."""
        today = date.today()
        if today.month == 1:
            return today.year - 1
        return today.year
    
    # ===== Compute Methods =====
    
    @api.depends('report_month', 'report_year')
    def _compute_snapshot_status(self):
        """Check snapshot availability for selected period."""
        Snapshot = self.env['hr.employee.snapshot']
        
        for record in self:
            if record.report_month and record.report_year:
                month = int(record.report_month)
                year = record.report_year
                
                count = Snapshot.search_count([
                    ('snapshot_year', '=', year),
                    ('snapshot_month', '=', month),
                    ('is_active', '=', True),
                ])
                
                record.snapshot_count = count
                record.snapshot_available = count > 0
                
                if count > 0:
                    record.snapshot_message = _(
                        '✅ Snapshot tersedia: %d data karyawan'
                    ) % count
                else:
                    record.snapshot_message = _(
                        '❌ Snapshot TIDAK tersedia untuk periode ini. '
                        'Laporan TIDAK DAPAT digenerate.'
                    )
            else:
                record.snapshot_count = 0
                record.snapshot_available = False
                record.snapshot_message = _('Pilih bulan dan tahun')
    
    @api.depends('report_month', 'report_year')
    def _compute_period_display(self):
        """Compute display name for period."""
        month_names = dict(MONTH_SELECTION)
        
        for record in self:
            if record.report_month and record.report_year:
                month_name = month_names.get(int(record.report_month), '')
                record.period_display = f"{month_name} {record.report_year}"
            else:
                record.period_display = ''
    
    @api.depends()
    def _compute_company_info(self):
        """Get company info for header."""
        for record in self:
            record.company_name = self.env.company.name
            record.company_logo = self.env.company.logo
    
    # ===== Report Data Methods =====
    
    def get_report_data(self):
        """
        Get complete report data for QWeb template.
        
        This method is called by the QWeb template to get all data
        needed for rendering the report.
        
        Returns:
            dict: Complete report data with charts
        """
        self.ensure_one()
        
        month = int(self.report_month)
        year = self.report_year
        
        # Get report service
        service = self.env['workforce.report.service'].get_service()
        
        # Generate complete report data
        report_data = service.generate_complete_report_data(year, month)
        
        # Add chart images
        report_data = self._prepare_chart_images(report_data)
        
        # Add meta info
        report_data['company_name'] = self.company_name
        report_data['company_logo'] = self.company_logo
        report_data['generated_by'] = self.env.user.name
        report_data['generated_at'] = fields.Datetime.now()
        
        return report_data
    
    # ===== Action Methods =====

    def action_validate_period(self):
        """
        Validate selected period and check snapshot availability.
        
        STRICT VALIDATION:
        - Snapshot MUST exist
        - No fallback to real-time data
        """
        self.ensure_one()
        
        if not self.snapshot_available:
            raise ValidationError(_(
                'LAPORAN TIDAK DAPAT DIGENERATE\n\n'
                'Snapshot untuk periode %s tidak tersedia.\n\n'
                'Workforce Report Engine WAJIB menggunakan data snapshot.\n'
                'Silakan generate snapshot terlebih dahulu melalui:\n'
                'Menu > Konfigurasi > Employee Snapshots > Generate Snapshot'
            ) % self.period_display)
        
        self.state = 'ready'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_generate_report(self):
        """
        Generate the Official Workforce Report PDF.
        
        PROCESS:
        1. Validate snapshot exists
        2. Get report service
        3. Generate complete data
        4. Render QWeb PDF
        5. Return download
        """
        self.ensure_one()
        
        month = int(self.report_month)
        year = self.report_year
        
        # Double-check snapshot availability (FAIL SAFE)
        if not self.snapshot_available:
            raise ValidationError(_(
                'CRITICAL ERROR: Snapshot tidak tersedia.\n'
                'Laporan TIDAK DAPAT digenerate tanpa data snapshot.'
            ))
        
        _logger.info(f"Generating Workforce Report for {month}/{year}")
        
        try:
            # Get report service
            service = self.env['workforce.report.service'].get_service()
            
            # Generate complete report data
            report_data = service.generate_complete_report_data(year, month)
            
            # Generate PDF using QWeb
            pdf_content = self._render_report_pdf(report_data)
            
            # Encode and store
            self.output_file = base64.b64encode(pdf_content)
            self.output_filename = f"Workforce_Report_{year}{month:02d}.pdf"
            self.state = 'done'
            
            _logger.info(f"Workforce Report generated successfully: {self.output_filename}")
            
            # Log audit
            self._log_report_generation(report_data)
            
        except ValidationError as e:
            raise
        except Exception as e:
            _logger.error(f"Error generating workforce report: {str(e)}")
            raise UserError(_(
                'Gagal generate laporan:\n%s'
            ) % str(e))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def _render_report_pdf(self, report_data):
        """
        Render report data to PDF using QWeb.
        
        Args:
            report_data: Complete report data from service
            
        Returns:
            bytes: PDF content
        """
        # Prepare chart images as base64 for PDF
        report_data = self._prepare_chart_images(report_data)
        
        # Find report action - try multiple methods for robustness
        report_action = None
        
        # Method 1: Try using external ID (env.ref)
        try:
            report_action = self.env.ref(
                'yhc_employee_export.action_report_workforce_official',
                raise_if_not_found=False
            )
        except (ValueError, Exception) as e:
            _logger.warning(f"Could not find report via env.ref: {e}")
        
        # Method 2: Search by report_name if env.ref fails
        if not report_action:
            report_action = self.env['ir.actions.report'].search([
                ('report_name', '=', 'yhc_employee_export.report_workforce_official_template')
            ], limit=1)
            
            if report_action:
                _logger.info(f"Found report action via search: {report_action.name}")
        
        # Method 3: Search by model if still not found
        if not report_action:
            report_action = self.env['ir.actions.report'].search([
                ('model', '=', 'workforce.report.wizard'),
                ('report_type', '=', 'qweb-pdf'),
                ('name', 'ilike', 'workforce')
            ], limit=1)
            
            if report_action:
                _logger.info(f"Found report action via model search: {report_action.name}")
        
        # Raise error if report action not found at all
        if not report_action:
            raise UserError(_(
                "Report action 'Official Workforce Report' tidak ditemukan.\n\n"
                "Kemungkinan penyebab:\n"
                "1. Module belum di-upgrade dengan benar\n"
                "2. File report XML tidak terload\n\n"
                "Solusi:\n"
                "1. Upgrade module via Apps menu\n"
                "2. Atau jalankan: odoo -u yhc_employee_export -d database_name\n"
                "3. Restart Odoo service"
            ))
        
        # Generate PDF
        pdf_content, content_type = report_action._render_qweb_pdf(
            report_action.id,
            res_ids=[self.id],
            data={'report_data': report_data}
        )
        
        return pdf_content
    
    def _prepare_chart_images(self, report_data):
        """
        Generate chart images for PDF embedding.
        
        Uses matplotlib to create SVG/PNG charts.
        
        Args:
            report_data: Report data structure
            
        Returns:
            dict: Report data with chart images added
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            _logger.warning("matplotlib not available, charts will be rendered as tables")
            return report_data
        
        # Chart 1: Payroll vs Non-Payroll Bar Chart
        chart_data = report_data['section_2_chart']
        report_data['chart_1_image'] = self._generate_bar_chart(
            chart_data['labels'],
            chart_data['datasets'],
            chart_data['title']
        )
        
        # Chart 2: Total Workforce Bar Chart
        chart_data = report_data['section_3_chart']
        report_data['chart_2_image'] = self._generate_horizontal_bar_chart(
            chart_data['labels'],
            chart_data['datasets'][0]['data'],
            chart_data['datasets'][0]['backgroundColor'],
            chart_data['title']
        )
        
        # Chart 3: Employment Status Pie Chart
        chart_data = report_data['section_5_chart']
        report_data['chart_3_image'] = self._generate_pie_chart(
            chart_data['labels'],
            chart_data['data'],
            chart_data['colors'],
            chart_data['title']
        )
        
        return report_data
    
    def _generate_bar_chart(self, labels, datasets, title):
        """Generate grouped bar chart as base64 image."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            x = np.arange(len(labels))
            width = 0.35
            
            for i, dataset in enumerate(datasets):
                offset = width * (i - len(datasets) / 2 + 0.5)
                bars = ax.bar(
                    x + offset,
                    dataset['data'],
                    width,
                    label=dataset['label'],
                    color=dataset.get('backgroundColor', '#714B67')
                )
                
                # Add value labels
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.annotate(
                            f'{int(height)}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center',
                            va='bottom',
                            fontsize=8
                        )
            
            ax.set_xlabel('Unit')
            ax.set_ylabel('Jumlah Karyawan')
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            _logger.error(f"Error generating bar chart: {e}")
            return None
    
    def _generate_horizontal_bar_chart(self, labels, data, colors, title):
        """Generate horizontal bar chart as base64 image."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(12, max(6, len(labels) * 0.4)))
            
            y_pos = np.arange(len(labels))
            
            # Handle colors (can be list or single color)
            if isinstance(colors, list):
                bar_colors = colors[:len(labels)]
            else:
                bar_colors = colors
            
            bars = ax.barh(y_pos, data, color=bar_colors)
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax.annotate(
                        f'{int(width)}',
                        xy=(width, bar.get_y() + bar.get_height() / 2),
                        xytext=(5, 0),
                        textcoords="offset points",
                        ha='left',
                        va='center',
                        fontsize=9
                    )
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=10)
            ax.set_xlabel('Jumlah Karyawan')
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)
            
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            _logger.error(f"Error generating horizontal bar chart: {e}")
            return None
    
    def _generate_pie_chart(self, labels, data, colors, title):
        """Generate pie chart as base64 image."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # Filter out zero values
            filtered = [(l, d, c) for l, d, c in zip(labels, data, colors) if d > 0]
            if not filtered:
                return None
            
            labels_f, data_f, colors_f = zip(*filtered)
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            wedges, texts, autotexts = ax.pie(
                data_f,
                labels=labels_f,
                colors=colors_f,
                autopct='%1.1f%%',
                startangle=90,
                pctdistance=0.75
            )
            
            # Style the labels
            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            # Add legend
            ax.legend(
                wedges,
                [f"{l}: {d}" for l, d in zip(labels_f, data_f)],
                title="Status",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1)
            )
            
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            _logger.error(f"Error generating pie chart: {e}")
            return None
    
    def _log_report_generation(self, report_data):
        """Log report generation to audit log."""
        try:
            self.env['hr.employee.export.audit.log'].sudo().create({
                'user_id': self.env.user.id,
                'action': 'export',
                'model': 'workforce.report.wizard',
                'record_count': report_data['validation']['total_employees'],
                'export_format': 'pdf',
                'description': f"Workforce Report - {report_data['header']['period_name']}",
            })
        except Exception as e:
            _logger.warning(f"Could not create audit log: {e}")
    
    def action_back(self):
        """Go back to period selection."""
        self.ensure_one()
        self.state = 'select'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_generate_snapshot(self):
        """Action to generate snapshot for the selected period."""
        self.ensure_one()
        
        month = int(self.report_month)
        year = self.report_year
        
        Snapshot = self.env['hr.employee.snapshot']
        count = Snapshot.generate_monthly_snapshot(year=year, month=month)
        
        if count > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Snapshot Generated'),
                    'message': _('%d employee snapshots created for %s %d') % (
                        count,
                        dict(MONTH_SELECTION).get(month, ''),
                        year
                    ),
                    'sticky': False,
                    'type': 'success',
                    'next': {
                        'type': 'ir.actions.act_window',
                        'res_model': self._name,
                        'res_id': self.id,
                        'view_mode': 'form',
                        'target': 'new',
                    }
                }
            }
        else:
            raise UserError(_(
                'Tidak ada karyawan yang dapat di-snapshot.\n'
                'Pastikan data karyawan tersedia dan memiliki departemen.'
            ))
