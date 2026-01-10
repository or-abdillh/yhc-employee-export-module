# -*- coding: utf-8 -*-
"""
Wizard: hr.employee.export.wizard
Wizard untuk export data karyawan.

Wizard ini menyediakan antarmuka untuk memilih parameter export
dan menjalankan proses export ke berbagai format.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import json
import logging
from io import BytesIO
from datetime import datetime

_logger = logging.getLogger(__name__)


class HrEmployeeExportWizard(models.TransientModel):
    """
    Wizard untuk export data karyawan.
    
    Wizard ini memungkinkan user untuk:
    - Memilih format export (Excel, CSV, PDF, JSON)
    - Menggunakan template atau konfigurasi kustom
    - Menerapkan filter (departemen, status, tanggal)
    - Preview data sebelum export
    - Menyimpan konfigurasi sebagai template baru
    """
    _name = 'hr.employee.export.wizard'
    _description = 'Wizard Export Data Karyawan'

    # ==================== Export Method Selection ====================
    export_method = fields.Selection(
        selection=[
            ('template', 'Gunakan Template'),
            ('config', 'Gunakan Konfigurasi'),
            ('custom', 'Kustom'),
        ],
        string='Metode Export',
        default='custom',
        required=True,
        help='Pilih metode untuk menentukan data yang akan di-export'
    )

    # ==================== Template/Config Selection ====================
    template_id = fields.Many2one(
        comodel_name='hr.employee.export.template',
        string='Template',
        domain="[('active', '=', True)]",
        help='Pilih template export yang sudah tersedia'
    )
    config_id = fields.Many2one(
        comodel_name='hr.employee.export.config',
        string='Konfigurasi',
        domain="[('active', '=', True)]",
        help='Pilih konfigurasi export yang sudah tersedia'
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
        default='xlsx',
        required=True,
        help='Format file yang akan dihasilkan'
    )

    # ==================== Data Categories (Custom) ====================
    include_identity = fields.Boolean(
        string='Data Identitas',
        default=True,
        help='Sertakan data identitas (NRP, NIK, Nama, TTL, Gender, Agama)'
    )
    include_employment = fields.Boolean(
        string='Data Kepegawaian',
        default=True,
        help='Sertakan data kepegawaian (Dept, Jabatan, Golongan, Grade, Status)'
    )
    include_family = fields.Boolean(
        string='Data Keluarga',
        default=False,
        help='Sertakan data keluarga (Pasangan, Anak)'
    )
    include_bpjs = fields.Boolean(
        string='Data BPJS',
        default=False,
        help='Sertakan data BPJS'
    )
    include_education = fields.Boolean(
        string='Data Pendidikan',
        default=False,
        help='Sertakan riwayat pendidikan'
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
        relation='hr_export_wizard_department_rel',
        column1='wizard_id',
        column2='department_id',
        string='Departemen',
        help='Filter berdasarkan departemen'
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
    include_inactive = fields.Boolean(
        string='Termasuk Tidak Aktif',
        default=False,
        help='Sertakan karyawan yang sudah tidak aktif'
    )

    # ==================== CSV Options ====================
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

    # ==================== Save as Template/Config ====================
    save_as_config = fields.Boolean(
        string='Simpan sebagai Konfigurasi',
        default=False,
        help='Simpan pengaturan ini sebagai konfigurasi baru'
    )
    new_config_name = fields.Char(
        string='Nama Konfigurasi Baru',
        help='Nama untuk konfigurasi baru'
    )

    # ==================== Result Fields ====================
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('preview', 'Preview'),
            ('done', 'Selesai'),
        ],
        string='Status',
        default='draft'
    )
    preview_count = fields.Integer(
        string='Jumlah Data',
        compute='_compute_preview_count',
        help='Jumlah karyawan yang akan di-export'
    )
    preview_html = fields.Html(
        string='Preview Data',
        compute='_compute_preview_html',
        help='Preview data dalam format HTML table'
    )

    # Output file
    output_file = fields.Binary(
        string='File Export',
        readonly=True
    )
    output_filename = fields.Char(
        string='Nama File',
        readonly=True
    )

    # ==================== Compute Methods ====================
    @api.depends('department_ids', 'employment_status', 'date_from', 'date_to', 'include_inactive')
    def _compute_preview_count(self):
        """Menghitung jumlah karyawan yang akan di-export."""
        Employee = self.env['hr.employee']
        for wizard in self:
            domain = wizard._build_employee_domain()
            wizard.preview_count = Employee.search_count(domain)

    @api.depends('department_ids', 'employment_status', 'date_from', 'date_to', 
                 'include_inactive', 'include_identity', 'include_employment')
    def _compute_preview_html(self):
        """Membuat preview data dalam format HTML."""
        Employee = self.env['hr.employee']
        for wizard in self:
            domain = wizard._build_employee_domain()
            employees = Employee.search(domain, limit=10)
            
            if not employees:
                wizard.preview_html = '<p class="text-muted">Tidak ada data yang sesuai filter.</p>'
                continue
            
            # Build simple preview table
            html = '<table class="table table-sm table-striped">'
            html += '<thead><tr><th>NRP</th><th>Nama</th><th>Departemen</th><th>Status</th></tr></thead>'
            html += '<tbody>'
            
            for emp in employees:
                html += f'<tr>'
                html += f'<td>{emp.nrp or "-"}</td>'
                html += f'<td>{emp.name or "-"}</td>'
                html += f'<td>{emp.department_id.name or "-"}</td>'
                html += f'<td>{emp.employment_status or "-"}</td>'
                html += f'</tr>'
            
            html += '</tbody></table>'
            
            if wizard.preview_count > 10:
                html += f'<p class="text-muted">Menampilkan 10 dari {wizard.preview_count} data.</p>'
            
            wizard.preview_html = html

    # ==================== Onchange Methods ====================
    @api.onchange('export_method')
    def _onchange_export_method(self):
        """Reset fields saat metode export berubah."""
        if self.export_method == 'template':
            self.config_id = False
        elif self.export_method == 'config':
            self.template_id = False

    @api.onchange('config_id')
    def _onchange_config_id(self):
        """Load nilai dari konfigurasi yang dipilih."""
        if self.config_id:
            self.export_type = self.config_id.export_type
            self.include_identity = self.config_id.include_identity
            self.include_employment = self.config_id.include_employment
            self.include_family = self.config_id.include_family
            self.include_bpjs = self.config_id.include_bpjs
            self.include_education = self.config_id.include_education
            self.include_payroll = self.config_id.include_payroll
            self.include_training = self.config_id.include_training
            self.include_reward_punishment = self.config_id.include_reward_punishment
            self.department_ids = self.config_id.department_ids
            self.employment_status = self.config_id.employment_status
            self.date_from = self.config_id.date_from
            self.date_to = self.config_id.date_to
            self.include_inactive = self.config_id.include_inactive
            self.csv_delimiter = self.config_id.csv_delimiter

    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Set export type berdasarkan template yang dipilih."""
        if self.template_id:
            # Template tidak menentukan format, jadi biarkan user pilih
            pass

    # ==================== Validation ====================
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Validasi tanggal."""
        for wizard in self:
            if wizard.date_from and wizard.date_to:
                if wizard.date_from > wizard.date_to:
                    raise ValidationError(_(
                        "Tanggal 'Dari' tidak boleh lebih besar dari tanggal 'Sampai'."
                    ))

    # ==================== Action Methods ====================
    def action_preview(self):
        """Tampilkan preview data yang akan di-export."""
        self.ensure_one()
        self.state = 'preview'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_back(self):
        """Kembali ke state draft."""
        self.ensure_one()
        self.state = 'draft'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_export(self):
        """Jalankan proses export."""
        self.ensure_one()
        
        # Validasi
        if self.preview_count == 0:
            raise UserError(_("Tidak ada data yang sesuai dengan filter."))
        
        # Simpan sebagai konfigurasi jika diminta
        if self.save_as_config and self.new_config_name:
            self._save_as_config()
        
        # Get employees
        employees = self._get_employees()
        
        # Export berdasarkan format
        if self.export_type == 'xlsx':
            return self._export_xlsx(employees)
        elif self.export_type == 'csv':
            return self._export_csv(employees)
        elif self.export_type == 'json':
            return self._export_json(employees)
        elif self.export_type == 'pdf':
            return self._export_pdf(employees)
        else:
            raise UserError(_("Format export tidak didukung."))

    def action_view_employees(self):
        """Buka view karyawan yang akan di-export."""
        self.ensure_one()
        domain = self._build_employee_domain()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Karyawan yang akan di-export'),
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False},
            'target': 'current',
        }

    # ==================== Helper Methods ====================
    def _build_employee_domain(self):
        """Build domain filter untuk query karyawan."""
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

    def _get_employees(self):
        """Get employees berdasarkan filter."""
        domain = self._build_employee_domain()
        return self.env['hr.employee'].search(domain)

    def _get_selected_categories(self):
        """Get list kategori yang dipilih."""
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

    def _save_as_config(self):
        """Simpan pengaturan sebagai konfigurasi baru."""
        Config = self.env['hr.employee.export.config']
        Config.create({
            'name': self.new_config_name,
            'export_type': self.export_type,
            'include_identity': self.include_identity,
            'include_employment': self.include_employment,
            'include_family': self.include_family,
            'include_bpjs': self.include_bpjs,
            'include_education': self.include_education,
            'include_payroll': self.include_payroll,
            'include_training': self.include_training,
            'include_reward_punishment': self.include_reward_punishment,
            'department_ids': [(6, 0, self.department_ids.ids)],
            'employment_status': self.employment_status,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'include_inactive': self.include_inactive,
            'csv_delimiter': self.csv_delimiter,
        })

    def _generate_filename(self, extension):
        """Generate nama file dengan timestamp."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"export_karyawan_{timestamp}.{extension}"

    # ==================== Export Methods ====================
    def _export_xlsx(self, employees):
        """Export ke format Excel."""
        self.ensure_one()
        
        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_("Library xlsxwriter tidak terinstall. Silakan install dengan: pip install xlsxwriter"))
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#714B67',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        cell_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
        })
        date_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': 'dd/mm/yyyy',
        })
        
        categories = self._get_selected_categories()
        
        # Create sheets berdasarkan kategori
        if 'identity' in categories:
            self._write_identity_sheet(workbook, employees, header_format, cell_format, date_format)
        if 'employment' in categories:
            self._write_employment_sheet(workbook, employees, header_format, cell_format, date_format)
        if 'bpjs' in categories:
            self._write_bpjs_sheet(workbook, employees, header_format, cell_format)
        if 'education' in categories:
            self._write_education_sheet(workbook, employees, header_format, cell_format)
        if 'payroll' in categories:
            self._write_payroll_sheet(workbook, employees, header_format, cell_format)
        if 'family' in categories:
            self._write_family_sheet(workbook, employees, header_format, cell_format, date_format)
        if 'training' in categories:
            self._write_training_sheet(workbook, employees, header_format, cell_format, date_format)
        if 'reward_punishment' in categories:
            self._write_reward_punishment_sheet(workbook, employees, header_format, cell_format, date_format)
        
        workbook.close()
        output.seek(0)
        
        filename = self._generate_filename('xlsx')
        self.write({
            'output_file': base64.b64encode(output.getvalue()),
            'output_filename': filename,
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=hr.employee.export.wizard&id={self.id}&field=output_file&filename={filename}&download=true',
            'target': 'self',
        }

    def _export_csv(self, employees):
        """Export ke format CSV."""
        self.ensure_one()
        import csv
        
        output = BytesIO()
        # UTF-8 BOM for Excel compatibility
        output.write(b'\xef\xbb\xbf')
        
        delimiter = self.csv_delimiter or ','
        
        # Get data based on template or categories
        if self.export_method == 'template' and self.template_id:
            data = self.template_id.get_export_data(employees)
            headers = self.template_id.get_headers()
        else:
            data, headers = self._get_custom_export_data(employees)
        
        # Write CSV
        import io
        text_output = io.StringIO()
        writer = csv.DictWriter(text_output, fieldnames=headers, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)
        
        output.write(text_output.getvalue().encode('utf-8'))
        output.seek(0)
        
        filename = self._generate_filename('csv')
        self.write({
            'output_file': base64.b64encode(output.getvalue()),
            'output_filename': filename,
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=hr.employee.export.wizard&id={self.id}&field=output_file&filename={filename}&download=true',
            'target': 'self',
        }

    def _export_json(self, employees):
        """Export ke format JSON."""
        self.ensure_one()
        
        if self.export_method == 'template' and self.template_id:
            data = self.template_id.get_export_data(employees)
        else:
            data, _ = self._get_custom_export_data(employees)
        
        json_output = json.dumps({
            'exported_at': datetime.now().isoformat(),
            'total_records': len(data),
            'data': data,
        }, indent=2, ensure_ascii=False, default=str)
        
        output = BytesIO()
        output.write(json_output.encode('utf-8'))
        output.seek(0)
        
        filename = self._generate_filename('json')
        self.write({
            'output_file': base64.b64encode(output.getvalue()),
            'output_filename': filename,
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=hr.employee.export.wizard&id={self.id}&field=output_file&filename={filename}&download=true',
            'target': 'self',
        }

    def _export_pdf(self, employees):
        """
        Export ke format PDF menggunakan QWeb report.
        
        Menggunakan service EmployeeExportPdf untuk generate PDF
        berdasarkan kategori data yang dipilih.
        """
        self.ensure_one()
        
        try:
            from ..services.export_pdf import EmployeeExportPdf
            
            # Get selected categories
            categories = self._get_selected_categories()
            if not categories:
                categories = ['identity', 'employment']
            
            # Initialize PDF service
            pdf_service = EmployeeExportPdf(self.env)
            
            # Generate PDF
            pdf_content, filename = pdf_service.export(employees, categories=categories)
            
            # Encode dan simpan file
            self.write({
                'output_file': base64.b64encode(pdf_content),
                'output_filename': filename,
                'state': 'done',
            })
            
            # Log export activity
            self._log_export_activity(len(employees), 'pdf')
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content?model=hr.employee.export.wizard&id={self.id}&field=output_file&filename={filename}&download=true',
                'target': 'self',
            }
            
        except ImportError as e:
            _logger.error(f"Import error for PDF export: {str(e)}")
            raise UserError(_("Gagal mengimpor modul PDF export. Pastikan service export_pdf tersedia."))
        except Exception as e:
            _logger.error(f"Error during PDF export: {str(e)}")
            raise UserError(_("Gagal melakukan export PDF: %s") % str(e))

    def _log_export_activity(self, record_count, export_format):
        """Log aktivitas export ke audit log jika tersedia."""
        try:
            AuditLog = self.env.get('hr.employee.export.audit.log')
            if AuditLog:
                AuditLog.create({
                    'user_id': self.env.user.id,
                    'export_type': export_format,
                    'record_count': record_count,
                    'export_date': fields.Datetime.now(),
                    'status': 'success',
                })
        except Exception as e:
            _logger.warning(f"Could not log export activity: {str(e)}")

    def _get_custom_export_data(self, employees):
        """Get export data berdasarkan kategori yang dipilih."""
        data = []
        headers = []
        
        # Build headers based on selected categories
        if self.include_identity:
            headers.extend(['NRP', 'Nama', 'NIK', 'Tempat Lahir', 'Tanggal Lahir', 'Usia', 'Gender', 'Agama'])
        if self.include_employment:
            headers.extend(['Departemen', 'Jabatan', 'Golongan', 'Grade', 'Status', 'Tanggal Masuk', 'Masa Kerja'])
        
        for emp in employees:
            row = {}
            
            if self.include_identity:
                row['NRP'] = emp.nrp or '-'
                row['Nama'] = emp.name or '-'
                row['NIK'] = emp.nik or '-'
                row['Tempat Lahir'] = emp.place_of_birth or '-'
                row['Tanggal Lahir'] = emp.birthday.strftime('%d/%m/%Y') if emp.birthday else '-'
                row['Usia'] = emp.age or '-'
                row['Gender'] = dict(emp._fields['gender'].selection).get(emp.gender, '-') if emp.gender else '-'
                row['Agama'] = dict(emp._fields['religion'].selection).get(emp.religion, '-') if emp.religion else '-'
            
            if self.include_employment:
                row['Departemen'] = emp.department_id.name or '-'
                row['Jabatan'] = emp.job_id.name or '-'
                row['Golongan'] = emp.golongan_id.name if hasattr(emp, 'golongan_id') and emp.golongan_id else '-'
                row['Grade'] = emp.grade_id.name if hasattr(emp, 'grade_id') and emp.grade_id else '-'
                row['Status'] = emp.employment_status or '-'
                row['Tanggal Masuk'] = emp.first_contract_date.strftime('%d/%m/%Y') if hasattr(emp, 'first_contract_date') and emp.first_contract_date else '-'
                row['Masa Kerja'] = f"{emp.service_length:.1f} tahun" if hasattr(emp, 'service_length') and emp.service_length else '-'
            
            data.append(row)
        
        return data, headers

    # ==================== Sheet Writers for Excel ====================
    def _write_identity_sheet(self, workbook, employees, header_format, cell_format, date_format):
        """Write identity data to Excel sheet."""
        sheet = workbook.add_worksheet('Data Identitas')
        
        headers = ['No', 'NRP', 'Nama Lengkap', 'NIK', 'No. KK', 'Tempat Lahir', 
                   'Tanggal Lahir', 'Usia', 'Gender', 'Agama', 'Gol. Darah', 'Status Nikah']
        
        # Write headers
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        # Write data
        row = 1
        for emp in employees:
            sheet.write(row, 0, row, cell_format)
            sheet.write(row, 1, emp.nrp or '-', cell_format)
            sheet.write(row, 2, emp.name or '-', cell_format)
            sheet.write(row, 3, emp.nik or '-', cell_format)
            sheet.write(row, 4, emp.no_kk if hasattr(emp, 'no_kk') else '-', cell_format)
            sheet.write(row, 5, emp.place_of_birth or '-', cell_format)
            if emp.birthday:
                sheet.write(row, 6, emp.birthday, date_format)
            else:
                sheet.write(row, 6, '-', cell_format)
            sheet.write(row, 7, emp.age if hasattr(emp, 'age') else '-', cell_format)
            sheet.write(row, 8, dict(emp._fields['gender'].selection).get(emp.gender, '-') if emp.gender else '-', cell_format)
            sheet.write(row, 9, dict(emp._fields['religion'].selection).get(emp.religion, '-') if hasattr(emp, 'religion') and emp.religion else '-', cell_format)
            sheet.write(row, 10, emp.blood_type if hasattr(emp, 'blood_type') else '-', cell_format)
            sheet.write(row, 11, emp.status_kawin if hasattr(emp, 'status_kawin') else '-', cell_format)
            row += 1
        
        # Auto-fit columns
        for col, header in enumerate(headers):
            sheet.set_column(col, col, max(len(header) + 2, 12))

    def _write_employment_sheet(self, workbook, employees, header_format, cell_format, date_format):
        """Write employment data to Excel sheet."""
        sheet = workbook.add_worksheet('Data Kepegawaian')
        
        headers = ['No', 'NRP', 'Nama', 'Departemen', 'Jabatan', 'Area Kerja',
                   'Golongan', 'Grade', 'Tipe Pegawai', 'Status', 'Tgl Masuk', 'Masa Kerja']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        row = 1
        for emp in employees:
            sheet.write(row, 0, row, cell_format)
            sheet.write(row, 1, emp.nrp or '-', cell_format)
            sheet.write(row, 2, emp.name or '-', cell_format)
            sheet.write(row, 3, emp.department_id.name or '-', cell_format)
            sheet.write(row, 4, emp.job_id.name or '-', cell_format)
            sheet.write(row, 5, emp.area_kerja_id.name if hasattr(emp, 'area_kerja_id') and emp.area_kerja_id else '-', cell_format)
            sheet.write(row, 6, emp.golongan_id.name if hasattr(emp, 'golongan_id') and emp.golongan_id else '-', cell_format)
            sheet.write(row, 7, emp.grade_id.name if hasattr(emp, 'grade_id') and emp.grade_id else '-', cell_format)
            sheet.write(row, 8, emp.employee_type_id.name if hasattr(emp, 'employee_type_id') and emp.employee_type_id else '-', cell_format)
            sheet.write(row, 9, emp.employment_status or '-', cell_format)
            if hasattr(emp, 'first_contract_date') and emp.first_contract_date:
                sheet.write(row, 10, emp.first_contract_date, date_format)
            else:
                sheet.write(row, 10, '-', cell_format)
            sheet.write(row, 11, f"{emp.service_length:.1f}" if hasattr(emp, 'service_length') and emp.service_length else '-', cell_format)
            row += 1
        
        for col, header in enumerate(headers):
            sheet.set_column(col, col, max(len(header) + 2, 12))

    def _write_bpjs_sheet(self, workbook, employees, header_format, cell_format):
        """Write BPJS data to Excel sheet."""
        sheet = workbook.add_worksheet('Data BPJS')
        
        headers = ['No', 'NRP', 'Nama', 'Jenis BPJS', 'Nomor BPJS', 'Faskes TK1', 'Kelas']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        row = 1
        for emp in employees:
            if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
                for bpjs in emp.bpjs_ids:
                    sheet.write(row, 0, row, cell_format)
                    sheet.write(row, 1, emp.nrp or '-', cell_format)
                    sheet.write(row, 2, emp.name or '-', cell_format)
                    sheet.write(row, 3, bpjs.bpjs_type or '-', cell_format)
                    sheet.write(row, 4, bpjs.number or '-', cell_format)
                    sheet.write(row, 5, bpjs.faskes_tk1 if hasattr(bpjs, 'faskes_tk1') else '-', cell_format)
                    sheet.write(row, 6, bpjs.kelas if hasattr(bpjs, 'kelas') else '-', cell_format)
                    row += 1
            else:
                sheet.write(row, 0, row, cell_format)
                sheet.write(row, 1, emp.nrp or '-', cell_format)
                sheet.write(row, 2, emp.name or '-', cell_format)
                sheet.write(row, 3, '-', cell_format)
                sheet.write(row, 4, '-', cell_format)
                sheet.write(row, 5, '-', cell_format)
                sheet.write(row, 6, '-', cell_format)
                row += 1
        
        for col, header in enumerate(headers):
            sheet.set_column(col, col, max(len(header) + 2, 15))

    def _write_education_sheet(self, workbook, employees, header_format, cell_format):
        """Write education data to Excel sheet."""
        sheet = workbook.add_worksheet('Data Pendidikan')
        
        headers = ['No', 'NRP', 'Nama', 'Jenjang', 'Institusi', 'Jurusan', 'Tahun Lulus']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        row = 1
        for emp in employees:
            if hasattr(emp, 'education_ids') and emp.education_ids:
                for edu in emp.education_ids:
                    sheet.write(row, 0, row, cell_format)
                    sheet.write(row, 1, emp.nrp or '-', cell_format)
                    sheet.write(row, 2, emp.name or '-', cell_format)
                    sheet.write(row, 3, edu.certificate or '-', cell_format)
                    sheet.write(row, 4, edu.study_school or '-', cell_format)
                    sheet.write(row, 5, edu.major if hasattr(edu, 'major') else '-', cell_format)
                    sheet.write(row, 6, edu.date_end.year if hasattr(edu, 'date_end') and edu.date_end else '-', cell_format)
                    row += 1
        
        for col, header in enumerate(headers):
            sheet.set_column(col, col, max(len(header) + 2, 15))

    def _write_payroll_sheet(self, workbook, employees, header_format, cell_format):
        """Write payroll data to Excel sheet."""
        sheet = workbook.add_worksheet('Data Payroll')
        
        headers = ['No', 'NRP', 'Nama', 'Nama Bank', 'No. Rekening', 'NPWP', 'EFIN']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        row = 1
        for emp in employees:
            sheet.write(row, 0, row, cell_format)
            sheet.write(row, 1, emp.nrp or '-', cell_format)
            sheet.write(row, 2, emp.name or '-', cell_format)
            if hasattr(emp, 'payroll_id') and emp.payroll_id:
                sheet.write(row, 3, emp.payroll_id.bank_name or '-', cell_format)
                sheet.write(row, 4, emp.payroll_id.bank_account or '-', cell_format)
                sheet.write(row, 5, emp.payroll_id.npwp or '-', cell_format)
                sheet.write(row, 6, emp.payroll_id.efin if hasattr(emp.payroll_id, 'efin') else '-', cell_format)
            else:
                sheet.write(row, 3, '-', cell_format)
                sheet.write(row, 4, '-', cell_format)
                sheet.write(row, 5, '-', cell_format)
                sheet.write(row, 6, '-', cell_format)
            row += 1
        
        for col, header in enumerate(headers):
            sheet.set_column(col, col, max(len(header) + 2, 15))

    def _write_family_sheet(self, workbook, employees, header_format, cell_format, date_format):
        """Write family data to Excel sheet."""
        sheet = workbook.add_worksheet('Data Keluarga')
        
        headers = ['No', 'NRP', 'Nama Karyawan', 'Status Nikah', 'Nama Pasangan', 
                   'NIK Pasangan', 'Jumlah Anak', 'Jml Anggota Keluarga']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        row = 1
        for emp in employees:
            sheet.write(row, 0, row, cell_format)
            sheet.write(row, 1, emp.nrp or '-', cell_format)
            sheet.write(row, 2, emp.name or '-', cell_format)
            sheet.write(row, 3, emp.status_kawin if hasattr(emp, 'status_kawin') else '-', cell_format)
            sheet.write(row, 4, emp.spouse_name if hasattr(emp, 'spouse_name') else '-', cell_format)
            sheet.write(row, 5, emp.spouse_nik if hasattr(emp, 'spouse_nik') else '-', cell_format)
            child_count = len(emp.child_ids) if hasattr(emp, 'child_ids') else 0
            sheet.write(row, 6, child_count, cell_format)
            sheet.write(row, 7, emp.jlh_anggota_keluarga if hasattr(emp, 'jlh_anggota_keluarga') else '-', cell_format)
            row += 1
        
        for col, header in enumerate(headers):
            sheet.set_column(col, col, max(len(header) + 2, 15))

    def _write_training_sheet(self, workbook, employees, header_format, cell_format, date_format):
        """Write training data to Excel sheet."""
        sheet = workbook.add_worksheet('Data Pelatihan')
        
        headers = ['No', 'NRP', 'Nama', 'Nama Pelatihan', 'Jenis', 'Metode', 'Tgl Mulai', 'Tgl Selesai']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        row = 1
        for emp in employees:
            if hasattr(emp, 'training_certificate_ids') and emp.training_certificate_ids:
                for training in emp.training_certificate_ids:
                    sheet.write(row, 0, row, cell_format)
                    sheet.write(row, 1, emp.nrp or '-', cell_format)
                    sheet.write(row, 2, emp.name or '-', cell_format)
                    sheet.write(row, 3, training.name or '-', cell_format)
                    sheet.write(row, 4, training.jenis_pelatihan if hasattr(training, 'jenis_pelatihan') else '-', cell_format)
                    sheet.write(row, 5, training.metode if hasattr(training, 'metode') else '-', cell_format)
                    if hasattr(training, 'date_start') and training.date_start:
                        sheet.write(row, 6, training.date_start, date_format)
                    else:
                        sheet.write(row, 6, '-', cell_format)
                    if hasattr(training, 'date_end') and training.date_end:
                        sheet.write(row, 7, training.date_end, date_format)
                    else:
                        sheet.write(row, 7, '-', cell_format)
                    row += 1
        
        for col, header in enumerate(headers):
            sheet.set_column(col, col, max(len(header) + 2, 15))

    def _write_reward_punishment_sheet(self, workbook, employees, header_format, cell_format, date_format):
        """Write reward & punishment data to Excel sheet."""
        sheet = workbook.add_worksheet('Reward & Punishment')
        
        headers = ['No', 'NRP', 'Nama', 'Tipe', 'Nama R/P', 'Tanggal', 'Keterangan']
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        
        row = 1
        for emp in employees:
            if hasattr(emp, 'reward_punishment_ids') and emp.reward_punishment_ids:
                for rp in emp.reward_punishment_ids:
                    sheet.write(row, 0, row, cell_format)
                    sheet.write(row, 1, emp.nrp or '-', cell_format)
                    sheet.write(row, 2, emp.name or '-', cell_format)
                    sheet.write(row, 3, rp.type if hasattr(rp, 'type') else '-', cell_format)
                    sheet.write(row, 4, rp.name or '-', cell_format)
                    if hasattr(rp, 'date') and rp.date:
                        sheet.write(row, 5, rp.date, date_format)
                    else:
                        sheet.write(row, 5, '-', cell_format)
                    sheet.write(row, 6, rp.description if hasattr(rp, 'description') else '-', cell_format)
                    row += 1
        
        for col, header in enumerate(headers):
            sheet.set_column(col, col, max(len(header) + 2, 15))