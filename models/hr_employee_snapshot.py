# -*- coding: utf-8 -*-
"""
Model: hr.employee.snapshot
Snapshot data karyawan untuk laporan historis dan analitik.

Snapshot diambil pada akhir setiap bulan dan bersifat immutable.
Digunakan sebagai basis data untuk:
- Grafik historis
- Export PDF berbasis snapshot
- Laporan eksekutif
"""

import logging
from datetime import date, timedelta
from calendar import monthrange

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrEmployeeSnapshot(models.Model):
    """
    Snapshot data karyawan per bulan.
    
    Record ini bersifat immutable setelah dibuat.
    Data diambil berdasarkan kondisi karyawan pada cut-off date.
    """
    
    _name = 'hr.employee.snapshot'
    _description = 'Employee Snapshot Data'
    _order = 'snapshot_year desc, snapshot_month desc, unit_id, employee_id'
    _rec_name = 'display_name'
    
    # ===== Core Fields =====
    
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Karyawan',
        required=True,
        index=True,
        ondelete='cascade',
    )
    
    unit_id = fields.Many2one(
        comodel_name='hr.department',
        string='Unit/Departemen',
        required=True,
        index=True,
    )
    
    # ===== Employment Classification =====
    
    employment_type = fields.Selection(
        selection=[
            ('payroll', 'Payroll'),
            ('non_payroll', 'Non-Payroll'),
        ],
        string='Tipe Kepegawaian',
        required=True,
        index=True,
        help='Payroll: Karyawan dengan gaji tetap dari perusahaan\n'
             'Non-Payroll: Outsource, magang, freelance, dll',
    )
    
    employment_status = fields.Selection(
        selection=[
            ('tetap', 'Tetap'),
            ('pkwt', 'PKWT'),
            ('spk', 'SPK'),
            ('thl', 'THL'),
            ('hju', 'HJU'),
            ('pns_dpk', 'PNS DPK'),
        ],
        string='Status Kepegawaian',
        required=True,
        index=True,
        help='Status kontrak/kepegawaian karyawan:\n'
             '- Tetap: Karyawan permanen\n'
             '- PKWT: Perjanjian Kerja Waktu Tertentu\n'
             '- SPK: Surat Perjanjian Kerja\n'
             '- THL: Tenaga Harian Lepas\n'
             '- HJU: Honorer Jaminan Usaha\n'
             '- PNS DPK: PNS Diperbantukan',
    )
    
    # ===== Snapshot Period =====
    
    snapshot_month = fields.Integer(
        string='Bulan',
        required=True,
        index=True,
    )
    
    snapshot_year = fields.Integer(
        string='Tahun',
        required=True,
        index=True,
    )
    
    snapshot_date = fields.Date(
        string='Tanggal Snapshot',
        compute='_compute_snapshot_date',
        store=True,
        index=True,
    )
    
    # ===== Status Fields =====
    
    is_active = fields.Boolean(
        string='Aktif',
        default=True,
        help='Status aktif karyawan pada saat snapshot',
    )
    
    gender = fields.Selection(
        selection=[
            ('male', 'Pria'),
            ('female', 'Wanita'),
            ('other', 'Lainnya'),
        ],
        string='Jenis Kelamin',
    )
    
    # ===== Metadata =====
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Perusahaan',
        default=lambda self: self.env.company,
    )
    
    # ===== SQL Constraints =====
    
    _sql_constraints = [
        (
            'unique_employee_snapshot',
            'UNIQUE(employee_id, snapshot_month, snapshot_year)',
            'Snapshot untuk karyawan ini sudah ada pada periode yang sama!'
        ),
        (
            'check_month_range',
            'CHECK(snapshot_month >= 1 AND snapshot_month <= 12)',
            'Bulan harus antara 1-12!'
        ),
        (
            'check_year_range',
            'CHECK(snapshot_year >= 2000 AND snapshot_year <= 2100)',
            'Tahun harus antara 2000-2100!'
        ),
    ]
    
    # ===== Compute Methods =====
    
    @api.depends('snapshot_month', 'snapshot_year')
    def _compute_snapshot_date(self):
        """Compute tanggal akhir bulan snapshot."""
        for record in self:
            if record.snapshot_month and record.snapshot_year:
                # Get last day of the month
                last_day = monthrange(record.snapshot_year, record.snapshot_month)[1]
                record.snapshot_date = date(
                    record.snapshot_year,
                    record.snapshot_month,
                    last_day
                )
            else:
                record.snapshot_date = False
    
    @api.depends('employee_id', 'snapshot_month', 'snapshot_year')
    def _compute_display_name(self):
        """Generate display name."""
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
            5: 'Mei', 6: 'Jun', 7: 'Jul', 8: 'Agu',
            9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
        }
        for record in self:
            if record.employee_id and record.snapshot_month and record.snapshot_year:
                month_str = month_names.get(record.snapshot_month, str(record.snapshot_month))
                record.display_name = f"{record.employee_id.name} - {month_str} {record.snapshot_year}"
            else:
                record.display_name = "New Snapshot"
    
    # ===== CRUD Override =====
    
    def write(self, vals):
        """
        Override write untuk enforce immutability.
        Hanya field non-core yang bisa diupdate.
        """
        immutable_fields = {
            'employee_id', 'unit_id', 'employment_type', 'employment_status',
            'snapshot_month', 'snapshot_year', 'is_active', 'gender'
        }
        
        updating_immutable = set(vals.keys()) & immutable_fields
        if updating_immutable:
            raise UserError(_(
                'Data snapshot bersifat immutable dan tidak dapat diubah.\n'
                'Field yang tidak dapat diubah: %s'
            ) % ', '.join(updating_immutable))
        
        return super().write(vals)
    
    # ===== Business Methods =====
    
    @api.model
    def generate_monthly_snapshot(self, year=None, month=None, force=False):
        """
        Generate snapshot untuk seluruh karyawan aktif.
        
        Args:
            year: Tahun snapshot (default: tahun ini)
            month: Bulan snapshot (default: bulan lalu)
            force: Jika True, hapus snapshot yang sudah ada sebelum generate ulang
            
        Returns:
            int: Jumlah snapshot yang dibuat
        """
        today = date.today()
        
        # Default ke bulan lalu
        if not year or not month:
            first_of_this_month = today.replace(day=1)
            last_month = first_of_this_month - timedelta(days=1)
            year = year or last_month.year
            month = month or last_month.month
        
        _logger.info(f"Generating employee snapshot for {month}/{year}")
        
        # Check existing snapshots
        existing = self.search([
            ('snapshot_year', '=', year),
            ('snapshot_month', '=', month),
        ])
        
        if existing and not force:
            _logger.warning(f"Snapshot for {month}/{year} already exists. Use force=True to regenerate.")
            return 0
        
        if existing and force:
            _logger.info(f"Force mode: deleting {len(existing)} existing snapshots")
            existing.sudo().unlink()
        
        # Get all employees (active and inactive for historical accuracy)
        employees = self.env['hr.employee'].sudo().search([
            ('active', 'in', [True, False])
        ])
        
        snapshots_to_create = []
        
        for emp in employees:
            # Determine employment type
            employment_type = self._determine_employment_type(emp)
            
            # Determine employment status
            employment_status = self._determine_employment_status(emp)
            
            # Get unit/department
            unit_id = emp.department_id.id if emp.department_id else False
            
            if not unit_id:
                _logger.warning(f"Employee {emp.name} has no department, skipping snapshot")
                continue
            
            snapshot_data = {
                'employee_id': emp.id,
                'unit_id': unit_id,
                'employment_type': employment_type,
                'employment_status': employment_status,
                'snapshot_month': month,
                'snapshot_year': year,
                'is_active': emp.active,
                'gender': emp.gender or 'other',
                'company_id': emp.company_id.id if emp.company_id else self.env.company.id,
            }
            
            snapshots_to_create.append(snapshot_data)
        
        # Bulk create snapshots
        if snapshots_to_create:
            created = self.sudo().create(snapshots_to_create)
            _logger.info(f"Created {len(created)} employee snapshots for {month}/{year}")
            return len(created)
        
        return 0
    
    def _determine_employment_type(self, employee):
        """
        Determine employment type dari data karyawan.
        
        Returns:
            str: 'payroll' atau 'non_payroll'
        """
        # Definisi tipe non-payroll
        non_payroll_types = ['outsource', 'intern', 'freelance', 'contractor', 'magang', 'harian']
        non_payroll_statuses = ['thl', 'hju', 'spk']
        
        # Coba dari employee_type_id (yhc_employee field)
        if hasattr(employee, 'employee_type_id') and employee.employee_type_id:
            type_name = employee.employee_type_id.name.lower() if employee.employee_type_id.name else ''
            
            for np_type in non_payroll_types:
                if np_type in type_name:
                    return 'non_payroll'
            
            for np_status in non_payroll_statuses:
                if np_status in type_name:
                    return 'non_payroll'
        
        # Coba dari employee_category_id
        if hasattr(employee, 'employee_category_id') and employee.employee_category_id:
            cat_name = employee.employee_category_id.name.lower() if employee.employee_category_id.name else ''
            
            for np_type in non_payroll_types:
                if np_type in cat_name:
                    return 'non_payroll'
        
        # Coba dari custom field x_employment_type atau employee_type
        emp_type = getattr(employee, 'x_employment_type', False) or \
                   getattr(employee, 'employee_type', False)
        
        if isinstance(emp_type, str) and emp_type.lower() in non_payroll_types:
            return 'non_payroll'
        
        return 'payroll'
    
    def _determine_employment_status(self, employee):
        """
        Determine employment status dari data karyawan.
        
        Returns:
            str: Status kepegawaian (tetap, pkwt, spk, thl, hju, pns_dpk)
        """
        # Coba dari employee_type_id (hr.employee.type) - field dari yhc_employee
        if hasattr(employee, 'employee_type_id') and employee.employee_type_id:
            type_name = employee.employee_type_id.name.lower() if employee.employee_type_id.name else ''
            
            # Mapping dari nama tipe ke status standar
            type_mapping = {
                'tetap': 'tetap',
                'permanent': 'tetap',
                'pkwt': 'pkwt',
                'kontrak': 'pkwt',
                'contract': 'pkwt',
                'spk': 'spk',
                'thl': 'thl',
                'hju': 'hju',
                'honorer': 'hju',
                'pns dpk': 'pns_dpk',
                'pns_dpk': 'pns_dpk',
                'pns': 'pns_dpk',
            }
            
            for key, value in type_mapping.items():
                if key in type_name:
                    return value
        
        # Coba dari employee_category_id (hr.employee.category)
        if hasattr(employee, 'employee_category_id') and employee.employee_category_id:
            cat_name = employee.employee_category_id.name.lower() if employee.employee_category_id.name else ''
            
            cat_mapping = {
                'tetap': 'tetap',
                'pkwt': 'pkwt',
                'spk': 'spk',
                'thl': 'thl',
                'hju': 'hju',
                'pns': 'pns_dpk',
            }
            
            for key, value in cat_mapping.items():
                if key in cat_name:
                    return value
        
        # Coba dari custom field x_employment_status atau contract_type
        status = getattr(employee, 'x_employment_status', False) or \
                 getattr(employee, 'contract_type', False)
        
        if isinstance(status, str):
            # Mapping dari berbagai format ke format standar
            status_mapping = {
                'permanent': 'tetap',
                'tetap': 'tetap',
                'contract': 'pkwt',
                'pkwt': 'pkwt',
                'spk': 'spk',
                'thl': 'thl',
                'hju': 'hju',
                'pns_dpk': 'pns_dpk',
                'pns': 'pns_dpk',
            }
            normalized_status = status_mapping.get(status.lower(), 'tetap')
            return normalized_status
        
        # Coba dari contract_id jika modul hr_contract terinstall
        if hasattr(employee, 'contract_id') and employee.contract_id:
            contract = employee.contract_id
            if hasattr(contract, 'date_end') and contract.date_end:
                return 'pkwt'  # Ada tanggal akhir = kontrak waktu tertentu
            else:
                return 'tetap'  # Tidak ada tanggal akhir = tetap
        
        return 'tetap'  # Default
    
    @api.model
    def get_snapshot_summary(self, year, month, unit_ids=None):
        """
        Get ringkasan snapshot untuk periode tertentu.
        
        Args:
            year: Tahun snapshot
            month: Bulan snapshot
            unit_ids: List of department IDs untuk filter (optional)
            
        Returns:
            dict: Summary data
        """
        domain = [
            ('snapshot_year', '=', year),
            ('snapshot_month', '=', month),
            ('is_active', '=', True),
        ]
        
        if unit_ids:
            domain.append(('unit_id', 'in', unit_ids))
        
        snapshots = self.search(domain)
        
        return {
            'total': len(snapshots),
            'payroll': len(snapshots.filtered(lambda s: s.employment_type == 'payroll')),
            'non_payroll': len(snapshots.filtered(lambda s: s.employment_type == 'non_payroll')),
            'by_status': self._group_by_status(snapshots),
            'by_unit': self._group_by_unit(snapshots),
            'by_gender': self._group_by_gender(snapshots),
        }
    
    def _group_by_status(self, snapshots):
        """Group snapshots berdasarkan status kepegawaian."""
        result = {}
        for snap in snapshots:
            status = snap.employment_status
            result[status] = result.get(status, 0) + 1
        return result
    
    def _group_by_unit(self, snapshots):
        """Group snapshots berdasarkan unit."""
        result = {}
        for snap in snapshots:
            unit_name = snap.unit_id.name if snap.unit_id else 'Tidak Ada Unit'
            result[unit_name] = result.get(unit_name, 0) + 1
        return result
    
    def _group_by_gender(self, snapshots):
        """Group snapshots berdasarkan gender."""
        result = {'male': 0, 'female': 0, 'other': 0}
        for snap in snapshots:
            gender = snap.gender or 'other'
            result[gender] = result.get(gender, 0) + 1
        return result
    
    @api.model
    def check_snapshot_exists(self, year, month):
        """
        Check apakah snapshot untuk periode tersebut sudah ada.
        
        Returns:
            bool: True jika ada
        """
        return bool(self.search_count([
            ('snapshot_year', '=', year),
            ('snapshot_month', '=', month),
        ]))
    
    @api.model
    def get_available_periods(self, limit=24):
        """
        Get daftar periode yang tersedia.
        
        Returns:
            list: List of tuples (year, month, count)
        """
        query = """
            SELECT snapshot_year, snapshot_month, COUNT(id) as count
            FROM hr_employee_snapshot
            GROUP BY snapshot_year, snapshot_month
            ORDER BY snapshot_year DESC, snapshot_month DESC
            LIMIT %s
        """
        self.env.cr.execute(query, (limit,))
        return self.env.cr.fetchall()
