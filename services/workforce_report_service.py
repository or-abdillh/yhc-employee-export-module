# -*- coding: utf-8 -*-
"""
Service: Workforce Report Service
Dedicated engine for Official Workforce Structural Report (PRD v1.1).

CRITICAL RULES:
1. Snapshot-based ONLY - No real-time data allowed
2. Unit organization is the PRIMARY dimension
3. Fixed structure - NOT configurable
4. Audit-ready with reproducible results
5. Backend aggregation ONLY

This is NOT:
- Dashboard analytics
- Export feature with options
- Flexible reporting tool

This IS:
- Official workforce structural report
- Source of truth for HR data
- Audit and reconciliation artifact
"""

import logging
from datetime import date
from calendar import monthrange
from collections import OrderedDict

from odoo import _, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


# Employment status labels (FIXED, SYSTEM-OWNED)
EMPLOYMENT_STATUS_LABELS = OrderedDict([
    ('tetap', 'Tetap'),
    ('pkwt', 'PKWT'),
    ('spk', 'SPK'),
    ('thl', 'THL'),
    ('hju', 'HJU'),
    ('pns_dpk', 'PNS DPK'),
])

# Employment status colors for charts
EMPLOYMENT_STATUS_COLORS = {
    'tetap': '#27AE60',    # Green
    'pkwt': '#3498DB',     # Blue
    'spk': '#F39C12',      # Orange
    'thl': '#E74C3C',      # Red
    'hju': '#9B59B6',      # Purple
    'pns_dpk': '#1ABC9C',  # Teal
}

# Month names in Indonesian
MONTH_NAMES = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
    5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}

MONTH_NAMES_SHORT = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
    5: 'Mei', 6: 'Jun', 7: 'Jul', 8: 'Agu',
    9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
}


