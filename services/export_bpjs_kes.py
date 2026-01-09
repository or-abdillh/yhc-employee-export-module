# -*- coding: utf-8 -*-
"""
Export Service BPJS Kesehatan untuk yhc_employee_export.

Service ini menangani export data karyawan ke format yang sesuai
dengan ketentuan pelaporan BPJS Kesehatan.

Format export mengikuti template resmi dari BPJS Kesehatan untuk:
- Pendaftaran peserta baru
- Perubahan data peserta
- Penonaktifan peserta
- Laporan data peserta aktif
"""

from io import BytesIO
from datetime import datetime, date
import logging

from .export_base import EmployeeExportBase

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False
    _logger.warning("xlsxwriter not installed. Excel export will not be available.")


class EmployeeExportBpjsKes(EmployeeExportBase):
    """
    Service untuk export data BPJS Kesehatan.
    
    Format export mengikuti template resmi BPJS Kesehatan dengan kolom:
    - Data Identitas Peserta
    - Data Kepesertaan
    - Data Faskes Tingkat 1
    - Data Keluarga (jika ada)
    """
    
    # Kolom standar untuk format BPJS Kesehatan
    HEADER_COLUMNS = [
        'NO',
        'NIK',
        'NAMA LENGKAP',
        'TEMPAT LAHIR',
        'TANGGAL LAHIR',
        'JENIS KELAMIN',
        'STATUS PERKAWINAN',
        'ALAMAT',
        'RT',
        'RW',
        'KELURAHAN',
        'KECAMATAN',
        'KOTA/KAB',
        'PROVINSI',
        'KODE POS',
        'NO HP',
        'EMAIL',
        'NO KARTU BPJS',
        'KELAS RAWAT',
        'KODE FASKES TK1',
        'NAMA FASKES TK1',
        'TGL MULAI AKTIF',
        'STATUS KEPESERTAAN',
        'GAJI',
        'KODE PERUSAHAAN',
        'NAMA PERUSAHAAN',
        'HUBUNGAN KELUARGA',
        'NIK PESERTA UTAMA',
    ]
    
    # Mapping jenis kelamin
    GENDER_MAP = {
        'male': 'L',
        'female': 'P',
        'laki-laki': 'L',
        'perempuan': 'P',
    }
    
    # Mapping status perkawinan
    MARITAL_MAP = {
        'single': 'TK',
        'married': 'K',
        'widower': 'D',
        'divorced': 'C',
        'belum_kawin': 'TK',
        'kawin': 'K',
        'duda': 'D',
        'janda': 'D',
        'cerai': 'C',
    }
    
    def __init__(self, env):
        """Initialize BPJS Kesehatan export service."""
        super().__init__(env)
        
        if not XLSXWRITER_AVAILABLE:
            raise ImportError(
                "Library xlsxwriter tidak terinstall. "
                "Silakan install dengan: pip install xlsxwriter"
            )
    
    def export(self, employees, export_type='active', include_family=True):
        """
        Export data BPJS Kesehatan.
        
        Args:
            employees: hr.employee recordset
            export_type (str): Tipe export ('active', 'new', 'update', 'inactive')
            include_family (bool): Include data keluarga
            
        Returns:
            tuple: (bytes, filename)
        """
        self.validate_employees(employees)
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Setup formats
        formats = self._setup_formats(workbook)
        
        # Create sheets
        self._write_main_sheet(workbook, formats, employees, export_type)
        
        if include_family:
            self._write_family_sheet(workbook, formats, employees)
        
        # Info sheet
        self._write_info_sheet(workbook, formats, employees, export_type)
        
        workbook.close()
        output.seek(0)
        
        # Generate filename
        type_suffix = {
            'active': 'peserta_aktif',
            'new': 'pendaftaran_baru',
            'update': 'perubahan_data',
            'inactive': 'penonaktifan',
        }
        suffix = type_suffix.get(export_type, 'data')
        filename = self.generate_filename(f'bpjs_kesehatan_{suffix}', 'xlsx')
        
        return output.getvalue(), filename
    
    def _setup_formats(self, workbook):
        """Setup Excel formats."""
        return {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#00A65A',  # BPJS Green
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
            }),
            'cell': workbook.add_format({
                'border': 1,
                'valign': 'vcenter',
            }),
            'cell_center': workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
            }),
            'date': workbook.add_format({
                'border': 1,
                'valign': 'vcenter',
                'num_format': 'dd-mm-yyyy',
            }),
            'number': workbook.add_format({
                'border': 1,
                'valign': 'vcenter',
                'num_format': '#,##0',
            }),
            'title': workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
            }),
            'info': workbook.add_format({
                'italic': True,
                'font_color': '#666666',
            }),
            'warning': workbook.add_format({
                'bold': True,
                'font_color': '#FF0000',
            }),
        }
    
    def _write_main_sheet(self, workbook, formats, employees, export_type):
        """Write main data sheet."""
        sheet = workbook.add_worksheet('Data Peserta')
        
        # Write title
        title = self._get_title(export_type)
        sheet.merge_range(0, 0, 0, len(self.HEADER_COLUMNS) - 1, 
                         title, formats['title'])
        
        # Write export info
        info = f"Tanggal Export: {datetime.now().strftime('%d-%m-%Y %H:%M')} | Total: {len(employees)} karyawan"
        sheet.merge_range(1, 0, 1, len(self.HEADER_COLUMNS) - 1,
                         info, formats['info'])
        
        # Write headers
        for col, header in enumerate(self.HEADER_COLUMNS):
            sheet.write(3, col, header, formats['header'])
        
        # Freeze panes
        sheet.freeze_panes(4, 0)
        
        # Write data
        row = 4
        for idx, emp in enumerate(employees, 1):
            self._write_employee_row(sheet, formats, row, idx, emp)
            row += 1
        
        # Auto-fit columns
        self._auto_fit_columns(sheet, len(self.HEADER_COLUMNS))
    
    def _get_title(self, export_type):
        """Get report title based on export type."""
        titles = {
            'active': 'LAPORAN DATA PESERTA BPJS KESEHATAN AKTIF',
            'new': 'DATA PENDAFTARAN PESERTA BPJS KESEHATAN BARU',
            'update': 'DATA PERUBAHAN PESERTA BPJS KESEHATAN',
            'inactive': 'DATA PENONAKTIFAN PESERTA BPJS KESEHATAN',
        }
        return titles.get(export_type, 'DATA PESERTA BPJS KESEHATAN')
    
    def _write_employee_row(self, sheet, formats, row, idx, emp):
        """Write single employee row."""
        # Get BPJS Kesehatan data
        bpjs_kes = None
        if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
            for bpjs in emp.bpjs_ids:
                if self.get_field_value(bpjs, 'bpjs_type') == 'kesehatan':
                    bpjs_kes = bpjs
                    break
        
        # Parse alamat
        alamat_data = self._parse_alamat(emp)
        
        # Gender mapping
        gender = self.get_field_value(emp, 'gender') or ''
        gender_code = self.GENDER_MAP.get(gender.lower(), '')
        
        # Marital status mapping
        marital = self.get_field_value(emp, 'status_kawin') or ''
        marital_code = self.MARITAL_MAP.get(marital.lower(), 'TK')
        
        # Birthday
        birthday = self.get_field_value(emp, 'birthday')
        
        # BPJS data
        bpjs_number = self.get_formatted_field_value(bpjs_kes, 'number') if bpjs_kes else ''
        kelas = self.get_formatted_field_value(bpjs_kes, 'kelas') if bpjs_kes else ''
        faskes_code = self.get_formatted_field_value(bpjs_kes, 'faskes_code') if bpjs_kes else ''
        faskes_name = self.get_formatted_field_value(bpjs_kes, 'faskes_tk1') if bpjs_kes else ''
        tgl_aktif = self.get_field_value(bpjs_kes, 'date_start') if bpjs_kes else None
        
        # Write row data
        data = [
            idx,                                                    # NO
            self.get_formatted_field_value(emp, 'nik'),            # NIK
            self.get_formatted_field_value(emp, 'name'),           # NAMA LENGKAP
            self.get_formatted_field_value(emp, 'place_of_birth'), # TEMPAT LAHIR
            birthday,                                               # TANGGAL LAHIR
            gender_code,                                            # JENIS KELAMIN
            marital_code,                                           # STATUS PERKAWINAN
            alamat_data.get('alamat', ''),                         # ALAMAT
            alamat_data.get('rt', ''),                             # RT
            alamat_data.get('rw', ''),                             # RW
            alamat_data.get('kelurahan', ''),                      # KELURAHAN
            alamat_data.get('kecamatan', ''),                      # KECAMATAN
            alamat_data.get('kota', ''),                           # KOTA/KAB
            alamat_data.get('provinsi', ''),                       # PROVINSI
            alamat_data.get('kode_pos', ''),                       # KODE POS
            self.get_formatted_field_value(emp, 'mobile_phone'),   # NO HP
            self.get_formatted_field_value(emp, 'work_email'),     # EMAIL
            bpjs_number,                                            # NO KARTU BPJS
            kelas,                                                  # KELAS RAWAT
            faskes_code,                                            # KODE FASKES TK1
            faskes_name,                                            # NAMA FASKES TK1
            tgl_aktif,                                              # TGL MULAI AKTIF
            'AKTIF',                                                # STATUS KEPESERTAAN
            '',                                                     # GAJI (optional)
            self.env.company.bpjs_code if hasattr(self.env.company, 'bpjs_code') else '',  # KODE PERUSAHAAN
            self.env.company.name,                                  # NAMA PERUSAHAAN
            'TK',                                                   # HUBUNGAN KELUARGA (TK=Tenaga Kerja)
            '',                                                     # NIK PESERTA UTAMA
        ]
        
        for col, value in enumerate(data):
            if col == 4 and value:  # TANGGAL LAHIR
                sheet.write(row, col, value, formats['date'])
            elif col == 21 and value:  # TGL MULAI AKTIF
                sheet.write(row, col, value, formats['date'])
            elif col == 0:  # NO
                sheet.write(row, col, value, formats['cell_center'])
            elif col in [5, 6]:  # JENIS KELAMIN, STATUS
                sheet.write(row, col, value, formats['cell_center'])
            else:
                sheet.write(row, col, value if value else '', formats['cell'])
    
    def _parse_alamat(self, emp):
        """
        Parse alamat dari field alamat_ktp.
        
        Returns:
            dict: Parsed alamat components
        """
        alamat_ktp = self.get_formatted_field_value(emp, 'alamat_ktp') or ''
        
        # Default values
        result = {
            'alamat': alamat_ktp,
            'rt': '',
            'rw': '',
            'kelurahan': '',
            'kecamatan': '',
            'kota': '',
            'provinsi': '',
            'kode_pos': '',
        }
        
        # Try to get from separate fields if available
        if hasattr(emp, 'rt'):
            result['rt'] = self.get_formatted_field_value(emp, 'rt')
        if hasattr(emp, 'rw'):
            result['rw'] = self.get_formatted_field_value(emp, 'rw')
        if hasattr(emp, 'kelurahan'):
            result['kelurahan'] = self.get_formatted_field_value(emp, 'kelurahan')
        if hasattr(emp, 'kecamatan'):
            result['kecamatan'] = self.get_formatted_field_value(emp, 'kecamatan')
        if hasattr(emp, 'kota'):
            result['kota'] = self.get_formatted_field_value(emp, 'kota')
        if hasattr(emp, 'provinsi'):
            result['provinsi'] = self.get_formatted_field_value(emp, 'provinsi')
        if hasattr(emp, 'kode_pos'):
            result['kode_pos'] = self.get_formatted_field_value(emp, 'kode_pos')
        
        return result
    
    def _write_family_sheet(self, workbook, formats, employees):
        """Write family data sheet for BPJS family members."""
        sheet = workbook.add_worksheet('Data Keluarga')
        
        headers = [
            'NO', 'NIK TENAGA KERJA', 'NAMA TENAGA KERJA',
            'NIK ANGGOTA KELUARGA', 'NAMA ANGGOTA KELUARGA',
            'TEMPAT LAHIR', 'TANGGAL LAHIR', 'JENIS KELAMIN',
            'HUBUNGAN KELUARGA', 'NO KARTU BPJS', 'KELAS RAWAT',
            'KODE FASKES TK1', 'NAMA FASKES TK1'
        ]
        
        # Write title
        sheet.merge_range(0, 0, 0, len(headers) - 1,
                         'DATA ANGGOTA KELUARGA PESERTA BPJS KESEHATAN',
                         formats['title'])
        
        # Write headers
        for col, header in enumerate(headers):
            sheet.write(2, col, header, formats['header'])
        
        sheet.freeze_panes(3, 0)
        
        # Write data
        row = 3
        no = 1
        
        for emp in employees:
            emp_nik = self.get_formatted_field_value(emp, 'nik')
            emp_name = self.get_formatted_field_value(emp, 'name')
            
            # Get BPJS Kesehatan data for faskes reference
            bpjs_kes = None
            if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
                for bpjs in emp.bpjs_ids:
                    if self.get_field_value(bpjs, 'bpjs_type') == 'kesehatan':
                        bpjs_kes = bpjs
                        break
            
            faskes_code = self.get_formatted_field_value(bpjs_kes, 'faskes_code') if bpjs_kes else ''
            faskes_name = self.get_formatted_field_value(bpjs_kes, 'faskes_tk1') if bpjs_kes else ''
            kelas = self.get_formatted_field_value(bpjs_kes, 'kelas') if bpjs_kes else ''
            
            # Write spouse if exists
            spouse_name = self.get_field_value(emp, 'spouse_name')
            if spouse_name:
                spouse_nik = self.get_formatted_field_value(emp, 'spouse_nik')
                spouse_birthday = self.get_field_value(emp, 'spouse_birthday')
                
                data = [
                    no, emp_nik, emp_name,
                    spouse_nik, spouse_name,
                    '', spouse_birthday, '',
                    'SUAMI/ISTRI', '', kelas,
                    faskes_code, faskes_name
                ]
                
                for col, value in enumerate(data):
                    if col in [6] and value:  # TANGGAL LAHIR
                        sheet.write(row, col, value, formats['date'])
                    elif col == 0:
                        sheet.write(row, col, value, formats['cell_center'])
                    else:
                        sheet.write(row, col, value if value else '', formats['cell'])
                
                row += 1
                no += 1
            
            # Write children
            if hasattr(emp, 'child_ids') and emp.child_ids:
                for child in emp.child_ids:
                    child_birthday = self.get_field_value(child, 'birth_date')
                    child_gender = self.get_field_value(child, 'gender') or ''
                    gender_code = self.GENDER_MAP.get(child_gender.lower(), '')
                    
                    data = [
                        no, emp_nik, emp_name,
                        self.get_formatted_field_value(child, 'nik') if hasattr(child, 'nik') else '',
                        self.get_formatted_field_value(child, 'name'),
                        '', child_birthday, gender_code,
                        'ANAK', '', kelas,
                        faskes_code, faskes_name
                    ]
                    
                    for col, value in enumerate(data):
                        if col in [6] and value:
                            sheet.write(row, col, value, formats['date'])
                        elif col == 0:
                            sheet.write(row, col, value, formats['cell_center'])
                        else:
                            sheet.write(row, col, value if value else '', formats['cell'])
                    
                    row += 1
                    no += 1
        
        self._auto_fit_columns(sheet, len(headers))
    
    def _write_info_sheet(self, workbook, formats, employees, export_type):
        """Write information sheet."""
        sheet = workbook.add_worksheet('Informasi')
        
        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 50)
        
        # Title
        sheet.merge_range('A1:B1', 'INFORMASI EXPORT BPJS KESEHATAN', formats['title'])
        
        row = 3
        info_data = [
            ('Tanggal Export', datetime.now().strftime('%d-%m-%Y %H:%M:%S')),
            ('Diekspor Oleh', self.env.user.name),
            ('Perusahaan', self.env.company.name),
            ('Tipe Export', export_type.upper()),
            ('', ''),
            ('Total Karyawan', len(employees)),
        ]
        
        for label, value in info_data:
            if label:
                sheet.write(row, 0, label, formats['header'])
                sheet.write(row, 1, value, formats['cell'])
            row += 1
        
        # Notes
        row += 2
        sheet.write(row, 0, 'CATATAN:', formats['warning'])
        row += 1
        
        notes = [
            '1. Pastikan data NIK sudah benar sebelum disubmit ke BPJS',
            '2. Format tanggal lahir: DD-MM-YYYY',
            '3. Kode jenis kelamin: L=Laki-laki, P=Perempuan',
            '4. Kode status perkawinan: TK=Tidak Kawin, K=Kawin, D=Duda/Janda, C=Cerai',
            '5. Hubungan keluarga: TK=Tenaga Kerja, SUAMI/ISTRI, ANAK',
        ]
        
        for note in notes:
            sheet.write(row, 0, note, formats['info'])
            row += 1
    
    def _auto_fit_columns(self, sheet, num_columns):
        """Auto-fit column widths."""
        widths = [5, 18, 30, 15, 12, 5, 5, 40, 5, 5, 15, 15, 15, 15, 8, 15, 25, 20, 5, 10, 30, 12, 10, 12, 15, 30, 15, 18]
        
        for col in range(num_columns):
            width = widths[col] if col < len(widths) else 15
            sheet.set_column(col, col, width)
    
    def export_registration(self, employees):
        """Export untuk pendaftaran peserta baru."""
        return self.export(employees, export_type='new', include_family=True)
    
    def export_update(self, employees):
        """Export untuk perubahan data peserta."""
        return self.export(employees, export_type='update', include_family=False)
    
    def export_inactive(self, employees):
        """Export untuk penonaktifan peserta."""
        return self.export(employees, export_type='inactive', include_family=False)
