# -*- coding: utf-8 -*-
"""
Service: Employee Analytics Service
Centralized analytics service untuk dashboard dan PDF export.

SINGLE SOURCE OF TRUTH untuk semua agregasi data analytics.
Service ini digunakan oleh:
- Dashboard OWL
- Graph PDF Export
- API Endpoints

PRINSIP:
- Semua agregasi di backend
- Dashboard dan PDF HARUS menggunakan service ini
- Data berbasis snapshot untuk laporan historis
- Caching untuk performa optimal
"""

import logging
from datetime import date, timedelta
from functools import lru_cache
from calendar import monthrange

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class EmployeeAnalyticsService:
    """
    Centralized analytics service.
    
    Menyediakan method agregasi yang reusable untuk:
    - Dashboard
    - PDF Export
    - API
    
    Semua method mengembalikan format yang konsisten:
    {
        'labels': [...],
        'data': [...],
        'colors': [...],
        'total': int,
        'metadata': {...}
    }
    """
    
    def __init__(self, env):
        """
        Initialize analytics service.
        
        Args:
            env: Odoo environment
        """
        self.env = env
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    # ===== UTILITY METHODS =====
    
    def _get_cache_key(self, method_name, *args, **kwargs):
        """Generate cache key untuk method."""
        return f"{method_name}_{hash(str(args))}_{hash(str(sorted(kwargs.items())))}"
    
    def _get_snapshot_domain(self, snapshot_date, unit_ids=None, active_only=True):
        """
        Build domain untuk query snapshot.
        
        Args:
            snapshot_date: Date object (tanggal cut-off)
            unit_ids: List of department IDs (optional)
            active_only: Hanya ambil karyawan aktif
            
        Returns:
            list: Domain filter
        """
        domain = [
            ('snapshot_year', '=', snapshot_date.year),
            ('snapshot_month', '=', snapshot_date.month),
        ]
        
        if active_only:
            domain.append(('is_active', '=', True))
        
        if unit_ids:
            domain.append(('unit_id', 'in', unit_ids))
        
        return domain
    
    def _get_snapshots(self, snapshot_date, unit_ids=None, active_only=True):
        """
        Get snapshot records untuk periode tertentu.
        
        Args:
            snapshot_date: Date object
            unit_ids: List of department IDs (optional)
            active_only: Hanya ambil karyawan aktif
            
        Returns:
            recordset: hr.employee.snapshot records
        """
        Snapshot = self.env['hr.employee.snapshot']
        domain = self._get_snapshot_domain(snapshot_date, unit_ids, active_only)
        return Snapshot.sudo().search(domain)
    
    def _check_snapshot_exists(self, snapshot_date):
        """
        Check apakah snapshot untuk periode tersebut ada.
        
        Args:
            snapshot_date: Date object
            
        Returns:
            bool: True jika ada
        """
        Snapshot = self.env['hr.employee.snapshot']
        return Snapshot.check_snapshot_exists(
            snapshot_date.year,
            snapshot_date.month
        )
    
    # ===== GRAPH G21: Payroll vs Non-Payroll per Unit =====
    
    def payroll_vs_non_payroll(self, snapshot_date, unit_ids=None):
        """
        G21: Perbandingan Payroll vs Non-Payroll per Unit.
        
        Args:
            snapshot_date: Date object untuk cut-off
            unit_ids: List of department IDs untuk filter (optional)
            
        Returns:
            dict: {
                'labels': ['Unit A', 'Unit B', ...],
                'datasets': [
                    {'label': 'Payroll', 'data': [10, 20, ...]},
                    {'label': 'Non-Payroll', 'data': [5, 10, ...]},
                ],
                'colors': ['#714B67', '#017E84'],
                'total': int,
                'metadata': {...}
            }
        """
        snapshots = self._get_snapshots(snapshot_date, unit_ids)
        
        if not snapshots:
            return self._empty_chart_data('Tidak ada data snapshot')
        
        # Group by unit
        unit_data = {}
        for snap in snapshots:
            unit_name = snap.unit_id.name if snap.unit_id else 'Lainnya'
            if unit_name not in unit_data:
                unit_data[unit_name] = {'payroll': 0, 'non_payroll': 0}
            unit_data[unit_name][snap.employment_type] += 1
        
        # Sort by total descending
        sorted_units = sorted(
            unit_data.items(),
            key=lambda x: x[1]['payroll'] + x[1]['non_payroll'],
            reverse=True
        )[:15]  # Top 15 units
        
        labels = [u[0] for u in sorted_units]
        payroll_data = [u[1]['payroll'] for u in sorted_units]
        non_payroll_data = [u[1]['non_payroll'] for u in sorted_units]
        
        return {
            'labels': labels,
            'datasets': [
                {'label': 'Payroll', 'data': payroll_data},
                {'label': 'Non-Payroll', 'data': non_payroll_data},
            ],
            'colors': ['#714B67', '#017E84'],
            'total': len(snapshots),
            'chart_type': 'bar',
            'metadata': {
                'snapshot_date': snapshot_date.isoformat(),
                'unit_count': len(unit_data),
                'total_payroll': sum(payroll_data),
                'total_non_payroll': sum(non_payroll_data),
            }
        }
    
    # ===== GRAPH G22: Total Karyawan per Unit =====
    
    def total_employee_per_unit(self, snapshot_date, unit_ids=None):
        """
        G22: Total Karyawan per Unit (Aggregate).
        
        Grafik utama untuk Executive Summary.
        Menampilkan total karyawan termasuk semua status.
        
        Args:
            snapshot_date: Date object
            unit_ids: List of department IDs (optional)
            
        Returns:
            dict: Chart data
        """
        snapshots = self._get_snapshots(snapshot_date, unit_ids)
        
        if not snapshots:
            return self._empty_chart_data('Tidak ada data snapshot')
        
        # Group by unit
        unit_totals = {}
        unit_details = {}
        
        for snap in snapshots:
            unit_name = snap.unit_id.name if snap.unit_id else 'Lainnya'
            
            if unit_name not in unit_totals:
                unit_totals[unit_name] = 0
                unit_details[unit_name] = {
                    'payroll': 0,
                    'non_payroll': 0,
                    'by_status': {}
                }
            
            unit_totals[unit_name] += 1
            unit_details[unit_name][snap.employment_type] += 1
            
            status = snap.employment_status
            if status not in unit_details[unit_name]['by_status']:
                unit_details[unit_name]['by_status'][status] = 0
            unit_details[unit_name]['by_status'][status] += 1
        
        # Sort by total descending
        sorted_units = sorted(
            unit_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]  # Top 20 units
        
        labels = [u[0] for u in sorted_units]
        data = [u[1] for u in sorted_units]
        
        # Generate colors
        colors = self._generate_colors(len(labels))
        
        return {
            'labels': labels,
            'data': data,
            'colors': colors,
            'total': len(snapshots),
            'chart_type': 'bar',
            'metadata': {
                'snapshot_date': snapshot_date.isoformat(),
                'unit_count': len(unit_totals),
                'details': {k: unit_details[k] for k in labels},
            }
        }
    
    # ===== GRAPH G23: Workforce Snapshot Trend (Monthly) =====
    
    def workforce_snapshot_trend(self, unit_id=None, year=None, months=12):
        """
        G23: Trend Workforce Snapshot per Bulan.
        
        Menampilkan perubahan jumlah karyawan bulanan.
        
        Args:
            unit_id: Single department ID untuk filter (optional)
            year: Tahun referensi (default: tahun ini)
            months: Jumlah bulan ke belakang (default: 12)
            
        Returns:
            dict: Chart data
        """
        today = date.today()
        year = year or today.year
        
        # Build list of periods (last N months)
        periods = []
        current_date = date(year, today.month, 1)
        
        for _ in range(months):
            periods.insert(0, (current_date.year, current_date.month))
            # Move to previous month
            current_date = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        
        Snapshot = self.env['hr.employee.snapshot']
        
        labels = []
        total_data = []
        payroll_data = []
        non_payroll_data = []
        
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
            5: 'Mei', 6: 'Jun', 7: 'Jul', 8: 'Agu',
            9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
        }
        
        for year_p, month_p in periods:
            domain = [
                ('snapshot_year', '=', year_p),
                ('snapshot_month', '=', month_p),
                ('is_active', '=', True),
            ]
            
            if unit_id:
                domain.append(('unit_id', '=', unit_id))
            
            snapshots = Snapshot.sudo().search(domain)
            
            labels.append(f"{month_names[month_p]} {year_p}")
            total_data.append(len(snapshots))
            payroll_data.append(len(snapshots.filtered(
                lambda s: s.employment_type == 'payroll'
            )))
            non_payroll_data.append(len(snapshots.filtered(
                lambda s: s.employment_type == 'non_payroll'
            )))
        
        return {
            'labels': labels,
            'datasets': [
                {'label': 'Total', 'data': total_data, 'borderColor': '#714B67'},
                {'label': 'Payroll', 'data': payroll_data, 'borderColor': '#27AE60'},
                {'label': 'Non-Payroll', 'data': non_payroll_data, 'borderColor': '#E74C3C'},
            ],
            'colors': ['#714B67', '#27AE60', '#E74C3C'],
            'total': sum(total_data),
            'chart_type': 'line',
            'metadata': {
                'periods': len(periods),
                'year': year,
                'unit_id': unit_id,
            }
        }
    
    # ===== GRAPH G24: Employment Status Distribution =====
    
    def employment_status_distribution(self, snapshot_date, unit_ids=None):
        """
        G24: Distribusi Status Kepegawaian.
        
        Args:
            snapshot_date: Date object
            unit_ids: List of department IDs (optional)
            
        Returns:
            dict: Chart data
        """
        snapshots = self._get_snapshots(snapshot_date, unit_ids)
        
        if not snapshots:
            return self._empty_chart_data('Tidak ada data snapshot')
        
        # Status labels mapping
        status_labels = {
            'tetap': 'Tetap',
            'pkwt': 'PKWT',
            'spk': 'SPK',
            'thl': 'THL',
            'hju': 'HJU',
            'pns_dpk': 'PNS DPK',
        }
        
        status_colors = {
            'tetap': '#27AE60',
            'pkwt': '#3498DB',
            'spk': '#F39C12',
            'thl': '#E74C3C',
            'hju': '#9B59B6',
            'pns_dpk': '#1ABC9C',
        }
        
        # Count by status
        status_counts = {}
        for snap in snapshots:
            status = snap.employment_status
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        # Sort by count descending
        sorted_statuses = sorted(
            status_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        labels = [status_labels.get(s[0], s[0]) for s in sorted_statuses]
        data = [s[1] for s in sorted_statuses]
        colors = [status_colors.get(s[0], '#714B67') for s in sorted_statuses]
        
        return {
            'labels': labels,
            'data': data,
            'colors': colors,
            'total': len(snapshots),
            'chart_type': 'pie',
            'metadata': {
                'snapshot_date': snapshot_date.isoformat(),
                'status_breakdown': {
                    status_labels.get(k, k): v
                    for k, v in status_counts.items()
                }
            }
        }
    
    # ===== COMBINED ANALYTICS (for Dashboard/PDF) =====
    
    def get_executive_summary(self, snapshot_date, unit_ids=None):
        """
        Get complete executive summary data.
        
        Returns semua grafik yang diperlukan untuk Executive Summary:
        - G22: Total per Unit (mandatory)
        - G21: Payroll vs Non-Payroll
        - G24: Status Distribution
        - KPI Summary
        
        Args:
            snapshot_date: Date object
            unit_ids: List of department IDs (optional)
            
        Returns:
            dict: Complete analytics data
        """
        return {
            'snapshot_date': snapshot_date.isoformat(),
            'snapshot_available': self._check_snapshot_exists(snapshot_date),
            'kpi': self.get_kpi_summary(snapshot_date, unit_ids),
            'g22_total_per_unit': self.total_employee_per_unit(snapshot_date, unit_ids),
            'g21_payroll_comparison': self.payroll_vs_non_payroll(snapshot_date, unit_ids),
            'g24_status_distribution': self.employment_status_distribution(snapshot_date, unit_ids),
        }
    
    def get_kpi_summary(self, snapshot_date, unit_ids=None):
        """
        Get KPI summary dari snapshot.
        
        Args:
            snapshot_date: Date object
            unit_ids: List of department IDs (optional)
            
        Returns:
            dict: KPI data
        """
        snapshots = self._get_snapshots(snapshot_date, unit_ids)
        active_snapshots = snapshots.filtered(lambda s: s.is_active)
        
        total = len(snapshots)
        active = len(active_snapshots)
        payroll = len(active_snapshots.filtered(lambda s: s.employment_type == 'payroll'))
        non_payroll = len(active_snapshots.filtered(lambda s: s.employment_type == 'non_payroll'))
        
        # Gender breakdown
        male = len(active_snapshots.filtered(lambda s: s.gender == 'male'))
        female = len(active_snapshots.filtered(lambda s: s.gender == 'female'))
        
        return {
            'total_employees': total,
            'active_employees': active,
            'inactive_employees': total - active,
            'payroll_count': payroll,
            'non_payroll_count': non_payroll,
            'payroll_percentage': round((payroll / active * 100), 1) if active else 0,
            'male_count': male,
            'female_count': female,
            'male_percentage': round((male / active * 100), 1) if active else 0,
            'snapshot_date': snapshot_date.isoformat(),
        }
    
    # ===== HELPER METHODS =====
    
    def _empty_chart_data(self, message='Tidak ada data'):
        """Return empty chart data structure."""
        return {
            'labels': [],
            'data': [],
            'colors': [],
            'total': 0,
            'chart_type': 'bar',
            'metadata': {
                'error': message,
                'empty': True,
            }
        }
    
    def _generate_colors(self, count):
        """Generate color palette."""
        base_colors = [
            '#714B67', '#017E84', '#E6007E', '#F39C12', '#27AE60',
            '#3498DB', '#9B59B6', '#E74C3C', '#1ABC9C', '#34495E',
            '#2C3E50', '#16A085', '#C0392B', '#8E44AD', '#2980B9',
        ]
        
        colors = []
        for i in range(count):
            colors.append(base_colors[i % len(base_colors)])
        
        return colors
    
    # ===== REAL-TIME FALLBACK METHODS =====
    # Used when snapshot data is not available
    
    def get_realtime_analytics(self, department_ids=None):
        """
        Fallback ke real-time analytics jika snapshot tidak tersedia.
        
        WARNING: Gunakan hanya jika snapshot tidak ada.
        
        Args:
            department_ids: List of department IDs untuk filter
            
        Returns:
            dict: Analytics data
        """
        domain = [('active', '=', True)]
        if department_ids:
            domain.append(('department_id', 'in', department_ids))
        
        employees = self.env['hr.employee'].sudo().search(domain)
        
        # Group by department
        dept_data = {}
        for emp in employees:
            dept_name = emp.department_id.name if emp.department_id else 'Lainnya'
            if dept_name not in dept_data:
                dept_data[dept_name] = {'total': 0, 'payroll': 0, 'non_payroll': 0}
            
            dept_data[dept_name]['total'] += 1
            
            # Determine payroll status
            emp_type = getattr(emp, 'x_employment_type', 'employee') or 'employee'
            if isinstance(emp_type, str) and emp_type.lower() in ['outsource', 'intern', 'freelance']:
                dept_data[dept_name]['non_payroll'] += 1
            else:
                dept_data[dept_name]['payroll'] += 1
        
        return {
            'source': 'realtime',
            'warning': 'Data ini bukan dari snapshot. Mungkin tidak konsisten untuk laporan historis.',
            'total': len(employees),
            'by_department': dept_data,
        }


# ===== Model Integration =====

class HrEmployeeAnalyticsService(models.TransientModel):
    """
    Transient model wrapper untuk EmployeeAnalyticsService.
    
    Menyediakan akses ke analytics service melalui ORM.
    """
    
    _name = 'hr.employee.analytics.service'
    _description = 'Employee Analytics Service Model'
    
    @api.model
    def get_service(self):
        """Get instance of EmployeeAnalyticsService."""
        return EmployeeAnalyticsService(self.env)
    
    @api.model
    def payroll_vs_non_payroll(self, snapshot_date, unit_ids=None):
        """G21: Payroll vs Non-Payroll per Unit."""
        service = self.get_service()
        return service.payroll_vs_non_payroll(
            fields.Date.from_string(snapshot_date) if isinstance(snapshot_date, str) else snapshot_date,
            unit_ids
        )
    
    @api.model
    def total_employee_per_unit(self, snapshot_date, unit_ids=None):
        """G22: Total Karyawan per Unit."""
        service = self.get_service()
        return service.total_employee_per_unit(
            fields.Date.from_string(snapshot_date) if isinstance(snapshot_date, str) else snapshot_date,
            unit_ids
        )
    
    @api.model
    def workforce_snapshot_trend(self, unit_id=None, year=None, months=12):
        """G23: Workforce Snapshot Trend."""
        service = self.get_service()
        return service.workforce_snapshot_trend(unit_id, year, months)
    
    @api.model
    def employment_status_distribution(self, snapshot_date, unit_ids=None):
        """G24: Employment Status Distribution."""
        service = self.get_service()
        return service.employment_status_distribution(
            fields.Date.from_string(snapshot_date) if isinstance(snapshot_date, str) else snapshot_date,
            unit_ids
        )
    
    @api.model
    def get_executive_summary(self, snapshot_date, unit_ids=None):
        """Get complete executive summary."""
        service = self.get_service()
        return service.get_executive_summary(
            fields.Date.from_string(snapshot_date) if isinstance(snapshot_date, str) else snapshot_date,
            unit_ids
        )
    
    @api.model
    def get_kpi_summary(self, snapshot_date, unit_ids=None):
        """Get KPI summary."""
        service = self.get_service()
        return service.get_kpi_summary(
            fields.Date.from_string(snapshot_date) if isinstance(snapshot_date, str) else snapshot_date,
            unit_ids
        )
