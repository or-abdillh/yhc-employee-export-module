# -*- coding: utf-8 -*-
"""
Export Service PDF untuk yhc_employee_export.

Service ini menangani export data karyawan ke format PDF
menggunakan QWeb report engine dari Odoo.
"""

from datetime import datetime, date
import logging
import base64

from .export_base import EmployeeExportBase, FIELD_MAPPINGS

_logger = logging.getLogger(__name__)


class EmployeeExportPdf(EmployeeExportBase):
    """
    Service untuk export data karyawan ke format PDF.
    
    Features:
    - Menggunakan QWeb report engine Odoo
    - Landscape/Portrait orientation
    - Header dengan logo perusahaan
    - Footer dengan page numbering
    """
    
    def __init__(self, env):
        """Initialize PDF export service."""
        super().__init__(env)
        self.report_name = 'yhc_employee_export.report_employee_export'
    
    def export(self, employees, categories=None, config=None):
        """
        Export data karyawan ke format PDF.
        
        Args:
            employees: hr.employee recordset
            categories (list): List kategori yang akan di-export
            config: hr.employee.export.config (optional)
            
        Returns:
            tuple: (bytes, filename)
        """
        self.validate_employees(employees)
        
        if categories is None:
            categories = ['identity', 'employment']
        
        # Prepare report data
        report_data = self._prepare_report_data(employees, categories)
        
        # Generate PDF using report action
        try:
            pdf_content = self._generate_pdf_report(employees, report_data)
            filename = self.generate_filename('export_karyawan', 'pdf')
            
            return pdf_content, filename
            
        except Exception as e:
            _logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    def _prepare_report_data(self, employees, categories):
        """
        Prepare data untuk report.
        
        Args:
            employees: hr.employee recordset
            categories (list): List kategori
            
        Returns:
            dict: Report data
        """
        return {
            'employees': employees,
            'categories': categories,
            'export_date': datetime.now(),
            'exported_by': self.env.user,
            'company': self.env.company,
            'total_employees': len(employees),
            'category_names': self._get_category_names(categories),
            'helper': self,  # Pass service untuk akses helper methods
        }
    
    def _get_category_names(self, categories):
        """Get display names untuk categories."""
        names = {
            'identity': 'Data Identitas',
            'employment': 'Data Kepegawaian',
            'family': 'Data Keluarga',
            'bpjs': 'Data BPJS',
            'education': 'Data Pendidikan',
            'payroll': 'Data Payroll',
            'training': 'Data Pelatihan',
            'reward_punishment': 'Data Reward & Punishment',
        }
        return [names.get(cat, cat) for cat in categories]
    
    def _generate_pdf_report(self, employees, report_data):
        """
        Generate PDF menggunakan report action.
        
        Args:
            employees: hr.employee recordset
            report_data: Data untuk report
            
        Returns:
            bytes: PDF content
        """
        # Get report action
        report = self.env.ref(self.report_name, raise_if_not_found=False)
        
        if report:
            # Use standard Odoo report
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report,
                employees.ids,
                data=report_data
            )
            return pdf_content
        else:
            # Fallback: Generate simple PDF using wkhtmltopdf directly
            return self._generate_simple_pdf(employees, report_data)
    
    def _generate_simple_pdf(self, employees, report_data):
        """
        Generate simple PDF jika report tidak tersedia.
        
        Args:
            employees: hr.employee recordset
            report_data: Data untuk report
            
        Returns:
            bytes: PDF content
        """
        # Generate HTML
        html_content = self._generate_html(employees, report_data)
        
        # Convert HTML to PDF using wkhtmltopdf
        try:
            from odoo.tools import pdf
            
            # Create PDF using Odoo's wkhtmltopdf wrapper
            IrActionsReport = self.env['ir.actions.report']
            pdf_content = IrActionsReport._run_wkhtmltopdf(
                [html_content.encode('utf-8')],
                landscape=True,
            )
            return pdf_content
            
        except Exception as e:
            _logger.error(f"Error running wkhtmltopdf: {str(e)}")
            # Return HTML as fallback
            return html_content.encode('utf-8')
    
    def _generate_html(self, employees, report_data):
        """
        Generate HTML content untuk PDF.
        
        Args:
            employees: hr.employee recordset
            report_data: Data untuk report
            
        Returns:
            str: HTML content
        """
        categories = report_data.get('categories', [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Export Data Karyawan</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                    margin: 20px;
                }}
                h1 {{
                    color: #714B67;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .info {{
                    margin-bottom: 20px;
                    font-size: 9pt;
                    color: #666;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th {{
                    background-color: #714B67;
                    color: white;
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #ccc;
                }}
                td {{
                    padding: 6px;
                    border: 1px solid #ccc;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    font-size: 8pt;
                    color: #999;
                }}
            </style>
        </head>
        <body>
            <h1>LAPORAN DATA KARYAWAN</h1>
            <div class="info">
                <p><strong>Tanggal Export:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>Diekspor Oleh:</strong> {self.env.user.name}</p>
                <p><strong>Perusahaan:</strong> {self.env.company.name}</p>
                <p><strong>Total Karyawan:</strong> {len(employees)}</p>
                <p><strong>Kategori:</strong> {', '.join(report_data.get('category_names', []))}</p>
            </div>
        """
        
        # Generate table berdasarkan kategori
        if 'identity' in categories or 'employment' in categories:
            html += self._generate_main_table(employees, categories)
        
        html += """
            <div class="footer">
                <p>Dokumen ini digenerate oleh sistem YHC Employee Export</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_main_table(self, employees, categories):
        """Generate main employee table HTML."""
        headers = ['No', 'NRP', 'Nama']
        
        if 'identity' in categories:
            headers.extend(['NIK', 'Tempat/Tgl Lahir', 'Jenis Kelamin'])
        
        if 'employment' in categories:
            headers.extend(['Unit Kerja', 'Jabatan', 'Status'])
        
        html = '<table><thead><tr>'
        for header in headers:
            html += f'<th>{header}</th>'
        html += '</tr></thead><tbody>'
        
        for idx, emp in enumerate(employees, 1):
            html += '<tr>'
            html += f'<td style="text-align:center">{idx}</td>'
            html += f'<td>{self.get_formatted_field_value(emp, "nrp")}</td>'
            html += f'<td>{self.get_formatted_field_value(emp, "name")}</td>'
            
            if 'identity' in categories:
                birthday = self.get_field_value(emp, 'birthday')
                ttl = f"{self.get_formatted_field_value(emp, 'place_of_birth')}"
                if birthday:
                    ttl += f", {birthday.strftime('%d/%m/%Y')}"
                
                html += f'<td>{self.get_formatted_field_value(emp, "nik")}</td>'
                html += f'<td>{ttl}</td>'
                html += f'<td>{self.get_selection_label(emp, "gender")}</td>'
            
            if 'employment' in categories:
                html += f'<td>{self.get_formatted_field_value(emp, "department_id.name")}</td>'
                html += f'<td>{self.get_formatted_field_value(emp, "job_id.name")}</td>'
                html += f'<td>{self.get_formatted_field_value(emp, "employment_status")}</td>'
            
            html += '</tr>'
        
        html += '</tbody></table>'
        
        return html
    
    def generate_employee_card_pdf(self, employee):
        """
        Generate PDF kartu karyawan.
        
        Args:
            employee: hr.employee record
            
        Returns:
            bytes: PDF content
        """
        report_name = 'yhc_employee_export.report_employee_card'
        report = self.env.ref(report_name, raise_if_not_found=False)
        
        if report:
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report,
                [employee.id],
            )
            return pdf_content
        
        # Fallback simple card
        return self._generate_simple_card_pdf(employee)
    
    def _generate_simple_card_pdf(self, employee):
        """Generate simple card PDF."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .card {{
                    width: 350px;
                    border: 2px solid #714B67;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px auto;
                }}
                .header {{
                    text-align: center;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 10px;
                    margin-bottom: 15px;
                }}
                .company {{ color: #714B67; font-weight: bold; }}
                .name {{ font-size: 16pt; font-weight: bold; margin: 10px 0; }}
                .nrp {{ color: #666; }}
                .info {{ margin: 5px 0; }}
                .label {{ color: #888; font-size: 9pt; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="header">
                    <div class="company">{self.env.company.name}</div>
                    <div class="name">{employee.name}</div>
                    <div class="nrp">NRP: {self.get_formatted_field_value(employee, 'nrp')}</div>
                </div>
                <div class="info">
                    <div class="label">Unit Kerja</div>
                    <div>{self.get_formatted_field_value(employee, 'department_id.name')}</div>
                </div>
                <div class="info">
                    <div class="label">Jabatan</div>
                    <div>{self.get_formatted_field_value(employee, 'job_id.name')}</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            IrActionsReport = self.env['ir.actions.report']
            pdf_content = IrActionsReport._run_wkhtmltopdf(
                [html.encode('utf-8')],
            )
            return pdf_content
        except Exception:
            return html.encode('utf-8')