class WorkforceReportService:
    """
    Dedicated service for Workforce Report Engine.
    
    PRINCIPLES (NON-NEGOTIABLE):
    1. All data MUST come from snapshots
    2. Structure is FIXED by the system
    3. Results MUST be reproducible
    4. No exploratory analytics
    5. No user-defined filters beyond period selection
    """
    
    def __init__(self, env):
        """
        Initialize workforce report service.
        
        Args:
            env: Odoo environment
        """
        self.env = env
    
    # ===== VALIDATION METHODS =====
    
    def validate_snapshot_exists(self, year, month):
        """
        Validate that snapshot data exists for the period.
        
        Args:
            year: Snapshot year
            month: Snapshot month
            
        Returns:
            bool: True if exists
            
        Raises:
            ValidationError: If snapshot not available
        """
        Snapshot = self.env['hr.employee.snapshot']
        exists = Snapshot.check_snapshot_exists(year, month)
        
        if not exists:
            raise ValidationError(_(
                'Snapshot untuk periode %s %d tidak tersedia.\n'
                'Laporan TIDAK DAPAT dibuat tanpa data snapshot.\n'
                'Silakan generate snapshot terlebih dahulu.'
            ) % (MONTH_NAMES.get(month, str(month)), year))
        
        return True
    
    def get_snapshot_count(self, year, month):
        """Get count of snapshot records for period."""
        Snapshot = self.env['hr.employee.snapshot']
        return Snapshot.search_count([
            ('snapshot_year', '=', year),
            ('snapshot_month', '=', month),
            ('is_active', '=', True),
        ])
    
    # ===== CORE DATA RETRIEVAL =====
    
    def _get_snapshots(self, year, month, active_only=True):
        """
        Get snapshot records for the specified period.
        
        Args:
            year: Snapshot year
            month: Snapshot month
            active_only: Only return active employees (default True)
            
        Returns:
            recordset: hr.employee.snapshot records
        """
        Snapshot = self.env['hr.employee.snapshot']
        domain = [
            ('snapshot_year', '=', year),
            ('snapshot_month', '=', month),
        ]
        
        if active_only:
            domain.append(('is_active', '=', True))
        
        return Snapshot.sudo().search(domain)
    
    def _get_units(self, snapshots):
        """
        Get unique units from snapshots, sorted by name.
        
        Args:
            snapshots: hr.employee.snapshot recordset
            
        Returns:
            list: List of unit dicts with id and name
        """
        units = {}
        for snap in snapshots:
            if snap.unit_id and snap.unit_id.id not in units:
                units[snap.unit_id.id] = {
                    'id': snap.unit_id.id,
                    'name': snap.unit_id.name,
                }
        
        return sorted(units.values(), key=lambda x: x['name'])
    
    # ===== SECTION 1: PAYROLL VS NON-PAYROLL PER UNIT (TABLE) =====
    
    def get_payroll_vs_non_payroll_table(self, year, month):
        """
        Generate table: Payroll vs Non-Payroll per Unit with gender breakdown.
        
        This is the PRIMARY data table for the report.
        
        Args:
            year: Snapshot year
            month: Snapshot month
            
        Returns:
            dict: {
                'rows': [
                    {
                        'unit_name': str,
                        'payroll_male': int,
                        'payroll_female': int,
                        'payroll_total': int,
                        'non_payroll_male': int,
                        'non_payroll_female': int,
                        'non_payroll_total': int,
                        'total': int,
                    },
                    ...
                ],
                'totals': {
                    'payroll_male': int,
                    'payroll_female': int,
                    'payroll_total': int,
                    'non_payroll_male': int,
                    'non_payroll_female': int,
                    'non_payroll_total': int,
                    'total': int,
                },
                'metadata': {...}
            }
        """
        self.validate_snapshot_exists(year, month)
        snapshots = self._get_snapshots(year, month)
        
        # Aggregate by unit
        unit_data = {}
        
        for snap in snapshots:
            unit_name = snap.unit_id.name if snap.unit_id else 'Tidak Ada Unit'
            
            if unit_name not in unit_data:
                unit_data[unit_name] = {
                    'payroll_male': 0,
                    'payroll_female': 0,
                    'non_payroll_male': 0,
                    'non_payroll_female': 0,
                }
            
            # Determine gender key
            gender_key = 'male' if snap.gender == 'male' else 'female'
            
            # Increment appropriate counter
            type_key = f"{snap.employment_type}_{gender_key}"
            unit_data[unit_name][type_key] += 1
        
        # Build rows
        rows = []
        totals = {
            'payroll_male': 0,
            'payroll_female': 0,
            'payroll_total': 0,
            'non_payroll_male': 0,
            'non_payroll_female': 0,
            'non_payroll_total': 0,
            'total': 0,
        }
        
        for unit_name in sorted(unit_data.keys()):
            data = unit_data[unit_name]
            
            payroll_total = data['payroll_male'] + data['payroll_female']
            non_payroll_total = data['non_payroll_male'] + data['non_payroll_female']
            unit_total = payroll_total + non_payroll_total
            
            row = {
                'unit_name': unit_name,
                'payroll_male': data['payroll_male'],
                'payroll_female': data['payroll_female'],
                'payroll_total': payroll_total,
                'non_payroll_male': data['non_payroll_male'],
                'non_payroll_female': data['non_payroll_female'],
                'non_payroll_total': non_payroll_total,
                'total': unit_total,
            }
            rows.append(row)
            
            # Update totals
            totals['payroll_male'] += data['payroll_male']
            totals['payroll_female'] += data['payroll_female']
            totals['payroll_total'] += payroll_total
            totals['non_payroll_male'] += data['non_payroll_male']
            totals['non_payroll_female'] += data['non_payroll_female']
            totals['non_payroll_total'] += non_payroll_total
            totals['total'] += unit_total
        
        return {
            'rows': rows,
            'totals': totals,
            'metadata': {
                'year': year,
                'month': month,
                'period_name': f"{MONTH_NAMES.get(month)} {year}",
                'unit_count': len(rows),
                'snapshot_count': len(snapshots),
            }
        }
    
    # ===== SECTION 2: PAYROLL VS NON-PAYROLL CHART DATA =====
    
    def get_payroll_vs_non_payroll_chart(self, year, month):
        """
        Generate bar chart data: Payroll vs Non-Payroll per Unit.
        
        Values MUST match table data exactly.
        
        Args:
            year: Snapshot year
            month: Snapshot month
            
        Returns:
            dict: Chart.js compatible data structure
        """
        table_data = self.get_payroll_vs_non_payroll_table(year, month)
        
        labels = [row['unit_name'] for row in table_data['rows']]
        payroll_data = [row['payroll_total'] for row in table_data['rows']]
        non_payroll_data = [row['non_payroll_total'] for row in table_data['rows']]
        
        return {
            'chart_type': 'bar',
            'title': 'Perbandingan Payroll vs Non-Payroll per Unit',
            'labels': labels,
            'datasets': [
                {
                    'label': 'Payroll',
                    'data': payroll_data,
                    'backgroundColor': '#714B67',
                },
                {
                    'label': 'Non-Payroll',
                    'data': non_payroll_data,
                    'backgroundColor': '#017E84',
                },
            ],
            'totals': {
                'payroll': table_data['totals']['payroll_total'],
                'non_payroll': table_data['totals']['non_payroll_total'],
            },
            'metadata': table_data['metadata'],
        }
    
    # ===== SECTION 3: TOTAL WORKFORCE PER UNIT =====
    
    def get_total_workforce_per_unit(self, year, month):
        """
        Generate bar chart data: Total Workforce per Unit.
        
        Title: JUMLAH KARYAWAN (TERMASUK STATUS KHUSUS)
        
        Total = Payroll + Non-Payroll + HJU + PNS DPK
        (Note: HJU and PNS DPK are included in the snapshot status)
        
        Args:
            year: Snapshot year
            month: Snapshot month
            
        Returns:
            dict: Chart.js compatible data structure
        """
        self.validate_snapshot_exists(year, month)
        snapshots = self._get_snapshots(year, month)
        
        # Aggregate by unit
        unit_totals = {}
        unit_details = {}
        
        for snap in snapshots:
            unit_name = snap.unit_id.name if snap.unit_id else 'Tidak Ada Unit'
            
            if unit_name not in unit_totals:
                unit_totals[unit_name] = 0
                unit_details[unit_name] = {
                    'payroll': 0,
                    'non_payroll': 0,
                    'by_status': {status: 0 for status in EMPLOYMENT_STATUS_LABELS.keys()},
                }
            
            unit_totals[unit_name] += 1
            unit_details[unit_name][snap.employment_type] += 1
            unit_details[unit_name]['by_status'][snap.employment_status] += 1
        
        # Sort by total descending
        sorted_units = sorted(
            unit_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        labels = [u[0] for u in sorted_units]
        data = [u[1] for u in sorted_units]
        
        # Generate gradient colors
        colors = self._generate_gradient_colors(len(labels), '#714B67', '#017E84')
        
        return {
            'chart_type': 'bar',
            'title': 'JUMLAH KARYAWAN (TERMASUK STATUS KHUSUS)',
            'labels': labels,
            'datasets': [
                {
                    'label': 'Total Karyawan',
                    'data': data,
                    'backgroundColor': colors,
                },
            ],
            'total': sum(data),
            'details': {k: unit_details.get(k, {}) for k in labels},
            'metadata': {
                'year': year,
                'month': month,
                'period_name': f"{MONTH_NAMES.get(month)} {year}",
                'unit_count': len(labels),
            }
        }
    
    # ===== SECTION 4: MONTHLY SNAPSHOT TABLE (JAN-DEC) =====
    
    def get_monthly_workforce_snapshot(self, year):
        """
        Generate table: Monthly Workforce Snapshot per Unit (Jan-Dec).
        
        Args:
            year: Year for the snapshot
            
        Returns:
            dict: {
                'headers': ['Unit', 'Jan', 'Feb', ..., 'Des', 'Rata-rata'],
                'rows': [
                    {
                        'unit_name': str,
                        'months': {1: int, 2: int, ..., 12: int},
                        'average': float,
                    },
                    ...
                ],
                'totals': {
                    'months': {1: int, 2: int, ..., 12: int},
                    'average': float,
                },
                'available_months': [1, 3, 5, ...]  # months with data
            }
        """
        Snapshot = self.env['hr.employee.snapshot']
        
        # Get all units that have data in this year
        all_units = {}
        available_months = set()
        
        for month in range(1, 13):
            snapshots = Snapshot.sudo().search([
                ('snapshot_year', '=', year),
                ('snapshot_month', '=', month),
                ('is_active', '=', True),
            ])
            
            if snapshots:
                available_months.add(month)
                
                for snap in snapshots:
                    unit_name = snap.unit_id.name if snap.unit_id else 'Tidak Ada Unit'
                    
                    if unit_name not in all_units:
                        all_units[unit_name] = {m: 0 for m in range(1, 13)}
                    
                    all_units[unit_name][month] += 1
        
        # Build rows
        rows = []
        totals = {m: 0 for m in range(1, 13)}
        
        for unit_name in sorted(all_units.keys()):
            month_data = all_units[unit_name]
            
            # Calculate average only for available months
            values = [month_data[m] for m in available_months if month_data[m] > 0]
            avg = sum(values) / len(values) if values else 0
            
            rows.append({
                'unit_name': unit_name,
                'months': month_data,
                'average': round(avg, 1),
            })
            
            for m in range(1, 13):
                totals[m] += month_data[m]
        
        # Calculate total average
        total_values = [totals[m] for m in available_months if totals[m] > 0]
        total_avg = sum(total_values) / len(total_values) if total_values else 0
        
        # Build headers
        headers = ['Unit']
        headers.extend([MONTH_NAMES_SHORT.get(m) for m in range(1, 13)])
        headers.append('Rata-rata')
        
        return {
            'headers': headers,
            'rows': rows,
            'totals': {
                'months': totals,
                'average': round(total_avg, 1),
            },
            'available_months': sorted(list(available_months)),
            'metadata': {
                'year': year,
                'unit_count': len(rows),
                'months_with_data': len(available_months),
            }
        }
    
    # ===== SECTION 5: EMPLOYMENT STATUS DISTRIBUTION =====
    
    def get_employment_status_distribution(self, year, month):
        """
        Generate chart data: Employment Status Distribution.
        
        Categories (FIXED, NON-NEGOTIABLE):
        - Tetap
        - PKWT
        - SPK
        - THL
        - HJU
        - PNS DPK
        
        Args:
            year: Snapshot year
            month: Snapshot month
            
        Returns:
            dict: Chart.js compatible data structure
        """
        self.validate_snapshot_exists(year, month)
        snapshots = self._get_snapshots(year, month)
        
        # Count by status
        status_counts = {status: 0 for status in EMPLOYMENT_STATUS_LABELS.keys()}
        
        for snap in snapshots:
            if snap.employment_status in status_counts:
                status_counts[snap.employment_status] += 1
        
        # Build chart data (maintain fixed order)
        labels = []
        data = []
        colors = []
        
        for status_key, status_label in EMPLOYMENT_STATUS_LABELS.items():
            count = status_counts[status_key]
            labels.append(status_label)
            data.append(count)
            colors.append(EMPLOYMENT_STATUS_COLORS.get(status_key, '#714B67'))
        
        total = sum(data)
        
        # Calculate percentages
        percentages = []
        for count in data:
            pct = round((count / total * 100), 1) if total > 0 else 0
            percentages.append(pct)
        
        return {
            'chart_type': 'pie',
            'title': 'Distribusi Status Kepegawaian',
            'labels': labels,
            'data': data,
            'colors': colors,
            'percentages': percentages,
            'total': total,
            'breakdown': {
                label: {'count': count, 'percentage': pct}
                for label, count, pct in zip(labels, data, percentages)
            },
            'metadata': {
                'year': year,
                'month': month,
                'period_name': f"{MONTH_NAMES.get(month)} {year}",
            }
        }
    
    # ===== COMPLETE REPORT DATA =====
    
    def generate_complete_report_data(self, year, month):
        """
        Generate complete report data for PDF rendering.
        
        This method assembles ALL required sections in the FIXED order.
        
        Args:
            year: Snapshot year
            month: Snapshot month
            
        Returns:
            dict: Complete report data structure
            
        Raises:
            ValidationError: If snapshot not available
        """
        self.validate_snapshot_exists(year, month)
        
        # Generate all sections
        payroll_table = self.get_payroll_vs_non_payroll_table(year, month)
        payroll_chart = self.get_payroll_vs_non_payroll_chart(year, month)
        total_chart = self.get_total_workforce_per_unit(year, month)
        monthly_table = self.get_monthly_workforce_snapshot(year)
        status_chart = self.get_employment_status_distribution(year, month)
        
        # Validate totals reconciliation
        self._validate_reconciliation(payroll_table, payroll_chart, total_chart)
        
        return {
            # Header data
            'header': {
                'organization_name': self.env.company.name,
                'period_month': month,
                'period_year': year,
                'period_name': f"{MONTH_NAMES.get(month)} {year}",
                'report_title': 'LAPORAN STRUKTUR SDM',
                'report_subtitle': f"Periode {MONTH_NAMES.get(month)} {year}",
            },
            
            # Section 1: Payroll vs Non-Payroll Table
            'section_1_table': payroll_table,
            
            # Section 2: Payroll vs Non-Payroll Chart
            'section_2_chart': payroll_chart,
            
            # Section 3: Total Workforce per Unit Chart
            'section_3_chart': total_chart,
            
            # Section 4: Monthly Snapshot Table
            'section_4_table': monthly_table,
            
            # Section 5: Employment Status Distribution Chart
            'section_5_chart': status_chart,
            
            # Footer data
            'footer': {
                'generated_at': fields.Datetime.now(),
                'generated_by': self.env.user.name,
                'company_name': self.env.company.name,
            },
            
            # Validation
            'validation': {
                'is_valid': True,
                'reconciliation_check': 'PASSED',
                'total_employees': payroll_table['totals']['total'],
            }
        }
    
    def _validate_reconciliation(self, payroll_table, payroll_chart, total_chart):
        """
        Validate that totals reconcile across all sections.
        
        Raises:
            ValidationError: If totals do not match
        """
        table_total = payroll_table['totals']['total']
        chart_payroll = payroll_chart['totals']['payroll']
        chart_non_payroll = payroll_chart['totals']['non_payroll']
        chart_combined = chart_payroll + chart_non_payroll
        total_chart_sum = total_chart['total']
        
        if table_total != chart_combined:
            raise ValidationError(_(
                'VALIDATION ERROR: Total tidak konsisten!\n'
                'Table total: %d\n'
                'Chart combined: %d\n'
                'Laporan tidak dapat digenerate karena data tidak valid.'
            ) % (table_total, chart_combined))
        
        if table_total != total_chart_sum:
            raise ValidationError(_(
                'VALIDATION ERROR: Total workforce tidak konsisten!\n'
                'Payroll table total: %d\n'
                'Workforce chart total: %d\n'
                'Laporan tidak dapat digenerate karena data tidak valid.'
            ) % (table_total, total_chart_sum))
        
        _logger.info(f"Reconciliation PASSED: Total = {table_total}")
    
    # ===== HELPER METHODS =====
    
    def _generate_gradient_colors(self, count, start_color, end_color):
        """
        Generate gradient colors between two colors.
        
        Args:
            count: Number of colors to generate
            start_color: Start hex color
            end_color: End hex color
            
        Returns:
            list: List of hex colors
        """
        if count <= 1:
            return [start_color]
        
        # Parse hex colors
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)
        
        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)
        
        colors = []
        for i in range(count):
            ratio = i / (count - 1) if count > 1 else 0
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            colors.append(rgb_to_hex((r, g, b)))
        
        return colors
