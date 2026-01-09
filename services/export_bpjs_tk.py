# -*- coding: utf-8 -*-
"""
Export Service BPJS Ketenagakerjaan untuk yhc_employee_export.

Service ini menangani export data karyawan ke format yang sesuai
dengan ketentuan pelaporan BPJS Ketenagakerjaan.

Format export mengikuti template resmi dari BPJS Ketenagakerjaan untuk:
- Pendaftaran peserta baru
- Perubahan data peserta (mutasi)
- Laporan iuran bulanan
- Pengajuan klaim
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


class EmployeeExportBpjsTk(EmployeeExportBase):
    """
    Service untuk export data BPJS Ketenagakerjaan.
    
    BPJS Ketenagakerjaan memiliki 4 program:
    - JHT (Jaminan Hari Tua)
    - JKK (Jaminan Kecelakaan Kerja)
    - JKM (Jaminan Kematian)
    - JP (Jaminan Pensiun)
    """
    
    # Kolom standar untuk format BPJS Ketenagakerjaan
    HEADER_COLUMNS = [
        'NO',
        'NIK',
        'NO KPJ',
        'NAMA LENGKAP',
        'TEMPAT LAHIR',
        'TANGGAL LAHIR',
        'JENIS KELAMIN',
        'STATUS PERKAWINAN',
        'ALAMAT',
        'KELURAHAN',
        'KECAMATAN',
        'KOTA/KAB',
        'PROVINSI',
        'KODE POS',
        'NO HP',
        'EMAIL',
        'NAMA IBU KANDUNG',
        'TGL MULAI BEKERJA',
        'UPAH',
        'STATUS KEPESERTAAN',
        'JHT',
        'JKK',
        'JKM',
        'JP',
        'KODE PERUSAHAAN',
        'NAMA PERUSAHAAN',
        'NPWP PERUSAHAAN',
    ]
    
    # Kolom untuk laporan iuran
    IURAN_COLUMNS = [
        'NO',
        'NO KPJ',
        'NIK',
        'NAMA LENGKAP',
        'UPAH',
        'IURAN JHT TK',
        'IURAN JHT PERUSAHAAN',
        'TOTAL JHT',
        'IURAN JKK',
        'IURAN JKM',
        'IURAN JP TK',
        'IURAN JP PERUSAHAAN',
        'TOTAL JP',
        'TOTAL IURAN TK',
        'TOTAL IURAN PERUSAHAAN',
        'GRAND TOTAL',
    ]
    
    # Persentase iuran (default)
    IURAN_RATE = {
        'jht_tk': 0.02,       # 2% dari TK
        'jht_company': 0.037,  # 3.7% dari perusahaan
        'jkk': 0.0054,         # 0.54% dari perusahaan (kategori risiko menengah)
        'jkm': 0.003,          # 0.3% dari perusahaan
        'jp_tk': 0.01,         # 1% dari TK
        'jp_company': 0.02,    # 2% dari perusahaan
    }
    
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
    }
    
    def __init__(self, env):
        """Initialize BPJS Ketenagakerjaan export service."""
        super().__init__(env)
        
        if not XLSXWRITER_AVAILABLE:
            raise ImportError(
                "Library xlsxwriter tidak terinstall. "
                "Silakan install dengan: pip install xlsxwriter"
            )
    
    def export(self, employees, export_type='active', include_iuran=False):
        """
        Export data BPJS Ketenagakerjaan.
        
        Args:
            employees: hr.employee recordset
            export_type (str): Tipe export ('active', 'new', 'mutation', 'resign')
            include_iuran (bool): Include perhitungan iuran
            
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
        
        if include_iuran:
            self._write_iuran_sheet(workbook, formats, employees)
        
        # Info sheet
        self._write_info_sheet(workbook, formats, employees, export_type)
        
        workbook.close()
        output.seek(0)
        
        # Generate filename
        type_suffix = {
            'active': 'peserta_aktif',
            'new': 'pendaftaran_baru',
            'mutation': 'mutasi',
            'resign': 'pengunduran_diri',
        }
        suffix = type_suffix.get(export_type, 'data')
        filename = self.generate_filename(f'bpjs_tk_{suffix}', 'xlsx')
        
        return output.getvalue(), filename
    
    def _setup_formats(self, workbook):
        """Setup Excel formats."""
        return {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#1565C0',  # BPJS TK Blue
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
            'currency': workbook.add_format({
                'border': 1,
                'valign': 'vcenter',
                'num_format': '#,##0',
            }),
            'currency_bold': workbook.add_format({
                'border': 1,
                'bold': True,
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
            'total': workbook.add_format({
                'bold': True,
                'bg_color': '#E3F2FD',
                'border': 1,
                'valign': 'vcenter',
                'num_format': '#,##0',
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
            'active': 'LAPORAN DATA PESERTA BPJS KETENAGAKERJAAN AKTIF',
            'new': 'DATA PENDAFTARAN PESERTA BPJS KETENAGAKERJAAN BARU',
            'mutation': 'DATA MUTASI PESERTA BPJS KETENAGAKERJAAN',
            'resign': 'DATA PENGUNDURAN DIRI PESERTA BPJS KETENAGAKERJAAN',
        }
        return titles.get(export_type, 'DATA PESERTA BPJS KETENAGAKERJAAN')
    
    def _write_employee_row(self, sheet, formats, row, idx, emp):
        """Write single employee row."""
        # Get BPJS TK data
        bpjs_tk = None
        if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
            for bpjs in emp.bpjs_ids:
                if self.get_field_value(bpjs, 'bpjs_type') == 'ketenagakerjaan':
                    bpjs_tk = bpjs
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
        
        # First contract date
        tgl_masuk = self.get_field_value(emp, 'first_contract_date')
        
        # BPJS data
        kpj_number = self.get_formatted_field_value(bpjs_tk, 'number') if bpjs_tk else ''
        
        # Program participation (default all Y for active)
        jht = 'Y'
        jkk = 'Y'
        jkm = 'Y'
        jp = 'Y'
        
        # Get upah/salary if available
        upah = 0
        if hasattr(emp, 'payroll_id') and emp.payroll_id:
            upah = self.get_field_value(emp.payroll_id, 'wage') or 0
        
        # Write row data
        data = [
            idx,                                                    # NO
            self.get_formatted_field_value(emp, 'nik'),            # NIK
            kpj_number,                                             # NO KPJ
            self.get_formatted_field_value(emp, 'name'),           # NAMA LENGKAP
            self.get_formatted_field_value(emp, 'place_of_birth'), # TEMPAT LAHIR
            birthday,                                               # TANGGAL LAHIR
            gender_code,                                            # JENIS KELAMIN
            marital_code,                                           # STATUS PERKAWINAN
            alamat_data.get('alamat', ''),                         # ALAMAT
            alamat_data.get('kelurahan', ''),                      # KELURAHAN
            alamat_data.get('kecamatan', ''),                      # KECAMATAN
            alamat_data.get('kota', ''),                           # KOTA/KAB
            alamat_data.get('provinsi', ''),                       # PROVINSI
            alamat_data.get('kode_pos', ''),                       # KODE POS
            self.get_formatted_field_value(emp, 'mobile_phone'),   # NO HP
            self.get_formatted_field_value(emp, 'work_email'),     # EMAIL
            self.get_formatted_field_value(emp, 'nama_ibu'),       # NAMA IBU KANDUNG
            tgl_masuk,                                              # TGL MULAI BEKERJA
            upah,                                                   # UPAH
            'AKTIF',                                                # STATUS KEPESERTAAN
            jht,                                                    # JHT
            jkk,                                                    # JKK
            jkm,                                                    # JKM
            jp,                                                     # JP
            self.env.company.bpjs_tk_code if hasattr(self.env.company, 'bpjs_tk_code') else '',  # KODE PERUSAHAAN
            self.env.company.name,                                  # NAMA PERUSAHAAN
            self.env.company.vat or '',                             # NPWP PERUSAHAAN
        ]
        
        for col, value in enumerate(data):
            if col in [5, 17] and value:  # TANGGAL
                sheet.write(row, col, value, formats['date'])
            elif col == 18 and value:  # UPAH
                sheet.write(row, col, value, formats['currency'])
            elif col == 0:  # NO
                sheet.write(row, col, value, formats['cell_center'])
            elif col in [6, 7, 20, 21, 22, 23]:  # Kode-kode
                sheet.write(row, col, value, formats['cell_center'])
            else:
                sheet.write(row, col, value if value else '', formats['cell'])
    
    def _parse_alamat(self, emp):
        """Parse alamat dari field alamat_ktp."""
        alamat_ktp = self.get_formatted_field_value(emp, 'alamat_ktp') or ''
        
        result = {
            'alamat': alamat_ktp,
            'kelurahan': '',
            'kecamatan': '',
            'kota': '',
            'provinsi': '',
            'kode_pos': '',
        }
        
        # Try to get from separate fields if available
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
    
    def _write_iuran_sheet(self, workbook, formats, employees):
        """Write iuran calculation sheet."""
        sheet = workbook.add_worksheet('Laporan Iuran')
        
        # Write title
        period = datetime.now().strftime('%B %Y')
        sheet.merge_range(0, 0, 0, len(self.IURAN_COLUMNS) - 1,
                         f'LAPORAN IURAN BPJS KETENAGAKERJAAN - {period.upper()}',
                         formats['title'])
        
        # Write headers
        for col, header in enumerate(self.IURAN_COLUMNS):
            sheet.write(2, col, header, formats['header'])
        
        sheet.freeze_panes(3, 0)
        
        # Initialize totals
        totals = {
            'upah': 0,
            'jht_tk': 0,
            'jht_company': 0,
            'total_jht': 0,
            'jkk': 0,
            'jkm': 0,
            'jp_tk': 0,
            'jp_company': 0,
            'total_jp': 0,
            'total_tk': 0,
            'total_company': 0,
            'grand_total': 0,
        }
        
        # Write data
        row = 3
        for idx, emp in enumerate(employees, 1):
            row_data = self._calculate_iuran(emp, idx)
            
            # Update totals
            for key in totals:
                if key in row_data:
                    totals[key] += row_data[key]
            
            # Write row
            data = [
                row_data['no'],
                row_data['kpj'],
                row_data['nik'],
                row_data['name'],
                row_data['upah'],
                row_data['jht_tk'],
                row_data['jht_company'],
                row_data['total_jht'],
                row_data['jkk'],
                row_data['jkm'],
                row_data['jp_tk'],
                row_data['jp_company'],
                row_data['total_jp'],
                row_data['total_tk'],
                row_data['total_company'],
                row_data['grand_total'],
            ]
            
            for col, value in enumerate(data):
                if col == 0:  # NO
                    sheet.write(row, col, value, formats['cell_center'])
                elif col in [1, 2, 3]:  # Text
                    sheet.write(row, col, value, formats['cell'])
                else:  # Currency
                    sheet.write(row, col, value, formats['currency'])
            
            row += 1
        
        # Write total row
        row += 1
        sheet.write(row, 0, '', formats['total'])
        sheet.write(row, 1, '', formats['total'])
        sheet.write(row, 2, '', formats['total'])
        sheet.write(row, 3, 'TOTAL', formats['total'])
        sheet.write(row, 4, totals['upah'], formats['total'])
        sheet.write(row, 5, totals['jht_tk'], formats['total'])
        sheet.write(row, 6, totals['jht_company'], formats['total'])
        sheet.write(row, 7, totals['total_jht'], formats['total'])
        sheet.write(row, 8, totals['jkk'], formats['total'])
        sheet.write(row, 9, totals['jkm'], formats['total'])
        sheet.write(row, 10, totals['jp_tk'], formats['total'])
        sheet.write(row, 11, totals['jp_company'], formats['total'])
        sheet.write(row, 12, totals['total_jp'], formats['total'])
        sheet.write(row, 13, totals['total_tk'], formats['total'])
        sheet.write(row, 14, totals['total_company'], formats['total'])
        sheet.write(row, 15, totals['grand_total'], formats['total'])
        
        # Auto-fit columns
        widths = [5, 18, 18, 30, 15, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 15]
        for col, width in enumerate(widths):
            sheet.set_column(col, col, width)
    
    def _calculate_iuran(self, emp, idx):
        """Calculate iuran for single employee."""
        # Get KPJ number
        kpj = ''
        if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
            for bpjs in emp.bpjs_ids:
                if self.get_field_value(bpjs, 'bpjs_type') == 'ketenagakerjaan':
                    kpj = self.get_formatted_field_value(bpjs, 'number')
                    break
        
        # Get upah
        upah = 0
        if hasattr(emp, 'payroll_id') and emp.payroll_id:
            upah = self.get_field_value(emp.payroll_id, 'wage') or 0
        
        # Calculate iuran
        jht_tk = upah * self.IURAN_RATE['jht_tk']
        jht_company = upah * self.IURAN_RATE['jht_company']
        total_jht = jht_tk + jht_company
        
        jkk = upah * self.IURAN_RATE['jkk']
        jkm = upah * self.IURAN_RATE['jkm']
        
        # JP has maximum wage cap (currently Rp 9.077.600)
        jp_max_wage = 9077600
        jp_wage = min(upah, jp_max_wage)
        jp_tk = jp_wage * self.IURAN_RATE['jp_tk']
        jp_company = jp_wage * self.IURAN_RATE['jp_company']
        total_jp = jp_tk + jp_company
        
        total_tk = jht_tk + jp_tk
        total_company = jht_company + jkk + jkm + jp_company
        grand_total = total_tk + total_company
        
        return {
            'no': idx,
            'kpj': kpj,
            'nik': self.get_formatted_field_value(emp, 'nik'),
            'name': self.get_formatted_field_value(emp, 'name'),
            'upah': upah,
            'jht_tk': jht_tk,
            'jht_company': jht_company,
            'total_jht': total_jht,
            'jkk': jkk,
            'jkm': jkm,
            'jp_tk': jp_tk,
            'jp_company': jp_company,
            'total_jp': total_jp,
            'total_tk': total_tk,
            'total_company': total_company,
            'grand_total': grand_total,
        }
    
    def _write_info_sheet(self, workbook, formats, employees, export_type):
        """Write information sheet."""
        sheet = workbook.add_worksheet('Informasi')
        
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 50)
        
        # Title
        sheet.merge_range('A1:B1', 'INFORMASI EXPORT BPJS KETENAGAKERJAAN', formats['title'])
        
        row = 3
        info_data = [
            ('Tanggal Export', datetime.now().strftime('%d-%m-%Y %H:%M:%S')),
            ('Diekspor Oleh', self.env.user.name),
            ('Perusahaan', self.env.company.name),
            ('NPWP Perusahaan', self.env.company.vat or '-'),
            ('Tipe Export', export_type.upper()),
            ('', ''),
            ('Total Karyawan', len(employees)),
        ]
        
        for label, value in info_data:
            if label:
                sheet.write(row, 0, label, formats['header'])
                sheet.write(row, 1, value, formats['cell'])
            row += 1
        
        # Program info
        row += 2
        sheet.write(row, 0, 'PROGRAM BPJS KETENAGAKERJAAN:', formats['warning'])
        row += 1
        
        programs = [
            ('JHT', 'Jaminan Hari Tua', '2% TK + 3.7% Perusahaan'),
            ('JKK', 'Jaminan Kecelakaan Kerja', '0.24% - 1.74% Perusahaan (tergantung risiko)'),
            ('JKM', 'Jaminan Kematian', '0.3% Perusahaan'),
            ('JP', 'Jaminan Pensiun', '1% TK + 2% Perusahaan (max upah Rp 9.077.600)'),
        ]
        
        for code, name, rate in programs:
            sheet.write(row, 0, f'{code} - {name}', formats['cell'])
            sheet.write(row, 1, rate, formats['info'])
            row += 1
        
        # Notes
        row += 2
        sheet.write(row, 0, 'CATATAN:', formats['warning'])
        row += 1
        
        notes = [
            '1. NO KPJ adalah Nomor Kartu Peserta Jamsostek',
            '2. Pastikan data NIK sudah benar sebelum disubmit',
            '3. Format tanggal: DD-MM-YYYY',
            '4. Upah yang dilaporkan adalah upah pokok + tunjangan tetap',
            '5. Batas maksimal upah untuk JP: Rp 9.077.600 (per Januari 2024)',
        ]
        
        for note in notes:
            sheet.write(row, 0, note, formats['info'])
            row += 1
    
    def _auto_fit_columns(self, sheet, num_columns):
        """Auto-fit column widths."""
        widths = [5, 18, 18, 30, 15, 12, 5, 5, 40, 15, 15, 15, 15, 8, 15, 25, 25, 12, 15, 10, 5, 5, 5, 5, 15, 30, 20]
        
        for col in range(num_columns):
            width = widths[col] if col < len(widths) else 15
            sheet.set_column(col, col, width)
    
    def export_registration(self, employees):
        """Export untuk pendaftaran peserta baru."""
        return self.export(employees, export_type='new', include_iuran=False)
    
    def export_iuran(self, employees):
        """Export laporan iuran bulanan."""
        return self.export(employees, export_type='active', include_iuran=True)
    
    def export_mutation(self, employees):
        """Export untuk mutasi data peserta."""
        return self.export(employees, export_type='mutation', include_iuran=False)
    
    def export_resign(self, employees):
        """Export untuk pengunduran diri peserta."""
        return self.export(employees, export_type='resign', include_iuran=False)
