# -*- coding: utf-8 -*-
"""
Model Analytics untuk Dashboard Employee Export

Model ini menyediakan data analitik untuk dashboard OWL.
Mengumpulkan statistik karyawan untuk visualisasi chart.
"""

import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class HrEmployeeAnalytics(models.TransientModel):
    """
    Model transient untuk analytics dashboard karyawan.
    
    Menyediakan method untuk mengambil data statistik
    yang ditampilkan di dashboard.
    """
    
    _name = 'hr.employee.analytics'
    _description = 'Employee Analytics Dashboard'
    
    # ===== Field Definitions =====
    
    department_id = fields.Many2one(
        'hr.department',
        string='Filter Departemen',
        help='Filter analitik berdasarkan departemen',
    )
    
    date_from = fields.Date(
        string='Dari Tanggal',
        default=lambda self: date.today().replace(month=1, day=1),
    )
    
    date_to = fields.Date(
        string='Sampai Tanggal',
        default=fields.Date.today,
    )
    
    # ===== Main API Method =====
    
    @api.model
    def get_dashboard_data(self, department_id=False):
        """
        Method utama untuk mengambil semua data dashboard.
        
        Args:
            department_id: ID departemen untuk filter (opsional)
            
        Returns:
            dict: Data dashboard lengkap dengan KPI dan chart data
        """
        domain = [('active', 'in', [True, False])]
        if department_id:
            domain.append(('department_id', '=', department_id))
        
        employees = self.env['hr.employee'].sudo().search(domain)
        active_employees = employees.filtered(lambda e: e.active)
        inactive_employees = employees.filtered(lambda e: not e.active)
        
        today = date.today()
        first_day_of_month = today.replace(day=1)
        
        return {
            'kpi': self._get_kpi_data(employees, active_employees, inactive_employees, first_day_of_month),
            'gender': self._get_gender_data(active_employees),
            'age_groups': self._get_age_groups_data(active_employees),
            'departments': self._get_department_data(active_employees),
            'education': self._get_education_data(active_employees),
            'employment_type': self._get_employment_type_data(active_employees),
            'service_length': self._get_service_length_data(active_employees),
            'bpjs': self._get_bpjs_data(active_employees),
            'religion': self._get_religion_data(active_employees),
            'marital': self._get_marital_data(active_employees),
        }
    
    # ===== KPI Data =====
    
    def _get_kpi_data(self, employees, active_employees, inactive_employees, first_day_of_month):
        """
        Menghitung data KPI untuk dashboard.
        
        Returns:
            dict: Data KPI (total, active, inactive, avg age, avg tenure, dll)
        """
        today = date.today()
        
        # Hitung rata-rata usia
        avg_age = 0
        age_count = 0
        for emp in active_employees:
            if emp.birthday:
                age = relativedelta(today, emp.birthday).years
                avg_age += age
                age_count += 1
        avg_age = float_round(avg_age / age_count, 1) if age_count > 0 else 0
        
        # Hitung rata-rata masa kerja (tenure)
        avg_tenure = 0
        tenure_count = 0
        for emp in active_employees:
            join_date = self._get_join_date(emp)
            if join_date:
                tenure = relativedelta(today, join_date)
                avg_tenure += tenure.years + (tenure.months / 12)
                tenure_count += 1
        avg_tenure = float_round(avg_tenure / tenure_count, 1) if tenure_count > 0 else 0
        
        # Hitung new hires bulan ini
        new_hires = 0
        for emp in active_employees:
            join_date = self._get_join_date(emp)
            if join_date and join_date >= first_day_of_month:
                new_hires += 1
        
        # Hitung resigns bulan ini (dari departure_date di contract atau field resign_date)
        resigns = 0
        for emp in inactive_employees:
            resign_date = getattr(emp, 'departure_date', False) or getattr(emp, 'x_resign_date', False)
            if resign_date and resign_date >= first_day_of_month:
                resigns += 1
        
        # Hitung gender
        male_count = len(active_employees.filtered(lambda e: e.gender == 'male'))
        female_count = len(active_employees.filtered(lambda e: e.gender == 'female'))
        
        return {
            'totalEmployees': len(employees),
            'activeEmployees': len(active_employees),
            'inactiveEmployees': len(inactive_employees),
            'avgAge': avg_age,
            'avgTenure': avg_tenure,
            'newHiresThisMonth': new_hires,
            'resignsThisMonth': resigns,
            'maleCount': male_count,
            'femaleCount': female_count,
        }
    
    def _get_join_date(self, employee):
        """
        Mendapatkan tanggal masuk karyawan dari berbagai sumber.
        
        Args:
            employee: hr.employee record
            
        Returns:
            date: Tanggal masuk atau False
        """
        # Coba dari custom field yhc_employee
        if hasattr(employee, 'x_join_date') and employee.x_join_date:
            return employee.x_join_date
        
        # Coba dari income_start (yhc_employee field)
        if hasattr(employee, 'income_start') and employee.income_start:
            return employee.income_start
        
        # Coba dari contract (jika hr_contract terinstall)
        if hasattr(employee, 'contract_id') and employee.contract_id:
            if hasattr(employee.contract_id, 'date_start') and employee.contract_id.date_start:
                return employee.contract_id.date_start
        
        # Coba dari first_contract_date
        if hasattr(employee, 'first_contract_date') and employee.first_contract_date:
            return employee.first_contract_date
        
        return False
    
    # ===== Chart Data Methods =====
    
    def _get_gender_data(self, employees):
        """
        Menghitung distribusi gender.
        
        Returns:
            dict: {'male': count, 'female': count}
        """
        male = len(employees.filtered(lambda e: e.gender == 'male'))
        female = len(employees.filtered(lambda e: e.gender == 'female'))
        other = len(employees) - male - female
        
        return {
            'male': male,
            'female': female,
            'other': other if other > 0 else 0,
        }
    
    def _get_age_groups_data(self, employees):
        """
        Menghitung distribusi kelompok usia.
        
        Returns:
            dict: {'< 25': count, '25-34': count, ...}
        """
        today = date.today()
        age_groups = {
            '< 25': 0,
            '25-34': 0,
            '35-44': 0,
            '45-54': 0,
            '55+': 0,
        }
        
        for emp in employees:
            if not emp.birthday:
                continue
                
            age = relativedelta(today, emp.birthday).years
            
            if age < 25:
                age_groups['< 25'] += 1
            elif age < 35:
                age_groups['25-34'] += 1
            elif age < 45:
                age_groups['35-44'] += 1
            elif age < 55:
                age_groups['45-54'] += 1
            else:
                age_groups['55+'] += 1
        
        return age_groups
    
    def _get_department_data(self, employees):
        """
        Menghitung distribusi per departemen.
        
        Returns:
            dict: {'Dept Name': count, ...}
        """
        department_data = {}
        
        for emp in employees:
            dept_name = emp.department_id.name if emp.department_id else 'Tidak Ada Departemen'
            department_data[dept_name] = department_data.get(dept_name, 0) + 1
        
        return department_data
    
    def _get_education_data(self, employees):
        """
        Menghitung distribusi tingkat pendidikan.
        
        Returns:
            dict: {'S1': count, 'S2': count, ...}
        """
        education_data = {}
        
        # Mapping untuk education level dari yhc_employee
        education_map = {
            'sd': 'SD',
            'smp': 'SMP',
            'sma': 'SMA/SMK',
            'smk': 'SMA/SMK',
            'd1': 'D1',
            'd2': 'D2',
            'd3': 'D3',
            'd4': 'D4',
            's1': 'S1',
            's2': 'S2',
            's3': 'S3',
            'other': 'Lainnya',
        }
        
        for emp in employees:
            # Coba dari custom field yhc_employee
            education = getattr(emp, 'x_education_level', False) or \
                        getattr(emp, 'certificate', False) or 'other'
            
            if isinstance(education, str):
                edu_label = education_map.get(education.lower(), education.upper())
            else:
                edu_label = 'Tidak Diketahui'
            
            education_data[edu_label] = education_data.get(edu_label, 0) + 1
        
        return education_data
    
    def _get_employment_type_data(self, employees):
        """
        Menghitung distribusi tipe karyawan.
        
        Returns:
            dict: {'Tetap': count, 'Kontrak': count, ...}
        """
        employment_data = {}
        
        type_map = {
            'permanent': 'Tetap',
            'contract': 'Kontrak',
            'probation': 'Probation',
            'intern': 'Magang',
            'freelance': 'Freelance',
            'outsource': 'Outsource',
        }
        
        for emp in employees:
            # Coba dari custom field atau employee_type
            emp_type = getattr(emp, 'x_employment_type', False) or \
                       getattr(emp, 'employee_type', False) or 'employee'
            
            if isinstance(emp_type, str):
                type_label = type_map.get(emp_type.lower(), emp_type.title())
            else:
                type_label = 'Karyawan'
            
            employment_data[type_label] = employment_data.get(type_label, 0) + 1
        
        return employment_data
    
    def _get_service_length_data(self, employees):
        """
        Menghitung distribusi masa kerja.
        
        Returns:
            dict: {'< 1 Tahun': count, '1-3 Tahun': count, ...}
        """
        today = date.today()
        service_data = {
            '< 1 Tahun': 0,
            '1-3 Tahun': 0,
            '3-5 Tahun': 0,
            '5-10 Tahun': 0,
            '> 10 Tahun': 0,
        }
        
        for emp in employees:
            join_date = self._get_join_date(emp)
            if not join_date:
                continue
            
            tenure = relativedelta(today, join_date)
            years = tenure.years + (tenure.months / 12)
            
            if years < 1:
                service_data['< 1 Tahun'] += 1
            elif years < 3:
                service_data['1-3 Tahun'] += 1
            elif years < 5:
                service_data['3-5 Tahun'] += 1
            elif years < 10:
                service_data['5-10 Tahun'] += 1
            else:
                service_data['> 10 Tahun'] += 1
        
        return service_data
    
    def _get_bpjs_data(self, employees):
        """
        Menghitung status kepesertaan BPJS.
        
        Returns:
            dict: {
                'kesehatan': {'registered': count, 'not_registered': count},
                'ketenagakerjaan': {'registered': count, 'not_registered': count}
            }
        """
        bpjs_kes_registered = 0
        bpjs_kes_not_registered = 0
        bpjs_tk_registered = 0
        bpjs_tk_not_registered = 0
        
        for emp in employees:
            # BPJS Kesehatan
            bpjs_kes = getattr(emp, 'x_bpjs_kesehatan', False) or \
                       getattr(emp, 'bpjs_kesehatan', False)
            if bpjs_kes:
                bpjs_kes_registered += 1
            else:
                bpjs_kes_not_registered += 1
            
            # BPJS Ketenagakerjaan
            bpjs_tk = getattr(emp, 'x_bpjs_ketenagakerjaan', False) or \
                      getattr(emp, 'bpjs_ketenagakerjaan', False)
            if bpjs_tk:
                bpjs_tk_registered += 1
            else:
                bpjs_tk_not_registered += 1
        
        return {
            'kesehatan': {
                'registered': bpjs_kes_registered,
                'not_registered': bpjs_kes_not_registered,
            },
            'ketenagakerjaan': {
                'registered': bpjs_tk_registered,
                'not_registered': bpjs_tk_not_registered,
            },
        }
    
    def _get_religion_data(self, employees):
        """
        Menghitung distribusi agama.
        
        Returns:
            dict: {'Islam': count, 'Kristen': count, ...}
        """
        religion_data = {}
        
        religion_map = {
            'islam': 'Islam',
            'muslim': 'Islam',
            'christian': 'Kristen',
            'kristen': 'Kristen',
            'protestant': 'Protestan',
            'protestan': 'Protestan',
            'catholic': 'Katolik',
            'katolik': 'Katolik',
            'hindu': 'Hindu',
            'buddha': 'Buddha',
            'buddhist': 'Buddha',
            'confucian': 'Konghucu',
            'konghucu': 'Konghucu',
            'other': 'Lainnya',
        }
        
        for emp in employees:
            religion = getattr(emp, 'x_religion', False) or \
                       getattr(emp, 'religion', False) or 'other'
            
            if isinstance(religion, str):
                religion_label = religion_map.get(religion.lower(), religion.title())
            else:
                religion_label = 'Tidak Diketahui'
            
            religion_data[religion_label] = religion_data.get(religion_label, 0) + 1
        
        return religion_data
    
    def _get_marital_data(self, employees):
        """
        Menghitung distribusi status pernikahan.
        
        Returns:
            dict: {'Menikah': count, 'Belum Menikah': count, ...}
        """
        marital_data = {}
        
        marital_map = {
            'single': 'Belum Menikah',
            'married': 'Menikah',
            'cohabitant': 'Kumpul Kebo',
            'widower': 'Duda/Janda',
            'divorced': 'Cerai',
        }
        
        for emp in employees:
            marital = emp.marital or 'single'
            marital_label = marital_map.get(marital, marital.title())
            marital_data[marital_label] = marital_data.get(marital_label, 0) + 1
        
        return marital_data
    
    # ===== Export Analytics =====
    
    @api.model
    def get_export_analytics(self, date_from=False, date_to=False):
        """
        Mendapatkan analytics untuk export history.
        
        Args:
            date_from: Tanggal mulai
            date_to: Tanggal akhir
            
        Returns:
            dict: Data analytics export
        """
        domain = []
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        configs = self.env['hr.employee.export.config'].sudo().search(domain)
        
        # Group by format
        format_data = {}
        for config in configs:
            fmt = config.export_format.upper() if config.export_format else 'UNKNOWN'
            format_data[fmt] = format_data.get(fmt, 0) + 1
        
        # Group by user
        user_data = {}
        for config in configs:
            user_name = config.create_uid.name if config.create_uid else 'System'
            user_data[user_name] = user_data.get(user_name, 0) + 1
        
        return {
            'total_exports': len(configs),
            'by_format': format_data,
            'by_user': user_data,
        }
