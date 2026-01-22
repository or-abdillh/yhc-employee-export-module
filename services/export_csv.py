# -*- coding: utf-8 -*-
"""
Export Service CSV untuk yhc_employee_export.

Service ini menangani export data karyawan ke format CSV
dengan fitur UTF-8 BOM, configurable delimiter, dan flattened data.
"""

import csv
from io import StringIO, BytesIO
from datetime import datetime, date
import logging

from .export_base import EmployeeExportBase, FIELD_MAPPINGS

_logger = logging.getLogger(__name__)


class EmployeeExportCsv(EmployeeExportBase):
    """
    Service untuk export data karyawan ke format CSV.
    
    Features:
    - UTF-8 encoding dengan BOM untuk kompatibilitas Excel
    - Configurable delimiter (comma, semicolon, tab)
    - Flattened data structure
    - Quoted fields untuk handle koma dalam value
    """
    
    def __init__(self, env):
        """Initialize CSV export service."""
        super().__init__(env)
        self.delimiter = ','
        self.quotechar = '"'
        self.quoting = csv.QUOTE_MINIMAL
    
    def export(self, employees, categories=None, config=None, delimiter=','):
        """
        Export data karyawan ke format CSV.
        
        Args:
            employees: hr.employee recordset
            categories (list): List kategori yang akan di-export
            config: hr.employee.export.config (optional)
            delimiter (str): Delimiter character (',', ';', '\t')
            
        Returns:
            tuple: (bytes, filename)
        """
        self.validate_employees(employees)
        
        if categories is None:
            categories = ['identity', 'employment']
        
        self.delimiter = delimiter
        
        # Build headers and data
        headers = self._build_headers(categories)
        rows = self._build_rows(employees, categories)
        
        # Write CSV
        output = StringIO()
        writer = csv.writer(
            output,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            quoting=self.quoting
        )
        
        # Write header row
        writer.writerow(headers)
        
        # Write data rows
        for row in rows:
            writer.writerow(row)
        
        # Convert to bytes with UTF-8 BOM
        csv_content = output.getvalue()
        # Add BOM for Excel compatibility
        csv_bytes = b'\xef\xbb\xbf' + csv_content.encode('utf-8')
        
        filename = self.generate_filename('export_karyawan', 'csv')
        
        return csv_bytes, filename
    
    def _build_headers(self, categories):
        """
        Build header row berdasarkan kategori yang dipilih.
        
        Args:
            categories (list): List kategori
            
        Returns:
            list: Header columns
        """
        headers = ['No', 'NRP', 'Nama Lengkap']
        
        # Mapping kategori ke header tambahan
        category_headers = {
            'identity': [
                'NIK', 'No. KK', 'Tempat Lahir', 'Tanggal Lahir', 'Usia',
                'Jenis Kelamin', 'Agama', 'Gol. Darah', 'Status Nikah', 'Alamat KTP'
            ],
            'employment': [
                'Unit Kerja', 'Jabatan', 'Area Kerja', 'Golongan', 'Grade',
                'Tipe Pegawai', 'Jenis Pegawai', 'Status', 'Tgl Masuk', 'Masa Kerja'
            ],
            'family': [
                'Nama Pasangan', 'NIK Pasangan', 'Tgl Lahir Pasangan',
                'Jumlah Anak', 'Jml Anggota Keluarga'
            ],
            'bpjs': [
                'No. BPJS Kesehatan', 'No. BPJS TK', 'Faskes TK1', 'Kelas BPJS'
            ],
            'education': [
                'Pendidikan Terakhir', 'Institusi', 'Jurusan', 'Tahun Lulus'
            ],
            'payroll': [
                'Nama Bank', 'No. Rekening', 'NPWP', 'EFIN'
            ],
            'training': [
                'Jumlah Pelatihan'
            ],
            'reward_punishment': [
                'Jumlah Reward', 'Jumlah Punishment'
            ],
        }
        
        for cat in categories:
            if cat in category_headers:
                headers.extend(category_headers[cat])
        
        return headers
    
    def _build_rows(self, employees, categories):
        """
        Build data rows untuk semua karyawan.
        
        Args:
            employees: hr.employee recordset
            categories (list): List kategori
            
        Returns:
            list: List of row data
        """
        rows = []
        
        for idx, emp in enumerate(employees, 1):
            row = self._build_employee_row(emp, idx, categories)
            rows.append(row)
        
        return rows
    
    def _build_employee_row(self, emp, idx, categories):
        """
        Build single row untuk satu karyawan.
        
        Args:
            emp: hr.employee record
            idx (int): Nomor urut
            categories (list): List kategori
            
        Returns:
            list: Row data
        """
        row = [
            idx,
            self.get_formatted_field_value(emp, 'nrp'),
            self.get_formatted_field_value(emp, 'name'),
        ]
        
        if 'identity' in categories:
            row.extend(self._get_identity_data(emp))
        
        if 'employment' in categories:
            row.extend(self._get_employment_data(emp))
        
        if 'family' in categories:
            row.extend(self._get_family_data(emp))
        
        if 'bpjs' in categories:
            row.extend(self._get_bpjs_data(emp))
        
        if 'education' in categories:
            row.extend(self._get_education_data(emp))
        
        if 'payroll' in categories:
            row.extend(self._get_payroll_data(emp))
        
        if 'training' in categories:
            row.extend(self._get_training_data(emp))
        
        if 'reward_punishment' in categories:
            row.extend(self._get_reward_punishment_data(emp))
        
        return row
    
    def _get_identity_data(self, emp):
        """Get identity data for CSV row."""
        birthday = self.get_field_value(emp, 'birthday')
        birthday_str = birthday.strftime('%d/%m/%Y') if birthday else self.empty_value
        
        return [
            self.get_formatted_field_value(emp, 'nik'),
            self.get_formatted_field_value(emp, 'no_kk'),
            self.get_formatted_field_value(emp, 'place_of_birth'),
            birthday_str,
            self.get_formatted_field_value(emp, 'age'),
            self.get_selection_label(emp, 'gender'),
            self.get_selection_label(emp, 'religion'),
            self.get_formatted_field_value(emp, 'blood_type'),
            self.get_formatted_field_value(emp, 'status_kawin'),
            self.get_formatted_field_value(emp, 'alamat_ktp'),
        ]
    
    def _get_employment_data(self, emp):
        """Get employment data for CSV row."""
        first_contract = self.get_field_value(emp, 'first_contract_date')
        tgl_masuk = first_contract.strftime('%d/%m/%Y') if first_contract else self.empty_value
        
        service_length = self.get_field_value(emp, 'service_length')
        masa_kerja = self._format_service_length(service_length, with_unit=True) if service_length else self.empty_value
        
        return [
            self.get_formatted_field_value(emp, 'department_id.name'),
            self.get_formatted_field_value(emp, 'job_id.name'),
            self.get_formatted_field_value(emp, 'area_kerja_id.name'),
            self.get_formatted_field_value(emp, 'golongan_id.name'),
            self.get_formatted_field_value(emp, 'grade_id.name'),
            self.get_formatted_field_value(emp, 'employee_type_id.name'),
            self.get_formatted_field_value(emp, 'employee_category_id.name'),
            self.get_formatted_field_value(emp, 'employment_status'),
            tgl_masuk,
            masa_kerja,
        ]
    
    def _get_family_data(self, emp):
        """Get family data for CSV row."""
        spouse_birthday = self.get_field_value(emp, 'spouse_birthday')
        spouse_birthday_str = spouse_birthday.strftime('%d/%m/%Y') if spouse_birthday else self.empty_value
        
        child_count = len(emp.child_ids) if hasattr(emp, 'child_ids') else 0
        
        return [
            self.get_formatted_field_value(emp, 'spouse_name'),
            self.get_formatted_field_value(emp, 'spouse_nik'),
            spouse_birthday_str,
            child_count,
            self.get_formatted_field_value(emp, 'jlh_anggota_keluarga'),
        ]
    
    def _get_bpjs_data(self, emp):
        """Get BPJS data for CSV row (flattened)."""
        bpjs_kesehatan = self.empty_value
        bpjs_tk = self.empty_value
        faskes = self.empty_value
        kelas = self.empty_value
        
        if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
            for bpjs in emp.bpjs_ids:
                bpjs_type = self.get_field_value(bpjs, 'bpjs_type')
                if bpjs_type == 'kesehatan':
                    bpjs_kesehatan = self.get_formatted_field_value(bpjs, 'number')
                    faskes = self.get_formatted_field_value(bpjs, 'faskes_tk1')
                    kelas = self.get_formatted_field_value(bpjs, 'kelas')
                elif bpjs_type == 'ketenagakerjaan':
                    bpjs_tk = self.get_formatted_field_value(bpjs, 'number')
        
        return [bpjs_kesehatan, bpjs_tk, faskes, kelas]
    
    def _get_education_data(self, emp):
        """Get education data for CSV row (latest education)."""
        pendidikan = self.empty_value
        institusi = self.empty_value
        jurusan = self.empty_value
        tahun_lulus = self.empty_value
        
        if hasattr(emp, 'education_ids') and emp.education_ids:
            # Get latest education (assuming ordered by date_end desc)
            latest_edu = emp.education_ids[0] if emp.education_ids else None
            
            if latest_edu:
                pendidikan = self.get_formatted_field_value(latest_edu, 'certificate')
                institusi = self.get_formatted_field_value(latest_edu, 'study_school')
                jurusan = self.get_formatted_field_value(latest_edu, 'major')
                
                date_end = self.get_field_value(latest_edu, 'date_end')
                tahun_lulus = date_end.year if date_end else self.empty_value
        
        return [pendidikan, institusi, jurusan, tahun_lulus]
    
    def _get_payroll_data(self, emp):
        """Get payroll data for CSV row."""
        payroll = self.get_field_value(emp, 'payroll_id')
        
        if payroll:
            return [
                self.get_formatted_field_value(payroll, 'bank_name'),
                self.get_formatted_field_value(payroll, 'bank_account'),
                self.get_formatted_field_value(payroll, 'npwp'),
                self.get_formatted_field_value(payroll, 'efin'),
            ]
        
        return [self.empty_value] * 4
    
    def _get_training_data(self, emp):
        """Get training data summary for CSV row."""
        training_count = 0
        
        if hasattr(emp, 'training_certificate_ids') and emp.training_certificate_ids:
            training_count = len(emp.training_certificate_ids)
        
        return [training_count]
    
    def _get_reward_punishment_data(self, emp):
        """Get reward/punishment data summary for CSV row."""
        reward_count = 0
        punishment_count = 0
        
        if hasattr(emp, 'reward_punishment_ids') and emp.reward_punishment_ids:
            for rp in emp.reward_punishment_ids:
                rp_type = self.get_field_value(rp, 'type')
                if rp_type == 'reward':
                    reward_count += 1
                elif rp_type == 'punishment':
                    punishment_count += 1
        
        return [reward_count, punishment_count]
    
    def export_detailed(self, employees, category, config=None, delimiter=','):
        """
        Export data detail untuk satu kategori (untuk data one-to-many).
        
        Ini berguna untuk export data seperti anak, BPJS, pendidikan, dll
        dalam format detail (satu baris per record).
        
        Args:
            employees: hr.employee recordset
            category (str): Kategori yang akan di-export
            config: hr.employee.export.config (optional)
            delimiter (str): Delimiter character
            
        Returns:
            tuple: (bytes, filename)
        """
        self.validate_employees(employees)
        self.delimiter = delimiter
        
        output = StringIO()
        writer = csv.writer(
            output,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            quoting=self.quoting
        )
        
        if category == 'bpjs':
            rows = self._export_bpjs_detailed(employees, writer)
        elif category == 'education':
            rows = self._export_education_detailed(employees, writer)
        elif category == 'family':
            rows = self._export_children_detailed(employees, writer)
        elif category == 'training':
            rows = self._export_training_detailed(employees, writer)
        elif category == 'reward_punishment':
            rows = self._export_rp_detailed(employees, writer)
        else:
            # Fallback to standard export
            return self.export(employees, [category], config, delimiter)
        
        # Convert to bytes with UTF-8 BOM
        csv_content = output.getvalue()
        csv_bytes = b'\xef\xbb\xbf' + csv_content.encode('utf-8')
        
        filename = self.generate_filename(f'export_{category}_detail', 'csv')
        
        return csv_bytes, filename
    
    def _export_bpjs_detailed(self, employees, writer):
        """Export BPJS data in detailed format."""
        headers = ['No', 'NRP', 'Nama Karyawan', 'NIK', 'Jenis BPJS',
                   'Nomor BPJS', 'Faskes TK1', 'Kelas']
        writer.writerow(headers)
        
        no = 1
        for emp in employees:
            if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
                for bpjs in emp.bpjs_ids:
                    row = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(emp, 'nik'),
                        self.get_formatted_field_value(bpjs, 'bpjs_type'),
                        self.get_formatted_field_value(bpjs, 'number'),
                        self.get_formatted_field_value(bpjs, 'faskes_tk1'),
                        self.get_formatted_field_value(bpjs, 'kelas'),
                    ]
                    writer.writerow(row)
                    no += 1
    
    def _export_education_detailed(self, employees, writer):
        """Export education data in detailed format."""
        headers = ['No', 'NRP', 'Nama Karyawan', 'Jenjang', 'Institusi',
                   'Jurusan', 'Tahun Masuk', 'Tahun Lulus']
        writer.writerow(headers)
        
        no = 1
        for emp in employees:
            if hasattr(emp, 'education_ids') and emp.education_ids:
                for edu in emp.education_ids:
                    date_start = self.get_field_value(edu, 'date_start')
                    date_end = self.get_field_value(edu, 'date_end')
                    
                    row = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(edu, 'certificate'),
                        self.get_formatted_field_value(edu, 'study_school'),
                        self.get_formatted_field_value(edu, 'major'),
                        date_start.year if date_start else self.empty_value,
                        date_end.year if date_end else self.empty_value,
                    ]
                    writer.writerow(row)
                    no += 1
    
    def _export_children_detailed(self, employees, writer):
        """Export children data in detailed format."""
        headers = ['No', 'NRP', 'Nama Karyawan', 'Nama Anak', 'Jenis Kelamin',
                   'Tanggal Lahir', 'Usia']
        writer.writerow(headers)
        
        no = 1
        for emp in employees:
            if hasattr(emp, 'child_ids') and emp.child_ids:
                for child in emp.child_ids:
                    birth_date = self.get_field_value(child, 'birth_date')
                    birth_str = birth_date.strftime('%d/%m/%Y') if birth_date else self.empty_value
                    
                    row = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(child, 'name'),
                        self.get_selection_label(child, 'gender') if hasattr(child, 'gender') else self.empty_value,
                        birth_str,
                        self.get_formatted_field_value(child, 'age') if hasattr(child, 'age') else self.empty_value,
                    ]
                    writer.writerow(row)
                    no += 1
    
    def _export_training_detailed(self, employees, writer):
        """Export training data in detailed format."""
        headers = ['No', 'NRP', 'Nama Karyawan', 'Nama Pelatihan', 'Jenis',
                   'Metode', 'Tgl Mulai', 'Tgl Selesai']
        writer.writerow(headers)
        
        no = 1
        for emp in employees:
            if hasattr(emp, 'training_certificate_ids') and emp.training_certificate_ids:
                for training in emp.training_certificate_ids:
                    date_start = self.get_field_value(training, 'date_start')
                    date_end = self.get_field_value(training, 'date_end')
                    
                    row = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        self.get_formatted_field_value(training, 'name'),
                        self.get_formatted_field_value(training, 'jenis_pelatihan'),
                        self.get_formatted_field_value(training, 'metode'),
                        date_start.strftime('%d/%m/%Y') if date_start else self.empty_value,
                        date_end.strftime('%d/%m/%Y') if date_end else self.empty_value,
                    ]
                    writer.writerow(row)
                    no += 1
    
    def _export_rp_detailed(self, employees, writer):
        """Export reward/punishment data in detailed format."""
        headers = ['No', 'NRP', 'Nama Karyawan', 'Tipe', 'Kategori',
                   'Tanggal', 'Keterangan']
        writer.writerow(headers)
        
        no = 1
        for emp in employees:
            if hasattr(emp, 'reward_punishment_ids') and emp.reward_punishment_ids:
                for rp in emp.reward_punishment_ids:
                    rp_date = self.get_field_value(rp, 'date')
                    rp_type = self.get_field_value(rp, 'type')
                    
                    # Get type label
                    type_label = 'Reward' if rp_type == 'reward' else ('Punishment' if rp_type == 'punishment' else self.empty_value)
                    
                    # Get category based on type
                    category = self.empty_value
                    if rp_type == 'reward':
                        reward_cat = self.get_field_value(rp, 'reward_category')
                        if reward_cat:
                            category_map = {
                                'gathering': 'Gathering',
                                'program_sekolah': 'Program Sekolah',
                                'program_yayasan': 'Program Yayasan',
                            }
                            category = category_map.get(reward_cat, reward_cat)
                    elif rp_type == 'punishment':
                        punishment_cat = self.get_field_value(rp, 'punishment_category')
                        if punishment_cat:
                            category_map = {
                                'st1': 'Surat Teguran 1',
                                'st2': 'Surat Teguran 2',
                                'st3': 'Surat Teguran 3',
                                'sp1': 'Surat Peringatan 1',
                                'sp2': 'Surat Peringatan 2',
                                'sp3': 'Surat Peringatan 3',
                            }
                            category = category_map.get(punishment_cat, punishment_cat)
                    
                    row = [
                        no,
                        self.get_formatted_field_value(emp, 'nrp'),
                        self.get_formatted_field_value(emp, 'name'),
                        type_label,
                        category,
                        rp_date.strftime('%d/%m/%Y') if rp_date else self.empty_value,
                        self.get_formatted_field_value(rp, 'description'),
                    ]
                    writer.writerow(row)
                    no += 1
