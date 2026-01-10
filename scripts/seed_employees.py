# -*- coding: utf-8 -*-
"""
Script untuk generate data dummy karyawan.

Cara menjalankan:
1. Masuk ke direktori Odoo
2. Jalankan: python odoo-bin shell -d <database_name>
3. Di shell, jalankan:
   exec(open('/path/to/yhc_employee_export/scripts/seed_employees.py').read())

Atau jalankan langsung dari terminal:
   python odoo-bin shell -d <database_name> < /path/to/seed_employees.py
"""

import random
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# ===== KONFIGURASI =====
TOTAL_EMPLOYEES = 50  # Jumlah karyawan yang akan dibuat
COMPANY_ID = 1  # ID perusahaan (sesuaikan dengan database)

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
AGAMA_WEIGHTS = [0.87, 0.07, 0.03, 0.02, 0.005, 0.005]  # Distribusi realistis

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
    'Jl. Anggrek', 'Jl. Dahlia', 'Jl. Cempaka', 'Jl. Flamboyan',
]

NAMA_BANK = ['BCA', 'Mandiri', 'BNI', 'BRI', 'CIMB Niaga', 'Danamon', 'Permata']

# ===== HELPER FUNCTIONS =====

def random_choice_weighted(choices, weights):
    """Pilih random dengan bobot."""
    return random.choices(choices, weights=weights, k=1)[0]

def generate_nik():
    """Generate NIK 16 digit."""
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])

def generate_npwp():
    """Generate NPWP format XX.XXX.XXX.X-XXX.XXX."""
    digits = ''.join([str(random.randint(0, 9)) for _ in range(15)])
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}.{digits[8]}-{digits[9:12]}.{digits[12:15]}"

def generate_phone():
    """Generate nomor HP Indonesia."""
    prefix = random.choice(['081', '082', '083', '085', '087', '088', '089'])
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"{prefix}{suffix}"

def generate_email(name):
    """Generate email dari nama."""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'email.com']
    clean_name = name.lower().replace(' ', '.').replace("'", "")
    return f"{clean_name}{random.randint(1, 99)}@{random.choice(domains)}"

