# -*- coding: utf-8 -*-
"""
Export Service Regulatory untuk yhc_employee_export.

Service ini menjadi facade untuk berbagai export format regulatory/regulasi:
- BPJS Kesehatan
- BPJS Ketenagakerjaan
- Laporan Pajak (SPT)
- Wajib Lapor Ketenagakerjaan

Service ini memudahkan akses ke berbagai format regulatory dari satu titik.
"""

from datetime import datetime, date
import logging

from .export_base import EmployeeExportBase
from .export_bpjs_kes import EmployeeExportBpjsKes
from .export_bpjs_tk import EmployeeExportBpjsTk

_logger = logging.getLogger(__name__)


class EmployeeExportRegulatory(EmployeeExportBase):
    """
    Facade service untuk export format regulatory.
    
    Menyediakan interface terpadu untuk berbagai format export
    yang dibutuhkan untuk pelaporan ke instansi pemerintah.
    """
    
    # Available regulatory export types
    EXPORT_TYPES = {
        'bpjs_kes': {
            'name': 'BPJS Kesehatan',
            'description': 'Export data untuk pelaporan BPJS Kesehatan',
            'subtypes': ['active', 'new', 'update', 'inactive'],
        },
        'bpjs_tk': {
            'name': 'BPJS Ketenagakerjaan',
            'description': 'Export data untuk pelaporan BPJS Ketenagakerjaan',
            'subtypes': ['active', 'new', 'mutation', 'resign', 'iuran'],
        },
        'spt': {
            'name': 'SPT Tahunan (1721)',
            'description': 'Export data untuk pelaporan pajak penghasilan',
            'subtypes': ['1721_a1', '1721_i'],
        },
        'wlk': {
            'name': 'Wajib Lapor Ketenagakerjaan',
            'description': 'Export data untuk laporan wajib ketenagakerjaan',
            'subtypes': ['semester1', 'semester2'],
        },
    }
    
    def __init__(self, env):
        """Initialize regulatory export service."""
        super().__init__(env)
        self._bpjs_kes = None
        self._bpjs_tk = None
    
    @property
    def bpjs_kes(self):
        """Get BPJS Kesehatan export service."""
        if self._bpjs_kes is None:
            self._bpjs_kes = EmployeeExportBpjsKes(self.env)
        return self._bpjs_kes
    
    @property
    def bpjs_tk(self):
        """Get BPJS Ketenagakerjaan export service."""
        if self._bpjs_tk is None:
            self._bpjs_tk = EmployeeExportBpjsTk(self.env)
        return self._bpjs_tk
    
    def get_available_exports(self):
        """
        Get list of available regulatory exports.
        
        Returns:
            dict: Available export types with info
        """
        return self.EXPORT_TYPES
    
    def export(self, employees, export_type, subtype=None, **kwargs):
        """
        Export data ke format regulatory tertentu.
        
        Args:
            employees: hr.employee recordset
            export_type (str): Tipe export ('bpjs_kes', 'bpjs_tk', 'spt', 'wlk')
            subtype (str): Sub-tipe export (optional)
            **kwargs: Additional arguments
            
        Returns:
            tuple: (bytes, filename)
        """
        self.validate_employees(employees)
        
        if export_type == 'bpjs_kes':
            return self._export_bpjs_kes(employees, subtype, **kwargs)
        elif export_type == 'bpjs_tk':
            return self._export_bpjs_tk(employees, subtype, **kwargs)
        elif export_type == 'spt':
            return self._export_spt(employees, subtype, **kwargs)
        elif export_type == 'wlk':
            return self._export_wlk(employees, subtype, **kwargs)
        else:
            raise ValueError(f"Unknown export type: {export_type}")
    
    def _export_bpjs_kes(self, employees, subtype=None, **kwargs):
        """Export BPJS Kesehatan."""
        subtype = subtype or 'active'
        include_family = kwargs.get('include_family', True)
        
        if subtype == 'new':
            return self.bpjs_kes.export_registration(employees)
        elif subtype == 'update':
            return self.bpjs_kes.export_update(employees)
        elif subtype == 'inactive':
            return self.bpjs_kes.export_inactive(employees)
        else:
            return self.bpjs_kes.export(employees, 'active', include_family)
    
    def _export_bpjs_tk(self, employees, subtype=None, **kwargs):
        """Export BPJS Ketenagakerjaan."""
        subtype = subtype or 'active'
        
        if subtype == 'new':
            return self.bpjs_tk.export_registration(employees)
        elif subtype == 'mutation':
            return self.bpjs_tk.export_mutation(employees)
        elif subtype == 'resign':
            return self.bpjs_tk.export_resign(employees)
        elif subtype == 'iuran':
            return self.bpjs_tk.export_iuran(employees)
        else:
            return self.bpjs_tk.export(employees, 'active', False)
    
    def _export_spt(self, employees, subtype=None, **kwargs):
        """
        Export SPT format.
        
        TODO: Implement SPT 1721-A1 dan 1721-I format
        """
        subtype = subtype or '1721_a1'
        
        # Placeholder - akan diimplementasi sesuai format DJP
        _logger.warning("SPT export belum diimplementasi sepenuhnya")
        
        return self._export_spt_1721_a1(employees, **kwargs)
    
    def _export_spt_1721_a1(self, employees, **kwargs):
        """Export SPT 1721-A1 format."""
        from io import BytesIO
        import xlsxwriter
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        formats = {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
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
            'currency': workbook.add_format({
                'border': 1,
                'valign': 'vcenter',
                'num_format': '#,##0',
            }),
            'title': workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
            }),
        }
        
        sheet = workbook.add_worksheet('1721-A1')
        
        # Headers sesuai format 1721-A1
        headers = [
            'NO', 'NPWP', 'NIK', 'NAMA', 'ALAMAT', 'STATUS PTKP',
            'NAMA JABATAN', 'JENIS KELAMIN', 'STATUS KARYAWAN',
            'GAJI POKOK', 'TUNJANGAN', 'BRUTO', 'BIAYA JABATAN',
            'IURAN PENSIUN', 'NETO', 'NETO SETAHUN', 'PTKP',
            'PKP', 'PPH TERUTANG', 'PPH DIPOTONG'
        ]
        
        # Write title
        year = kwargs.get('year', datetime.now().year)
        sheet.merge_range(0, 0, 0, len(headers) - 1,
                         f'BUKTI PEMOTONGAN PPH PASAL 21 (1721-A1) TAHUN {year}',
                         formats['title'])
        
        # Write headers
        for col, header in enumerate(headers):
            sheet.write(2, col, header, formats['header'])
        
        sheet.freeze_panes(3, 0)
        
        # Write data (simplified)
        row = 3
        for idx, emp in enumerate(employees, 1):
            # Get payroll data if available
            npwp = ''
            if hasattr(emp, 'payroll_id') and emp.payroll_id:
                npwp = self.get_formatted_field_value(emp.payroll_id, 'npwp')
            
            data = [
                idx,
                npwp,
                self.get_formatted_field_value(emp, 'nik'),
                self.get_formatted_field_value(emp, 'name'),
                self.get_formatted_field_value(emp, 'alamat_ktp'),
                'TK/0',  # Default PTKP status
                self.get_formatted_field_value(emp, 'job_id.name'),
                self.get_formatted_field_value(emp, 'gender'),
                self.get_formatted_field_value(emp, 'employment_status'),
                0,  # Gaji Pokok
                0,  # Tunjangan
                0,  # Bruto
                0,  # Biaya Jabatan
                0,  # Iuran Pensiun
                0,  # Neto
                0,  # Neto Setahun
                0,  # PTKP
                0,  # PKP
                0,  # PPH Terutang
                0,  # PPH Dipotong
            ]
            
            for col, value in enumerate(data):
                if col >= 9:  # Currency columns
                    sheet.write(row, col, value, formats['currency'])
                else:
                    sheet.write(row, col, value if value else '', formats['cell'])
            
            row += 1
        
        # Auto-fit
        for col in range(len(headers)):
            sheet.set_column(col, col, 15)
        
        workbook.close()
        output.seek(0)
        
        filename = self.generate_filename(f'spt_1721_a1_{year}', 'xlsx')
        return output.getvalue(), filename
    
    def _export_wlk(self, employees, subtype=None, **kwargs):
        """
        Export Wajib Lapor Ketenagakerjaan.
        
        Format sesuai dengan Permenaker tentang Wajib Lapor Ketenagakerjaan.
        """
        from io import BytesIO
        import xlsxwriter
        
        subtype = subtype or 'semester1'
        semester = 1 if subtype == 'semester1' else 2
        year = kwargs.get('year', datetime.now().year)
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        formats = {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#2E7D32',
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
            'title': workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
            }),
        }
        
        sheet = workbook.add_worksheet('Data Tenaga Kerja')
        
        # Headers
        headers = [
            'NO', 'NIK', 'NAMA LENGKAP', 'JENIS KELAMIN', 'TEMPAT LAHIR',
            'TANGGAL LAHIR', 'PENDIDIKAN TERAKHIR', 'STATUS PERKAWINAN',
            'KEWARGANEGARAAN', 'ALAMAT', 'JABATAN', 'UNIT KERJA',
            'TANGGAL MULAI BEKERJA', 'JENIS PEKERJAAN', 'STATUS PEKERJA',
            'UPAH PER BULAN', 'JAMINAN SOSIAL'
        ]
        
        # Write title
        sheet.merge_range(0, 0, 0, len(headers) - 1,
                         f'WAJIB LAPOR KETENAGAKERJAAN - SEMESTER {semester} TAHUN {year}',
                         formats['title'])
        
        # Company info
        sheet.write(1, 0, f'Perusahaan: {self.env.company.name}')
        
        # Write headers
        for col, header in enumerate(headers):
            sheet.write(3, col, header, formats['header'])
        
        sheet.freeze_panes(4, 0)
        
        # Write data
        row = 4
        for idx, emp in enumerate(employees, 1):
            birthday = self.get_field_value(emp, 'birthday')
            first_contract = self.get_field_value(emp, 'first_contract_date')
            
            # Get education
            pendidikan = ''
            if hasattr(emp, 'education_ids') and emp.education_ids:
                latest = emp.education_ids[0]
                pendidikan = self.get_formatted_field_value(latest, 'certificate')
            
            data = [
                idx,
                self.get_formatted_field_value(emp, 'nik'),
                self.get_formatted_field_value(emp, 'name'),
                self.get_selection_label(emp, 'gender'),
                self.get_formatted_field_value(emp, 'place_of_birth'),
                birthday.strftime('%d-%m-%Y') if birthday else '',
                pendidikan,
                self.get_formatted_field_value(emp, 'status_kawin'),
                'WNI',
                self.get_formatted_field_value(emp, 'alamat_ktp'),
                self.get_formatted_field_value(emp, 'job_id.name'),
                self.get_formatted_field_value(emp, 'department_id.name'),
                first_contract.strftime('%d-%m-%Y') if first_contract else '',
                self.get_formatted_field_value(emp, 'employee_category_id.name'),
                self.get_formatted_field_value(emp, 'employment_status'),
                0,  # Upah
                'BPJS Kesehatan, BPJS TK',
            ]
            
            for col, value in enumerate(data):
                if col == 0:
                    sheet.write(row, col, value, formats['cell_center'])
                else:
                    sheet.write(row, col, value if value else '', formats['cell'])
            
            row += 1
        
        # Summary
        row += 2
        sheet.write(row, 0, f'Total Tenaga Kerja: {len(employees)}')
        
        # Statistics
        male_count = sum(1 for e in employees if self.get_field_value(e, 'gender') == 'male')
        female_count = len(employees) - male_count
        
        row += 1
        sheet.write(row, 0, f'Laki-laki: {male_count}, Perempuan: {female_count}')
        
        # Auto-fit columns
        for col in range(len(headers)):
            sheet.set_column(col, col, 18)
        
        workbook.close()
        output.seek(0)
        
        filename = self.generate_filename(f'wlk_semester{semester}_{year}', 'xlsx')
        return output.getvalue(), filename
    
    def get_summary(self, employees):
        """
        Get summary data untuk regulatory reporting.
        
        Args:
            employees: hr.employee recordset
            
        Returns:
            dict: Summary statistics
        """
        summary = {
            'total_employees': len(employees),
            'gender': {'male': 0, 'female': 0},
            'marital': {},
            'education': {},
            'bpjs': {
                'kesehatan': {'registered': 0, 'not_registered': 0},
                'ketenagakerjaan': {'registered': 0, 'not_registered': 0},
            },
            'npwp': {'has_npwp': 0, 'no_npwp': 0},
        }
        
        for emp in employees:
            # Gender
            gender = self.get_field_value(emp, 'gender')
            if gender == 'male':
                summary['gender']['male'] += 1
            else:
                summary['gender']['female'] += 1
            
            # Marital
            marital = self.get_field_value(emp, 'status_kawin') or 'unknown'
            summary['marital'][marital] = summary['marital'].get(marital, 0) + 1
            
            # Education
            if hasattr(emp, 'education_ids') and emp.education_ids:
                edu = self.get_formatted_field_value(emp.education_ids[0], 'certificate')
                summary['education'][edu] = summary['education'].get(edu, 0) + 1
            
            # BPJS
            has_bpjs_kes = False
            has_bpjs_tk = False
            
            if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
                for bpjs in emp.bpjs_ids:
                    bpjs_type = self.get_field_value(bpjs, 'bpjs_type')
                    if bpjs_type == 'kesehatan':
                        has_bpjs_kes = True
                    elif bpjs_type == 'ketenagakerjaan':
                        has_bpjs_tk = True
            
            if has_bpjs_kes:
                summary['bpjs']['kesehatan']['registered'] += 1
            else:
                summary['bpjs']['kesehatan']['not_registered'] += 1
            
            if has_bpjs_tk:
                summary['bpjs']['ketenagakerjaan']['registered'] += 1
            else:
                summary['bpjs']['ketenagakerjaan']['not_registered'] += 1
            
            # NPWP
            has_npwp = False
            if hasattr(emp, 'payroll_id') and emp.payroll_id:
                npwp = self.get_field_value(emp.payroll_id, 'npwp')
                has_npwp = bool(npwp)
            
            if has_npwp:
                summary['npwp']['has_npwp'] += 1
            else:
                summary['npwp']['no_npwp'] += 1
        
        return summary
