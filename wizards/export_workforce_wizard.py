# -*- coding: utf-8 -*-
"""
Wizard: hr.employee.export.workforce.wizard
Wizard untuk export workforce analytics ke PDF (PRD v1.1).

Wizard ini menyediakan antarmuka untuk:
- Memilih grafik workforce analytics (WA01-WA04)
- Mengatur snapshot date dan filter unit
- Preview dan generate PDF laporan eksekutif
"""

import base64
import logging
from datetime import date, datetime, timedelta
from calendar import monthrange

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from ..models.graph_registry import GRAPH_REGISTRY, get_workforce_analytics_graphs

_logger = logging.getLogger(__name__)


class HrEmployeeExportWorkforceWizard(models.TransientModel):
    """
    Wizard untuk export workforce analytics ke PDF.
    
    Fitur:
    - Pilih grafik dari workforce analytics registry
    - Select snapshot date (periode cut-off)
    - Filter by unit/departemen
    - Layout options (executive summary, dll)
    - Export atau preview PDF
    """
    
    _name = 'hr.employee.export.workforce.wizard'
    _description = 'Wizard Export Workforce Analytics PDF'
    
    # ===== Snapshot Selection =====
    
    snapshot_date = fields.Date(
        string='Tanggal Snapshot',
        required=True,
        default=lambda self: self._default_snapshot_date(),
        help='Pilih akhir bulan untuk data snapshot. '
             'Data akan diambil berdasarkan snapshot pada tanggal ini.',
    )
    
    snapshot_available = fields.Boolean(
        string='Snapshot Tersedia',
        compute='_compute_snapshot_available',
    )
    
    snapshot_warning = fields.Char(
        string='Peringatan Snapshot',
        compute='_compute_snapshot_available',
    )
    
    # ===== Graph Selection =====
    
    include_wa01 = fields.Boolean(
        string='Payroll vs Non-Payroll per Unit',
        default=True,
        help='Bar chart: Perbandingan karyawan payroll dan non-payroll per unit',
    )
    
    include_wa02 = fields.Boolean(
        string='Total Karyawan per Unit',
        default=True,
        help='Bar chart: Total seluruh karyawan per unit (MANDATORY untuk Executive Summary)',
    )
    
    include_wa03 = fields.Boolean(
        string='Trend Workforce Bulanan',
        default=True,
        help='Line chart: Snapshot jumlah karyawan per bulan (12 bulan terakhir)',
    )
    
    include_wa04 = fields.Boolean(
        string='Distribusi Status Kepegawaian',
        default=True,
        help='Pie chart: Distribusi status (Tetap, PKWT, SPK, THL, HJU, PNS DPK)',
    )
    
    # ===== Filter Options =====
    
    unit_ids = fields.Many2many(
        comodel_name='hr.department',
        relation='export_workforce_wizard_unit_rel',
        column1='wizard_id',
        column2='unit_id',
        string='Filter Unit/Departemen',
        help='Kosongkan untuk semua unit',
    )
    
    # ===== Layout Options =====
    
    layout_type = fields.Selection(
        selection=[
            ('executive_summary', 'Executive Summary'),
            ('full_report', 'Laporan Lengkap'),
            ('single_graphs', 'Grafik Terpisah'),
        ],
        string='Tipe Layout',
        default='executive_summary',
        required=True,
    )
    
    include_cover = fields.Boolean(
        string='Sertakan Halaman Cover',
        default=True,
    )
    
    include_kpi_summary = fields.Boolean(
        string='Sertakan Ringkasan KPI',
        default=True,
    )
    
    report_title = fields.Char(
        string='Judul Laporan',
        default='Laporan Workforce Analytics',
    )
    
    report_subtitle = fields.Char(
        string='Subjudul',
        compute='_compute_report_subtitle',
    )
    
    # ===== Output =====
    
    state = fields.Selection(
        selection=[
            ('config', 'Konfigurasi'),
            ('preview', 'Preview'),
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
    
    # ===== Computed Info =====
    
    graph_count = fields.Integer(
        string='Jumlah Grafik',
        compute='_compute_graph_count',
    )
    
    preview_info = fields.Html(
        string='Info Preview',
        compute='_compute_preview_info',
    )
    
    # ===== Default Methods =====
    
    @api.model
    def _default_snapshot_date(self):
        """Get default snapshot date (last day of previous month)."""
        today = date.today()
        first_of_month = today.replace(day=1)
        last_day_prev_month = first_of_month - timedelta(days=1)
        return last_day_prev_month
    
    # ===== Compute Methods =====
    
    @api.depends('snapshot_date')
    def _compute_snapshot_available(self):
        """Check if snapshot data is available for selected date."""
        Snapshot = self.env['hr.employee.snapshot']
        
        for record in self:
            if record.snapshot_date:
                exists = Snapshot.check_snapshot_exists(
                    record.snapshot_date.year,
                    record.snapshot_date.month
                )
                record.snapshot_available = exists
                
                if not exists:
                    record.snapshot_warning = _(
                        'Snapshot untuk periode %s/%s belum tersedia. '
                        'Silakan generate snapshot terlebih dahulu atau gunakan data real-time.'
                    ) % (record.snapshot_date.month, record.snapshot_date.year)
                else:
                    record.snapshot_warning = False
            else:
                record.snapshot_available = False
                record.snapshot_warning = _('Pilih tanggal snapshot')
    
    @api.depends('include_wa01', 'include_wa02', 'include_wa03', 'include_wa04')
    def _compute_graph_count(self):
        """Count selected graphs."""
        for record in self:
            count = 0
            if record.include_wa01:
                count += 1
            if record.include_wa02:
                count += 1
            if record.include_wa03:
                count += 1
            if record.include_wa04:
                count += 1
            record.graph_count = count
    
    @api.depends('snapshot_date')
    def _compute_report_subtitle(self):
        """Generate subtitle based on snapshot date."""
        month_names = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        for record in self:
            if record.snapshot_date:
                month = month_names.get(record.snapshot_date.month, str(record.snapshot_date.month))
                record.report_subtitle = f'Periode {month} {record.snapshot_date.year}'
            else:
                record.report_subtitle = ''
    
    @api.depends('graph_count', 'unit_ids', 'snapshot_date', 'snapshot_available', 'layout_type')
    def _compute_preview_info(self):
        """Generate preview info HTML."""
        for record in self:
            lines = []
            
            # Graph info
            lines.append(f'<p><strong>📊 Grafik:</strong> {record.graph_count} grafik dipilih</p>')
            
            # Snapshot info
            if record.snapshot_date:
                status = '✅' if record.snapshot_available else '⚠️'
                lines.append(f'<p><strong>📅 Snapshot:</strong> {status} {record.snapshot_date.strftime("%B %Y")}</p>')
            
            # Filter info
            if record.unit_ids:
                units = ', '.join(record.unit_ids.mapped('name')[:3])
                if len(record.unit_ids) > 3:
                    units += f' (+{len(record.unit_ids) - 3} lainnya)'
                lines.append(f'<p><strong>🏢 Unit:</strong> {units}</p>')
            else:
                lines.append('<p><strong>🏢 Unit:</strong> Semua unit</p>')
            
            # Layout info
            layout_names = {
                'executive_summary': 'Executive Summary',
                'full_report': 'Laporan Lengkap',
                'single_graphs': 'Grafik Terpisah',
            }
            lines.append(f'<p><strong>📄 Layout:</strong> {layout_names.get(record.layout_type, record.layout_type)}</p>')
            
            # Warning if snapshot not available
            if not record.snapshot_available and record.snapshot_date:
                lines.append('<p style="color: #e74c3c;">⚠️ <em>Snapshot belum tersedia. Data akan menggunakan fallback real-time.</em></p>')
            
            record.preview_info = ''.join(lines)
    
    # ===== Constraint Methods =====
    
    @api.constrains('graph_count')
    def _check_graph_count(self):
        """Validate at least 1 graph is selected."""
        for record in self:
            if record.graph_count < 1:
                raise ValidationError(_('Minimal 1 grafik harus dipilih!'))
            if record.graph_count > 6:
                raise ValidationError(_('Maksimal 6 grafik per export!'))
    
    @api.constrains('layout_type', 'include_wa02')
    def _check_executive_summary(self):
        """WA02 is mandatory for executive summary."""
        for record in self:
            if record.layout_type == 'executive_summary' and not record.include_wa02:
                raise ValidationError(_(
                    'Grafik "Total Karyawan per Unit" (WA02) wajib disertakan '
                    'untuk layout Executive Summary!'
                ))
    
    # ===== Helper Methods =====
    
    def _get_selected_graph_codes(self):
        """Get list of selected graph codes."""
        codes = []
        if self.include_wa01:
            codes.append('WA01')
        if self.include_wa02:
            codes.append('WA02')
        if self.include_wa03:
            codes.append('WA03')
        if self.include_wa04:
            codes.append('WA04')
        return codes
    
    def _get_selected_graphs(self):
        """Get list of selected graph definitions."""
        codes = self._get_selected_graph_codes()
        return [GRAPH_REGISTRY[code] for code in codes if code in GRAPH_REGISTRY]
    
    def _get_analytics_data(self):
        """
        Get analytics data dari service.
        
        Returns semua data yang diperlukan untuk grafik yang dipilih.
        """
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        unit_ids = self.unit_ids.ids if self.unit_ids else None
        
        data = {
            'snapshot_date': self.snapshot_date,
            'snapshot_available': self.snapshot_available,
            'kpi': {},
            'graphs': {},
        }
        
        # Get KPI summary
        if self.include_kpi_summary:
            data['kpi'] = service.get_kpi_summary(self.snapshot_date, unit_ids)
        
        # Get data for each selected graph
        if self.include_wa01:
            data['graphs']['WA01'] = service.payroll_vs_non_payroll(self.snapshot_date, unit_ids)
        
        if self.include_wa02:
            data['graphs']['WA02'] = service.total_employee_per_unit(self.snapshot_date, unit_ids)
        
        if self.include_wa03:
            # WA03 uses single unit_id and year
            unit_id = self.unit_ids[0].id if self.unit_ids and len(self.unit_ids) == 1 else None
            data['graphs']['WA03'] = service.workforce_snapshot_trend(
                unit_id=unit_id,
                year=self.snapshot_date.year
            )
        
        if self.include_wa04:
            data['graphs']['WA04'] = service.employment_status_distribution(self.snapshot_date, unit_ids)
        
        return data
    
    # ===== Action Methods =====
    
    def action_generate_snapshot(self):
        """Generate snapshot untuk periode yang dipilih."""
        self.ensure_one()
        
        if not self.snapshot_date:
            raise UserError(_('Pilih tanggal snapshot terlebih dahulu!'))
        
        Snapshot = self.env['hr.employee.snapshot']
        count = Snapshot.generate_monthly_snapshot(
            year=self.snapshot_date.year,
            month=self.snapshot_date.month,
            force=True
        )
        
        if count > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Snapshot Generated'),
                    'message': _('%d employee snapshots created for %s/%s') % (
                        count,
                        self.snapshot_date.month,
                        self.snapshot_date.year
                    ),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Info'),
                    'message': _('No employees found to create snapshot'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
    
    def action_preview(self):
        """Preview laporan (render to screen)."""
        self.ensure_one()
        self._validate_before_export()
        
        # For now, just show notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Preview'),
                'message': _('Preview akan ditampilkan di tab baru...'),
                'type': 'info',
            }
        }
    
    def action_export_pdf(self):
        """Export laporan ke PDF."""
        self.ensure_one()
        self._validate_before_export()
        
        import time
        start_time = time.time()
        
        try:
            # Get analytics data
            analytics_data = self._get_analytics_data()
            
            # Render charts
            from ..services.advanced_graph_renderer import AdvancedGraphRenderer
            renderer = AdvancedGraphRenderer(self.env)
            
            charts_config = []
            for code in self._get_selected_graph_codes():
                if code in analytics_data['graphs']:
                    charts_config.append({
                        'graph_def': GRAPH_REGISTRY.get(code, {}),
                        'data': analytics_data['graphs'][code],
                    })
            
            rendered_charts = renderer.render_multiple_charts(charts_config, output_format='png')
            
            # Generate PDF using QWeb
            pdf_content = self._generate_pdf(analytics_data, rendered_charts)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"workforce_analytics_{timestamp}.pdf"
            
            # Log export
            self._log_export(len(self._get_selected_graph_codes()), duration)
            
            # Update wizard state
            self.write({
                'state': 'done',
                'output_file': base64.b64encode(pdf_content),
                'output_filename': filename,
            })
            
            # Return download action
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content?model={self._name}&id={self.id}&field=output_file&filename_field=output_filename&download=true',
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error(f"Error exporting workforce analytics PDF: {e}", exc_info=True)
            raise UserError(_('Gagal export PDF: %s') % str(e))
    
    def _validate_before_export(self):
        """Validate before export."""
        if self.graph_count < 1:
            raise UserError(_('Minimal 1 grafik harus dipilih!'))
        
        if self.graph_count > 6:
            raise UserError(_('Maksimal 6 grafik per export untuk performa optimal!'))
        
        if not self.snapshot_date:
            raise UserError(_('Tanggal snapshot harus diisi!'))
        
        if self.layout_type == 'executive_summary' and not self.include_wa02:
            raise UserError(_(
                'Grafik "Total Karyawan per Unit" (WA02) wajib untuk Executive Summary!'
            ))
    
    def _generate_pdf(self, analytics_data, rendered_charts):
        """
        Generate PDF dari analytics data dan rendered charts.
        
        Args:
            analytics_data: Data dari _get_analytics_data()
            rendered_charts: List dari AdvancedGraphRenderer.render_multiple_charts()
            
        Returns:
            bytes: PDF content
        """
        # Prepare report data
        report_data = {
            'title': self.report_title,
            'subtitle': self.report_subtitle,
            'snapshot_date': self.snapshot_date,
            'generated_at': datetime.now(),
            'user': self.env.user.name,
            'company': self.env.company,  # Pass recordset, not string
            'company_name': self.env.company.name,  # String for display
            'include_cover': self.include_cover,
            'include_kpi_summary': self.include_kpi_summary,
            'layout_type': self.layout_type,
            'kpi': analytics_data.get('kpi', {}),
            'charts': rendered_charts,
            'unit_filter': ', '.join(self.unit_ids.mapped('name')) if self.unit_ids else 'Semua Unit',
        }
        
        # Render PDF using QWeb
        report = self.env.ref('yhc_employee_export.action_report_workforce_analytics')
        pdf_content, _ = report._render_qweb_pdf(
            'yhc_employee_export.report_workforce_analytics_template',
            res_ids=self.ids,
            data=report_data
        )
        
        return pdf_content
    
    def _log_export(self, graph_count, duration):
        """Log export activity."""
        try:
            AuditLog = self.env['hr.employee.export.audit.log'].sudo()
            AuditLog.create({
                'export_type': 'workforce_analytics_pdf',
                'record_count': graph_count,
                'status': 'success',
                'duration': duration,
                'notes': f"Layout: {self.layout_type}, Snapshot: {self.snapshot_date}",
            })
        except Exception as e:
            _logger.warning(f"Failed to create audit log: {e}")
    
    def action_back(self):
        """Go back to config state."""
        self.write({'state': 'config'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
