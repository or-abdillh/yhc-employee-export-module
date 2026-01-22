# -*- coding: utf-8 -*-
"""
Export Service XLSX untuk yhc_employee_export.

Service ini menangani export data karyawan ke format Excel (.xlsx)
dengan fitur multiple sheets, formatting, dan auto-width columns.
"""

from io import BytesIO
from datetime import datetime, date
import logging

from .export_base import EmployeeExportBase, FIELD_MAPPINGS

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False
    _logger.warning("xlsxwriter not installed. Excel export will not be available.")


class EmployeeExportXlsx(EmployeeExportBase):
    """
    Service untuk export data karyawan ke format Excel (.xlsx).
    
    Features:
    - Multiple sheets berdasarkan kategori data
    - Auto-width columns
    - Header formatting dengan warna Odoo
    - Freeze panes untuk header
    - Date formatting
    - Number formatting
    """
    
    def __init__(self, env):
        """Initialize XLSX export service."""
        super().__init__(env)
        self.workbook = None
        self.formats = {}
        
        if not XLSXWRITER_AVAILABLE:
            raise ImportError(
                "Library xlsxwriter tidak terinstall. "
                "Silakan install dengan: pip install xlsxwriter"
            )
    
    def export(self, employees, categories=None, config=None):
        """
        Export data karyawan ke format Excel.
        
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
        
        output = BytesIO()
        self.workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Setup formats
        self._setup_formats()
        
        # Write sheets berdasarkan kategori
        if 'identity' in categories:
            self._write_identity_sheet(employees)
        if 'employment' in categories:
            self._write_employment_sheet(employees)
        if 'family' in categories:
            self._write_family_sheet(employees)
        if 'bpjs' in categories:
            self._write_bpjs_sheet(employees)
        if 'education' in categories:
            self._write_education_sheet(employees)
        if 'payroll' in categories:
            self._write_payroll_sheet(employees)
        if 'training' in categories:
            self._write_training_sheet(employees)
        if 'reward_punishment' in categories:
            self._write_reward_punishment_sheet(employees)
        
        # Add summary sheet
        self._write_summary_sheet(employees, categories)
        
        self.workbook.close()
        output.seek(0)
        
        filename = self.generate_filename('export_karyawan', 'xlsx')
        
        return output.getvalue(), filename
    
    def _setup_formats(self):
        """Setup format styles untuk workbook."""
        # Header format - Odoo purple
        self.formats['header'] = self.workbook.add_format({
            'bold': True,
            'bg_color': '#714B67',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })
        
        # Sub-header format
        self.formats['subheader'] = self.workbook.add_format({
            'bold': True,
            'bg_color': '#E8E8E8',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        
        # Cell format
        self.formats['cell'] = self.workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
        })
        
        # Cell center format
        self.formats['cell_center'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        
        # Date format
        self.formats['date'] = self.workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': 'dd/mm/yyyy',
        })
        
        # Number format
        self.formats['number'] = self.workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': '#,##0',
        })
        
        # Decimal format
        self.formats['decimal'] = self.workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': '#,##0.00',
        })
        
        # Title format
        self.formats['title'] = self.workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
        })
        
        # Info format
        self.formats['info'] = self.workbook.add_format({
            'italic': True,
            'font_color': '#666666',
        })
    
    def _write_sheet_header(self, sheet, title, headers, start_row=0):
        """
        Write header ke sheet.
        
        Args:
            sheet: Worksheet object
            title (str): Judul sheet
            headers (list): List header columns
            start_row (int): Baris mulai
            
        Returns:
            int: Baris selanjutnya untuk data
        """
        # Write title
        sheet.merge_range(start_row, 0, start_row, len(headers) - 1, 
                         title, self.formats['title'])
        
        # Write export info
        export_info = f"Diekspor pada: {datetime.now().strftime('%d/%m/%Y %H:%M')} oleh {self.env.user.name}"
        sheet.merge_range(start_row + 1, 0, start_row + 1, len(headers) - 1,
                         export_info, self.formats['info'])
        
        # Write headers
        header_row = start_row + 3
        for col, header in enumerate(headers):
            sheet.write(header_row, col, header, self.formats['header'])
        
        # Freeze panes
        sheet.freeze_panes(header_row + 1, 0)
        
        return header_row + 1
    
    def _auto_fit_columns(self, sheet, data_rows, headers):
        """
        Auto-fit column widths berdasarkan konten.
        
        Args:
            sheet: Worksheet object
            data_rows (list): List of data rows
            headers (list): List header columns
        """
        for col_idx, header in enumerate(headers):
            max_length = len(str(header))
            
            for row in data_rows:
                if col_idx < len(row):
                    cell_length = len(str(row[col_idx])) if row[col_idx] else 0
                    max_length = max(max_length, cell_length)
            
            # Set width with some padding, max 50
            width = min(max_length + 2, 50)
            sheet.set_column(col_idx, col_idx, width)
    
    def _write_identity_sheet(self, employees):
        """Write sheet Data Identitas."""
        sheet = self.workbook.add_worksheet('Data Identitas')
        
        headers = ['No', 'NRP', 'Nama Lengkap', 'Gelar', 'NIK', 'No. KK', 
                   'Tempat Lahir', 'Tanggal Lahir', 'Usia', 'Jenis Kelamin',
                   'Agama', 'Gol. Darah', 'Status Nikah', 'Alamat KTP']
        
        data_row = self._write_sheet_header(sheet, 'DATA IDENTITAS KARYAWAN', headers)
        data_rows = []
        
        for idx, emp in enumerate(employees, 1):
            row_data = [
                idx,
                self.get_formatted_field_value(emp, 'nrp'),
                self.get_formatted_field_value(emp, 'name'),
                self.get_formatted_field_value(emp, 'gelar'),
                self.get_formatted_field_value(emp, 'nik'),
                self.get_formatted_field_value(emp, 'no_kk'),
                self.get_formatted_field_value(emp, 'place_of_birth'),
                emp.birthday if emp.birthday else None,
                self.get_formatted_field_value(emp, 'age'),
                self.get_selection_label(emp, 'gender'),
                self.get_selection_label(emp, 'religion'),
                self.get_formatted_field_value(emp, 'blood_type'),
                self.get_formatted_field_value(emp, 'status_kawin'),
                self.get_formatted_field_value(emp, 'alamat_ktp'),
            ]
            
            for col, value in enumerate(row_data):
                if col == 7 and value:  # Tanggal Lahir
                    sheet.write(data_row, col, value, self.formats['date'])
                elif col == 0:  # No
                    sheet.write(data_row, col, value, self.formats['cell_center'])
                else:
                    sheet.write(data_row, col, value if value else self.empty_value, 
                               self.formats['cell'])
            
            data_rows.append(row_data)
            data_row += 1
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_employment_sheet(self, employees):
        """Write sheet Data Kepegawaian."""
        sheet = self.workbook.add_worksheet('Data Kepegawaian')
        
        headers = ['No', 'NRP', 'Nama', 'Unit Kerja', 'Jabatan', 'Area Kerja',
                   'Golongan', 'Grade', 'Tipe Pegawai', 'Jenis Pegawai', 
                   'Status', 'Tgl Masuk', 'Masa Kerja']
        
        data_row = self._write_sheet_header(sheet, 'DATA KEPEGAWAIAN', headers)
        data_rows = []
        
        for idx, emp in enumerate(employees, 1):
            # Get masa kerja
            service_length = self.get_field_value(emp, 'service_length')
            masa_kerja = self._format_service_length(service_length, with_unit=True) if service_length else self.empty_value
            
            row_data = [
                idx,
                self.get_formatted_field_value(emp, 'nrp'),
                self.get_formatted_field_value(emp, 'name'),
                self.get_formatted_field_value(emp, 'department_id.name'),
                self.get_formatted_field_value(emp, 'job_id.name'),
                self.get_formatted_field_value(emp, 'area_kerja_id.name'),
                self.get_formatted_field_value(emp, 'golongan_id.name'),
                self.get_formatted_field_value(emp, 'grade_id.name'),
                self.get_formatted_field_value(emp, 'employee_type_id.name'),
                self.get_formatted_field_value(emp, 'employee_category_id.name'),
                self.get_formatted_field_value(emp, 'employment_status'),
                self.get_field_value(emp, 'first_contract_date'),
                masa_kerja,
            ]
            
            for col, value in enumerate(row_data):
                if col == 11 and value:  # Tgl Masuk
                    sheet.write(data_row, col, value, self.formats['date'])
                elif col == 0:  # No
                    sheet.write(data_row, col, value, self.formats['cell_center'])
                else:
                    sheet.write(data_row, col, value if value else self.empty_value,
                               self.formats['cell'])
            
            data_rows.append(row_data)
            data_row += 1
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_family_sheet(self, employees):
        """Write sheet Data Keluarga."""
        sheet = self.workbook.add_worksheet('Data Keluarga')
        
        headers = ['No', 'NRP', 'Nama Karyawan', 'Status Nikah', 'Nama Pasangan',
                   'NIK Pasangan', 'Tgl Lahir Pasangan', 'Jumlah Anak', 'Jml Anggota Keluarga']
        
        data_row = self._write_sheet_header(sheet, 'DATA KELUARGA', headers)
        data_rows = []
        
        for idx, emp in enumerate(employees, 1):
            child_count = len(emp.child_ids) if hasattr(emp, 'child_ids') else 0
            
            row_data = [
                idx,
                self.get_formatted_field_value(emp, 'nrp'),
                self.get_formatted_field_value(emp, 'name'),
                self.get_formatted_field_value(emp, 'status_kawin'),
                self.get_formatted_field_value(emp, 'spouse_name'),
                self.get_formatted_field_value(emp, 'spouse_nik'),
                self.get_field_value(emp, 'spouse_birthday'),
                child_count,
                self.get_formatted_field_value(emp, 'jlh_anggota_keluarga'),
            ]
            
            for col, value in enumerate(row_data):
                if col == 6 and value:  # Tgl Lahir Pasangan
                    sheet.write(data_row, col, value, self.formats['date'])
                elif col in [0, 7, 8]:  # No, Jumlah
                    sheet.write(data_row, col, value if value else 0, self.formats['cell_center'])
                else:
                    sheet.write(data_row, col, value if value else self.empty_value,
                               self.formats['cell'])
            
            data_rows.append(row_data)
            data_row += 1
        
        # Jika ada data anak, buat sheet terpisah
        self._write_children_sheet(employees)
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_children_sheet(self, employees):
        """Write sheet Data Anak."""
        sheet = self.workbook.add_worksheet('Data Anak')
        
        headers = ['No', 'NRP', 'Nama Karyawan', 'Nama Anak', 'Jenis Kelamin',
                   'Tanggal Lahir', 'Usia', 'Status']
        
        data_row = self._write_sheet_header(sheet, 'DATA ANAK KARYAWAN', headers)
        data_rows = []
        no = 1
        
        for emp in employees:
            if hasattr(emp, 'child_ids') and emp.child_ids:
                for child in emp.child_ids:
                    row_data = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(child, 'name'),
                        self.get_selection_label(child, 'gender') if hasattr(child, 'gender') else self.empty_value,
                        self.get_field_value(child, 'birth_date'),
                        self.get_formatted_field_value(child, 'age') if hasattr(child, 'age') else self.empty_value,
                        self.get_formatted_field_value(child, 'status') if hasattr(child, 'status') else self.empty_value,
                    ]
                    
                    for col, value in enumerate(row_data):
                        if col == 5 and value:  # Tanggal Lahir
                            sheet.write(data_row, col, value, self.formats['date'])
                        elif col == 0:
                            sheet.write(data_row, col, value, self.formats['cell_center'])
                        else:
                            sheet.write(data_row, col, value if value else self.empty_value,
                                       self.formats['cell'])
                    
                    data_rows.append(row_data)
                    data_row += 1
                    no += 1
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_bpjs_sheet(self, employees):
        """Write sheet Data BPJS."""
        sheet = self.workbook.add_worksheet('Data BPJS')
        
        headers = ['No', 'NRP', 'Nama', 'NIK', 'Jenis BPJS', 'Nomor BPJS', 
                   'Faskes TK1', 'Kelas']
        
        data_row = self._write_sheet_header(sheet, 'DATA BPJS', headers)
        data_rows = []
        no = 1
        
        for emp in employees:
            if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
                for bpjs in emp.bpjs_ids:
                    row_data = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(emp, 'nik'),
                        self.get_formatted_field_value(bpjs, 'bpjs_type'),
                        self.get_formatted_field_value(bpjs, 'number'),
                        self.get_formatted_field_value(bpjs, 'faskes_tk1'),
                        self.get_formatted_field_value(bpjs, 'kelas'),
                    ]
                    
                    for col, value in enumerate(row_data):
                        if col == 0:
                            sheet.write(data_row, col, value, self.formats['cell_center'])
                        else:
                            sheet.write(data_row, col, value if value else self.empty_value,
                                       self.formats['cell'])
                    
                    data_rows.append(row_data)
                    data_row += 1
                    no += 1
            else:
                # Karyawan tanpa BPJS
                row_data = [
                    no,
                    self.get_formatted_field_value(emp, 'nrp'),
                    self.get_formatted_field_value(emp, 'name'),
                    self.get_formatted_field_value(emp, 'nik'),
                    self.empty_value,
                    self.empty_value,
                    self.empty_value,
                    self.empty_value,
                ]
                
                for col, value in enumerate(row_data):
                    if col == 0:
                        sheet.write(data_row, col, value, self.formats['cell_center'])
                    else:
                        sheet.write(data_row, col, value, self.formats['cell'])
                
                data_rows.append(row_data)
                data_row += 1
                no += 1
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_education_sheet(self, employees):
        """Write sheet Data Pendidikan."""
        sheet = self.workbook.add_worksheet('Data Pendidikan')
        
        headers = ['No', 'NRP', 'Nama', 'Jenjang', 'Institusi', 'Jurusan',
                   'Tahun Masuk', 'Tahun Lulus']
        
        data_row = self._write_sheet_header(sheet, 'DATA PENDIDIKAN', headers)
        data_rows = []
        no = 1
        
        for emp in employees:
            if hasattr(emp, 'education_ids') and emp.education_ids:
                for edu in emp.education_ids:
                    date_start = self.get_field_value(edu, 'date_start')
                    date_end = self.get_field_value(edu, 'date_end')
                    
                    row_data = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(edu, 'certificate'),
                        self.get_formatted_field_value(edu, 'study_school'),
                        self.get_formatted_field_value(edu, 'major'),
                        date_start.year if date_start else self.empty_value,
                        date_end.year if date_end else self.empty_value,
                    ]
                    
                    for col, value in enumerate(row_data):
                        if col == 0:
                            sheet.write(data_row, col, value, self.formats['cell_center'])
                        elif col in [6, 7] and value != self.empty_value:
                            sheet.write(data_row, col, value, self.formats['cell_center'])
                        else:
                            sheet.write(data_row, col, value if value else self.empty_value,
                                       self.formats['cell'])
                    
                    data_rows.append(row_data)
                    data_row += 1
                    no += 1
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_payroll_sheet(self, employees):
        """Write sheet Data Payroll."""
        sheet = self.workbook.add_worksheet('Data Payroll')
        
        headers = ['No', 'NRP', 'Nama', 'NIK', 'Nama Bank', 'No. Rekening',
                   'NPWP', 'EFIN']
        
        data_row = self._write_sheet_header(sheet, 'DATA PAYROLL', headers)
        data_rows = []
        
        for idx, emp in enumerate(employees, 1):
            payroll = self.get_field_value(emp, 'payroll_id')
            
            row_data = [
                idx,
                self.get_formatted_field_value(emp, 'nrp'),
                self.get_formatted_field_value(emp, 'name'),
                self.get_formatted_field_value(emp, 'nik'),
                self.get_formatted_field_value(payroll, 'bank_name') if payroll else self.empty_value,
                self.get_formatted_field_value(payroll, 'bank_account') if payroll else self.empty_value,
                self.get_formatted_field_value(payroll, 'npwp') if payroll else self.empty_value,
                self.get_formatted_field_value(payroll, 'efin') if payroll else self.empty_value,
            ]
            
            for col, value in enumerate(row_data):
                if col == 0:
                    sheet.write(data_row, col, value, self.formats['cell_center'])
                else:
                    sheet.write(data_row, col, value if value else self.empty_value,
                               self.formats['cell'])
            
            data_rows.append(row_data)
            data_row += 1
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_training_sheet(self, employees):
        """Write sheet Data Pelatihan."""
        sheet = self.workbook.add_worksheet('Data Pelatihan')
        
        headers = ['No', 'NRP', 'Nama', 'Unit Kerja', 'Nama Pelatihan',
                   'Jenis', 'Metode', 'Tgl Mulai', 'Tgl Selesai']
        
        data_row = self._write_sheet_header(sheet, 'DATA PELATIHAN', headers)
        data_rows = []
        no = 1
        
        for emp in employees:
            if hasattr(emp, 'training_certificate_ids') and emp.training_certificate_ids:
                for training in emp.training_certificate_ids:
                    row_data = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(emp, 'department_id.name'),
                        self.get_formatted_field_value(training, 'name'),
                        self.get_formatted_field_value(training, 'jenis_pelatihan'),
                        self.get_formatted_field_value(training, 'metode'),
                        self.get_field_value(training, 'date_start'),
                        self.get_field_value(training, 'date_end'),
                    ]
                    
                    for col, value in enumerate(row_data):
                        if col in [7, 8] and value:  # Tanggal
                            sheet.write(data_row, col, value, self.formats['date'])
                        elif col == 0:
                            sheet.write(data_row, col, value, self.formats['cell_center'])
                        else:
                            sheet.write(data_row, col, value if value else self.empty_value,
                                       self.formats['cell'])
                    
                    data_rows.append(row_data)
                    data_row += 1
                    no += 1
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_reward_punishment_sheet(self, employees):
        """Write sheet Data Reward & Punishment."""
        sheet = self.workbook.add_worksheet('Reward & Punishment')
        
        headers = ['No', 'NRP', 'Nama', 'Unit Kerja', 'Tipe', 'Nama R/P',
                   'Tanggal', 'Keterangan']
        
        data_row = self._write_sheet_header(sheet, 'DATA REWARD & PUNISHMENT', headers)
        data_rows = []
        no = 1
        
        for emp in employees:
            if hasattr(emp, 'reward_punishment_ids') and emp.reward_punishment_ids:
                for rp in emp.reward_punishment_ids:
                    row_data = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(emp, 'department_id.name'),
                        self.get_formatted_field_value(rp, 'type'),
                        self.get_formatted_field_value(rp, 'name'),
                        self.get_field_value(rp, 'date'),
                        self.get_formatted_field_value(rp, 'description'),
                    ]
                    
                    for col, value in enumerate(row_data):
                        if col == 6 and value:  # Tanggal
                            sheet.write(data_row, col, value, self.formats['date'])
                        elif col == 0:
                            sheet.write(data_row, col, value, self.formats['cell_center'])
                        else:
                            sheet.write(data_row, col, value if value else self.empty_value,
                                       self.formats['cell'])
                    
                    data_rows.append(row_data)
                    data_row += 1
                    no += 1
        
        self._auto_fit_columns(sheet, data_rows, headers)
    
    def _write_summary_sheet(self, employees, categories):
        """Write sheet Summary."""
        sheet = self.workbook.add_worksheet('Summary')
        
        # Title
        sheet.merge_range('A1:D1', 'RINGKASAN EXPORT DATA KARYAWAN', self.formats['title'])
        
        # Export info
        row = 3
        info_data = [
            ('Tanggal Export', datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
            ('Diekspor Oleh', self.env.user.name),
            ('Perusahaan', self.env.company.name),
            ('', ''),
            ('Total Karyawan', len(employees)),
        ]
        
        for label, value in info_data:
            if label:
                sheet.write(row, 0, label, self.formats['subheader'])
                sheet.write(row, 1, value, self.formats['cell'])
            row += 1
        
        # Kategori yang di-export
        row += 1
        sheet.write(row, 0, 'Kategori Data:', self.formats['subheader'])
        row += 1
        
        category_names = {
            'identity': 'Data Identitas',
            'employment': 'Data Kepegawaian',
            'family': 'Data Keluarga',
            'bpjs': 'Data BPJS',
            'education': 'Data Pendidikan',
            'payroll': 'Data Payroll',
            'training': 'Data Pelatihan',
            'reward_punishment': 'Data Reward & Punishment',
        }
        
        for cat in categories:
            sheet.write(row, 0, f"  • {category_names.get(cat, cat)}", self.formats['cell'])
            row += 1
        
        # Set column widths
        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 40)