def generate_bank_account():
    """Generate nomor rekening bank."""
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def random_date_between(start_date, end_date):
    """Generate tanggal random antara dua tanggal."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def get_or_create_department(env, name):
    """Get atau create department."""
    dept = env['hr.department'].search([('name', '=', name)], limit=1)
    if not dept:
        dept = env['hr.department'].create({'name': name})
    return dept

def get_or_create_job(env, name, dept_id=None):
    """Get atau create job position."""
    domain = [('name', '=', name)]
    if dept_id:
        domain.append(('department_id', '=', dept_id))
    job = env['hr.job'].search(domain, limit=1)
    if not job:
        vals = {'name': name}
        if dept_id:
            vals['department_id'] = dept_id
        job = env['hr.job'].create(vals)
    return job

# ===== MAIN SEEDER =====

def seed_employees(env, count=TOTAL_EMPLOYEES):
    """
    Generate data dummy karyawan.
    
    Args:
        env: Odoo environment
        count: Jumlah karyawan yang akan dibuat
    """
    print(f"\n{'='*60}")
    print(f"  SEEDER: Membuat {count} data dummy karyawan")
    print(f"{'='*60}\n")
    
    Employee = env['hr.employee']
    
    # Setup departments
    departments = {
        'IT': get_or_create_department(env, 'IT'),
        'HRD': get_or_create_department(env, 'Human Resources'),
        'Finance': get_or_create_department(env, 'Finance'),
        'Marketing': get_or_create_department(env, 'Marketing'),
        'Operations': get_or_create_department(env, 'Operations'),
        'Sales': get_or_create_department(env, 'Sales'),
        'R&D': get_or_create_department(env, 'Research & Development'),
    }
    
    # Setup jobs per department
    jobs = {
        'IT': ['Software Engineer', 'System Analyst', 'IT Support', 'DevOps Engineer', 'Data Analyst'],
        'HRD': ['HR Manager', 'HR Staff', 'Recruiter', 'Training Specialist'],
        'Finance': ['Accountant', 'Finance Manager', 'Tax Specialist', 'Cashier'],
        'Marketing': ['Marketing Manager', 'Digital Marketing', 'Content Creator', 'Brand Manager'],
        'Operations': ['Operations Manager', 'Admin Staff', 'Logistics Coordinator', 'Warehouse Staff'],
        'Sales': ['Sales Manager', 'Sales Executive', 'Account Manager', 'Business Development'],
        'R&D': ['R&D Manager', 'Product Designer', 'Quality Assurance', 'Research Analyst'],
    }
    
    job_records = {}
    for dept_key, dept in departments.items():
        job_records[dept_key] = []
        for job_name in jobs.get(dept_key, []):
            job_records[dept_key].append(get_or_create_job(env, job_name, dept.id))
    
    # Get existing related records (jika ada dari yhc_employee)
    Golongan = env['hr.employee.golongan'] if 'hr.employee.golongan' in env else None
    Grade = env['hr.employee.grade'] if 'hr.employee.grade' in env else None
    EmployeeType = env['hr.employee.type'] if 'hr.employee.type' in env else None
    
    golongan_ids = Golongan.search([]).ids if Golongan else []
    grade_ids = Grade.search([]).ids if Grade else []
    employee_type_ids = EmployeeType.search([]).ids if EmployeeType else []
    
    created_employees = []
    
    for i in range(count):
        # Determine gender
        gender = random.choice(['male', 'female'])
        
        # Generate name
        if gender == 'male':
            first_name = random.choice(NAMA_DEPAN_PRIA)
        else:
            first_name = random.choice(NAMA_DEPAN_WANITA)
        last_name = random.choice(NAMA_BELAKANG)
        full_name = f"{first_name} {last_name}"
        
        # Random department & job
        dept_key = random.choice(list(departments.keys()))
        department = departments[dept_key]
        job_list = job_records.get(dept_key, [])
        job = random.choice(job_list) if job_list else None
        
        # Generate dates
        today = date.today()
        
        # Birthday: age between 22-55
        min_birthday = today - relativedelta(years=55)
        max_birthday = today - relativedelta(years=22)
        birthday = random_date_between(min_birthday, max_birthday)
        
        # Join date: between 1-15 years ago
        min_join = today - relativedelta(years=15)
        max_join = today - relativedelta(months=1)
        first_contract_date = random_date_between(min_join, max_join)
        
        # Employee values
        vals = {
            'name': full_name,
            'gender': gender,
            'birthday': birthday,
            'marital': random_choice_weighted(STATUS_NIKAH, STATUS_NIKAH_WEIGHTS),
            'place_of_birth': random.choice(KOTA_LAHIR),
            'identification_id': generate_nik(),
            'department_id': department.id,
            'job_id': job.id if job else False,
            'work_phone': generate_phone(),
            'mobile_phone': generate_phone(),
            'work_email': generate_email(full_name),
            'private_email': generate_email(f"{first_name}{random.randint(1,99)}"),
            'private_street': f"{random.choice(ALAMAT_JALAN)} No. {random.randint(1, 200)}",
            'private_city': random.choice(KOTA_LAHIR),
            'private_zip': f"{random.randint(10000, 99999)}",
            'private_country_id': env.ref('base.id').id,  # Indonesia
            'bank_account_id': False,  # Will set below if needed
        }
        
        # Add yhc_employee specific fields if available
        if hasattr(Employee, 'religion'):
            vals['religion'] = random_choice_weighted(AGAMA, AGAMA_WEIGHTS)
        
        if hasattr(Employee, 'blood_type'):
            vals['blood_type'] = random.choice(GOLONGAN_DARAH)
        
        if hasattr(Employee, 'education_level'):
            vals['education_level'] = random_choice_weighted(PENDIDIKAN, PENDIDIKAN_WEIGHTS)
        
        if hasattr(Employee, 'first_contract_date'):
            vals['first_contract_date'] = first_contract_date
        
        if hasattr(Employee, 'npwp'):
            vals['npwp'] = generate_npwp()
        
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
        
        try:
            employee = Employee.create(vals)
            created_employees.append(employee)
            print(f"  ✓ [{i+1}/{count}] Created: {full_name} ({department.name})")
        except Exception as e:
            print(f"  ✗ [{i+1}/{count}] Failed: {full_name} - {str(e)}")
    
    # Commit transaction
    env.cr.commit()
    
    print(f"\n{'='*60}")
    print(f"  ✅ Selesai! {len(created_employees)} karyawan berhasil dibuat.")
    print(f"{'='*60}\n")
    
    return created_employees

# ===== EXECUTE =====
if __name__ == '__main__' or 'env' in dir():
    # Jika dijalankan dari Odoo shell
    if 'env' in dir():
        seed_employees(env)
    else:
        print("Script ini harus dijalankan dari Odoo shell.")
        print("Gunakan: python odoo-bin shell -d <database_name>")
