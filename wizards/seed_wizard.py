# -*- coding: utf-8 -*-
"""
Wizard untuk generate data dummy karyawan.
Dapat diakses melalui menu di Odoo.
"""

import random
import logging
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrEmployeeSeedWizard(models.TransientModel):
    """Wizard untuk generate data dummy karyawan."""
    
    _name = 'hr.employee.seed.wizard'
    _description = 'Generate Data Dummy Karyawan'
    
    count = fields.Integer(
        string='Jumlah Karyawan',
        default=50,
        required=True,
        help='Jumlah karyawan dummy yang akan dibuat',
    )
    
    include_departments = fields.Boolean(
        string='Buat Departemen',
        default=True,
        help='Otomatis buat departemen jika belum ada',
    )
    
    include_jobs = fields.Boolean(
        string='Buat Jabatan',
        default=True,
        help='Otomatis buat jabatan jika belum ada',
    )
    
    result_message = fields.Text(
        string='Hasil',
        readonly=True,
    )
    
    state = fields.Selection([
        ('config', 'Konfigurasi'),
        ('done', 'Selesai'),
    ], default='config')
    
    # ===== DATA MASTER =====
    
    NAMA_DEPAN_PRIA = [
        'Ahmad', 'Budi', 'Cahyo', 'Dedi', 'Eko', 'Fajar', 'Gunawan', 'Hadi',
        'Irwan', 'Joko', 'Kurniawan', 'Lukman', 'Muhammad', 'Nur', 'Oki',
        'Putra', 'Rahmat', 'Sigit', 'Teguh', 'Umar', 'Wahyu', 'Yusuf', 'Zainal',
        'Agus', 'Bambang', 'Dwi', 'Hendri', 'Rizky', 'Surya', 'Taufik',
        'Arif', 'Bayu', 'Dimas', 'Fauzan', 'Gilang', 'Hanif', 'Ilham', 'Kevin',
    ]
    
    NAMA_DEPAN_WANITA = [
        'Ani', 'Bunga', 'Citra', 'Dewi', 'Eka', 'Fitri', 'Gita', 'Hana',
        'Indah', 'Julia', 'Kartika', 'Lestari', 'Maya', 'Nadia', 'Oktavia',
        'Putri', 'Ratna', 'Sari', 'Tika', 'Utami', 'Vina', 'Wulan', 'Yuni',
        'Anisa', 'Bella', 'Dian', 'Erna', 'Fika', 'Gia', 'Intan', 'Lisa',
        'Mega', 'Nia', 'Rini', 'Sinta', 'Tari', 'Vera', 'Winda', 'Yolanda',
    ]
    
    NAMA_BELAKANG = [
        'Pratama', 'Saputra', 'Wijaya', 'Kusuma', 'Hidayat', 'Nugroho', 'Santoso',
        'Wibowo', 'Setiawan', 'Suryadi', 'Permana', 'Ramadhan', 'Hakim', 'Putra',
        'Utama', 'Lestari', 'Sari', 'Dewi', 'Putri', 'Maharani', 'Purnama',
        'Syahputra', 'Firmansyah', 'Kurniawan', 'Prasetyo', 'Hartono', 'Budiman',
        'Susanto', 'Gunawan', 'Hermawan', 'Sugiarto', 'Atmaja', 'Darmawan',
    ]
    
    AGAMA = ['islam', 'kristen', 'katolik', 'hindu', 'buddha', 'konghucu']
    AGAMA_WEIGHTS = [0.87, 0.07, 0.03, 0.02, 0.005, 0.005]
    
    PENDIDIKAN = ['sma', 'd3', 's1', 's2', 's3']
    PENDIDIKAN_WEIGHTS = [0.25, 0.15, 0.50, 0.09, 0.01]
    
    STATUS_NIKAH = ['single', 'married', 'divorced', 'widowed']
    STATUS_NIKAH_WEIGHTS = [0.35, 0.55, 0.07, 0.03]
    
    GOLONGAN_DARAH = ['A', 'B', 'AB', 'O']
    
    KOTA_LAHIR = [
        'Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Semarang', 'Makassar',
        'Palembang', 'Tangerang', 'Depok', 'Bekasi', 'Bogor', 'Malang',
        'Yogyakarta', 'Solo', 'Denpasar', 'Balikpapan', 'Pontianak', 'Manado',
    ]
    
    ALAMAT_JALAN = [
        'Jl. Merdeka', 'Jl. Sudirman', 'Jl. Gatot Subroto', 'Jl. Ahmad Yani',
        'Jl. Diponegoro', 'Jl. Imam Bonjol', 'Jl. Veteran', 'Jl. Pahlawan',
        'Jl. Raya', 'Jl. Mangga', 'Jl. Melati', 'Jl. Kenanga', 'Jl. Mawar',
    ]
    
    DEPARTMENTS = {
        'IT': ['Software Engineer', 'System Analyst', 'IT Support', 'DevOps Engineer', 'Data Analyst'],
        'Human Resources': ['HR Manager', 'HR Staff', 'Recruiter', 'Training Specialist'],
        'Finance': ['Accountant', 'Finance Manager', 'Tax Specialist', 'Cashier'],
        'Marketing': ['Marketing Manager', 'Digital Marketing', 'Content Creator', 'Brand Manager'],
        'Operations': ['Operations Manager', 'Admin Staff', 'Logistics Coordinator', 'Warehouse Staff'],
        'Sales': ['Sales Manager', 'Sales Executive', 'Account Manager', 'Business Development'],
        'R&D': ['R&D Manager', 'Product Designer', 'Quality Assurance', 'Research Analyst'],
    }
    
    # ===== HELPER METHODS =====
    
    def _random_choice_weighted(self, choices, weights):
        """Pilih random dengan bobot."""
        return random.choices(choices, weights=weights, k=1)[0]
    
    def _generate_nik(self):
        """Generate NIK 16 digit."""
        return ''.join([str(random.randint(0, 9)) for _ in range(16)])
    
    def _generate_npwp(self):
        """Generate NPWP format XX.XXX.XXX.X-XXX.XXX."""
        digits = ''.join([str(random.randint(0, 9)) for _ in range(15)])
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}.{digits[8]}-{digits[9:12]}.{digits[12:15]}"
    
    def _generate_phone(self):
        """Generate nomor HP Indonesia."""
        prefix = random.choice(['081', '082', '083', '085', '087', '088', '089'])
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return f"{prefix}{suffix}"
    
    def _generate_email(self, name):
        """Generate email dari nama."""
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'email.com']
        clean_name = name.lower().replace(' ', '.').replace("'", "")
        return f"{clean_name}{random.randint(1, 99)}@{random.choice(domains)}"
    
    def _random_date_between(self, start_date, end_date):
        """Generate tanggal random antara dua tanggal."""
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        return start_date + timedelta(days=random_days)
    
    def _get_or_create_department(self, name):
        """Get atau create department."""
        Department = self.env['hr.department']
        dept = Department.search([('name', '=', name)], limit=1)
        if not dept:
            dept = Department.create({'name': name})
        return dept
    
    def _get_or_create_job(self, name, dept_id=None):
        """Get atau create job position."""
        Job = self.env['hr.job']
        domain = [('name', '=', name)]
        if dept_id:
            domain.append(('department_id', '=', dept_id))
        job = Job.search(domain, limit=1)
        if not job:
            vals = {'name': name}
            if dept_id:
                vals['department_id'] = dept_id
            job = Job.create(vals)
        return job
    
    # ===== MAIN ACTIONS =====
    
    def action_generate(self):
        """Generate data dummy karyawan."""
        self.ensure_one()
        
        if self.count < 1:
            raise UserError(_('Jumlah karyawan harus minimal 1'))
        if self.count > 500:
            raise UserError(_('Jumlah karyawan maksimal 500'))
        
        Employee = self.env['hr.employee']
        
        # Setup departments & jobs
        departments = {}
        job_records = {}
        
        if self.include_departments:
            for dept_name, jobs in self.DEPARTMENTS.items():
                dept = self._get_or_create_department(dept_name)
                departments[dept_name] = dept
                job_records[dept_name] = []
                
                if self.include_jobs:
                    for job_name in jobs:
                        job = self._get_or_create_job(job_name, dept.id)
                        job_records[dept_name].append(job)
        
        # Get existing master data (yhc_employee fields)
        golongan_ids = []
        grade_ids = []
        employee_type_ids = []
        
        if 'hr.employee.golongan' in self.env:
            golongan_ids = self.env['hr.employee.golongan'].search([]).ids
        if 'hr.employee.grade' in self.env:
            grade_ids = self.env['hr.employee.grade'].search([]).ids
        if 'hr.employee.type' in self.env:
            employee_type_ids = self.env['hr.employee.type'].search([]).ids
        
        created_count = 0
        failed_count = 0
        errors = []
        
        for i in range(self.count):
            try:
                # Determine gender
                gender = random.choice(['male', 'female'])
                
                # Generate name
                if gender == 'male':
                    first_name = random.choice(self.NAMA_DEPAN_PRIA)
                else:
                    first_name = random.choice(self.NAMA_DEPAN_WANITA)
                last_name = random.choice(self.NAMA_BELAKANG)
                full_name = f"{first_name} {last_name}"
                
                # Random department & job
                if departments:
                    dept_key = random.choice(list(departments.keys()))
                    department = departments[dept_key]
                    job_list = job_records.get(dept_key, [])
                    job = random.choice(job_list) if job_list else None
                else:
                    department = None
                    job = None
                
                # Generate dates
                today = date.today()
                min_birthday = today - relativedelta(years=55)
                max_birthday = today - relativedelta(years=22)
                birthday = self._random_date_between(min_birthday, max_birthday)
                
                min_join = today - relativedelta(years=15)
                max_join = today - relativedelta(months=1)
                first_contract_date = self._random_date_between(min_join, max_join)
                
                # Employee values
                vals = {
                    'name': full_name,
                    'gender': gender,
                    'birthday': birthday,
                    'marital': self._random_choice_weighted(self.STATUS_NIKAH, self.STATUS_NIKAH_WEIGHTS),
                    'place_of_birth': random.choice(self.KOTA_LAHIR),
                    'identification_id': self._generate_nik(),
                    'work_phone': self._generate_phone(),
                    'mobile_phone': self._generate_phone(),
                    'work_email': self._generate_email(full_name),
                    'private_street': f"{random.choice(self.ALAMAT_JALAN)} No. {random.randint(1, 200)}",
                    'private_city': random.choice(self.KOTA_LAHIR),
                    'private_zip': f"{random.randint(10000, 99999)}",
                }
                
                if department:
                    vals['department_id'] = department.id
                if job:
                    vals['job_id'] = job.id
                
                # Check Indonesia country
                try:
                    indonesia = self.env.ref('base.id')
                    vals['private_country_id'] = indonesia.id
                except:
                    pass
                
                # Add yhc_employee specific fields if available
                if hasattr(Employee, 'religion'):
                    vals['religion'] = self._random_choice_weighted(self.AGAMA, self.AGAMA_WEIGHTS)
                
                if hasattr(Employee, 'blood_type'):
                    vals['blood_type'] = random.choice(self.GOLONGAN_DARAH)
                
                if hasattr(Employee, 'education_level'):
                    vals['education_level'] = self._random_choice_weighted(self.PENDIDIKAN, self.PENDIDIKAN_WEIGHTS)
                
                if hasattr(Employee, 'first_contract_date'):
                    vals['first_contract_date'] = first_contract_date
                
                if hasattr(Employee, 'npwp'):
                    vals['npwp'] = self._generate_npwp()
                
                if hasattr(Employee, 'employee_code'):
                    vals['employee_code'] = f"EMP{str(i+1).zfill(5)}"
                
                if hasattr(Employee, 'employment_status'):
                    vals['employment_status'] = random.choice(['permanent', 'contract', 'probation'])
                
                if golongan_ids and hasattr(Employee, 'golongan_id'):
                    vals['golongan_id'] = random.choice(golongan_ids)
                
                if grade_ids and hasattr(Employee, 'grade_id'):
                    vals['grade_id'] = random.choice(grade_ids)
                
                if employee_type_ids and hasattr(Employee, 'employee_type_id'):
                    vals['employee_type_id'] = random.choice(employee_type_ids)
                
                Employee.create(vals)
                created_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append(f"#{i+1}: {str(e)}")
                _logger.warning(f"Failed to create employee #{i+1}: {e}")
        
        # Build result message
        result_lines = [
            "=" * 50,
            "HASIL GENERATE DATA DUMMY KARYAWAN",
            "=" * 50,
            "",
            f"✅ Berhasil dibuat: {created_count} karyawan",
        ]
        
        if failed_count:
            result_lines.append(f"❌ Gagal: {failed_count} karyawan")
        
        if self.include_departments:
            result_lines.append(f"📁 Departemen: {len(departments)}")
        
        if self.include_jobs:
            total_jobs = sum(len(j) for j in job_records.values())
            result_lines.append(f"💼 Jabatan: {total_jobs}")
        
        if errors[:5]:  # Show first 5 errors
            result_lines.append("")
            result_lines.append("Error (5 pertama):")
            result_lines.extend(errors[:5])
        
        result_lines.append("")
        result_lines.append("=" * 50)
        
        self.write({
            'state': 'done',
            'result_message': '\n'.join(result_lines),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_back(self):
        """Kembali ke konfigurasi."""
        self.write({
            'state': 'config',
            'result_message': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_view_employees(self):
        """Lihat daftar karyawan yang dibuat."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Karyawan'),
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'target': 'current',
        }
