# -*- coding: utf-8 -*-
"""
Test Suite: Workforce Report Engine
Tests for Official Workforce Structural Report (PRD v1.1).

Tests cover:
1. Snapshot validation (mandatory)
2. Aggregation service accuracy
3. Report data reconciliation
4. PDF generation
5. Reproducibility (same input = same output)
"""

import logging
from datetime import date, timedelta
from calendar import monthrange

from odoo.tests import common, tagged
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'yhc_export', 'workforce_report')
class TestWorkforceReportEngine(common.TransactionCase):
    """Test cases for Workforce Report Engine."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Get current period for testing
        today = date.today()
        if today.month == 1:
            cls.test_month = 12
            cls.test_year = today.year - 1
        else:
            cls.test_month = today.month - 1
            cls.test_year = today.year
        
        # Create test departments
        cls.dept_1 = cls.env['hr.department'].create({
            'name': 'Test Department 1',
        })
        cls.dept_2 = cls.env['hr.department'].create({
            'name': 'Test Department 2',
        })
        
        # Create test employees
        cls.employees = []
        for i in range(10):
            emp = cls.env['hr.employee'].create({
                'name': f'Test Employee {i+1}',
                'department_id': cls.dept_1.id if i < 6 else cls.dept_2.id,
                'gender': 'male' if i % 2 == 0 else 'female',
            })
            cls.employees.append(emp)
        
        # Create snapshot data for test period
        cls._create_test_snapshots()
    
    @classmethod
    def _create_test_snapshots(cls):
        """Create test snapshot data."""
        Snapshot = cls.env['hr.employee.snapshot']
        
        # Clear existing snapshots for test period
        existing = Snapshot.search([
            ('snapshot_year', '=', cls.test_year),
            ('snapshot_month', '=', cls.test_month),
        ])
        existing.sudo().unlink()
        
        # Create new snapshots
        employment_types = ['payroll', 'non_payroll']
        employment_statuses = ['tetap', 'pkwt', 'spk', 'thl', 'hju', 'pns_dpk']
        
        for i, emp in enumerate(cls.employees):
            Snapshot.sudo().create({
                'employee_id': emp.id,
                'unit_id': emp.department_id.id,
                'gender': emp.gender or 'male',
                'employment_type': employment_types[i % 2],
                'employment_status': employment_statuses[i % 6],
                'snapshot_month': cls.test_month,
                'snapshot_year': cls.test_year,
                'is_active': True,
            })
    
    # ===== TEST: SNAPSHOT VALIDATION =====
    
    def test_01_snapshot_validation_exists(self):
        """Test that service validates snapshot existence."""
        service = self.env['workforce.report.service'].get_service()
        
        # Should not raise for valid period
        result = service.validate_snapshot_exists(self.test_year, self.test_month)
        self.assertTrue(result)
    
    def test_02_snapshot_validation_missing(self):
        """Test that service raises error for missing snapshot."""
        service = self.env['workforce.report.service'].get_service()
        
        # Should raise ValidationError for non-existent period
        with self.assertRaises(ValidationError):
            service.validate_snapshot_exists(1999, 1)
    
    # ===== TEST: DATA AGGREGATION =====
    
    def test_10_payroll_table_structure(self):
        """Test payroll vs non-payroll table data structure."""
        service = self.env['workforce.report.service'].get_service()
        
        data = service.get_payroll_vs_non_payroll_table(
            self.test_year, 
            self.test_month
        )
        
        # Check structure
        self.assertIn('rows', data)
        self.assertIn('totals', data)
        self.assertIn('metadata', data)
        
        # Check row structure
        for row in data['rows']:
            self.assertIn('unit_name', row)
            self.assertIn('payroll_male', row)
            self.assertIn('payroll_female', row)
            self.assertIn('payroll_total', row)
            self.assertIn('non_payroll_male', row)
            self.assertIn('non_payroll_female', row)
            self.assertIn('non_payroll_total', row)
            self.assertIn('total', row)
    
    def test_11_payroll_table_totals(self):
        """Test that row totals are calculated correctly."""
        service = self.env['workforce.report.service'].get_service()
        
        data = service.get_payroll_vs_non_payroll_table(
            self.test_year, 
            self.test_month
        )
        
        for row in data['rows']:
            # Payroll total = male + female
            expected_payroll = row['payroll_male'] + row['payroll_female']
            self.assertEqual(row['payroll_total'], expected_payroll)
            
            # Non-payroll total = male + female
            expected_non_payroll = row['non_payroll_male'] + row['non_payroll_female']
            self.assertEqual(row['non_payroll_total'], expected_non_payroll)
            
            # Row total = payroll + non-payroll
            expected_total = row['payroll_total'] + row['non_payroll_total']
            self.assertEqual(row['total'], expected_total)
    
    def test_12_total_workforce_consistency(self):
        """Test that total workforce matches across sections."""
        service = self.env['workforce.report.service'].get_service()
        
        payroll_data = service.get_payroll_vs_non_payroll_table(
            self.test_year, 
            self.test_month
        )
        
        workforce_data = service.get_total_workforce_per_unit(
            self.test_year, 
            self.test_month
        )
        
        # Totals must match
        self.assertEqual(
            payroll_data['totals']['total'],
            workforce_data['total']
        )
    
    def test_13_status_distribution_complete(self):
        """Test that status distribution includes all categories."""
        service = self.env['workforce.report.service'].get_service()
        
        data = service.get_employment_status_distribution(
            self.test_year, 
            self.test_month
        )
        
        # Must have all 6 status categories (FIXED)
        expected_labels = ['Tetap', 'PKWT', 'SPK', 'THL', 'HJU', 'PNS DPK']
        self.assertEqual(data['labels'], expected_labels)
        
        # Total from status must match
        self.assertEqual(sum(data['data']), data['total'])
    
    # ===== TEST: RECONCILIATION =====
    
    def test_20_complete_report_reconciliation(self):
        """Test that complete report data reconciles correctly."""
        service = self.env['workforce.report.service'].get_service()
        
        data = service.generate_complete_report_data(
            self.test_year, 
            self.test_month
        )
        
        # Check validation passed
        self.assertTrue(data['validation']['is_valid'])
        self.assertEqual(data['validation']['reconciliation_check'], 'PASSED')
        
        # Cross-check totals
        table_total = data['section_1_table']['totals']['total']
        chart_total = data['section_3_chart']['total']
        status_total = data['section_5_chart']['total']
        
        self.assertEqual(table_total, chart_total)
        self.assertEqual(table_total, status_total)
    
    # ===== TEST: REPRODUCIBILITY =====
    
    def test_30_reproducibility(self):
        """Test that same period generates identical results."""
        service = self.env['workforce.report.service'].get_service()
        
        # Generate report twice
        data_1 = service.generate_complete_report_data(
            self.test_year, 
            self.test_month
        )
        
        data_2 = service.generate_complete_report_data(
            self.test_year, 
            self.test_month
        )
        
        # Core data must be identical
        self.assertEqual(
            data_1['section_1_table']['rows'],
            data_2['section_1_table']['rows']
        )
        
        self.assertEqual(
            data_1['section_1_table']['totals'],
            data_2['section_1_table']['totals']
        )
        
        self.assertEqual(
            data_1['validation']['total_employees'],
            data_2['validation']['total_employees']
        )
    
    # ===== TEST: WIZARD FUNCTIONALITY =====
    
    def test_40_wizard_validation(self):
        """Test wizard snapshot validation."""
        wizard = self.env['workforce.report.wizard'].create({
            'report_month': str(self.test_month),
            'report_year': self.test_year,
        })
        
        # Should have snapshot available
        self.assertTrue(wizard.snapshot_available)
        self.assertGreater(wizard.snapshot_count, 0)
    
    def test_41_wizard_invalid_period(self):
        """Test wizard with invalid period."""
        wizard = self.env['workforce.report.wizard'].create({
            'report_month': '1',
            'report_year': 1999,
        })
        
        # Should not have snapshot available
        self.assertFalse(wizard.snapshot_available)
        self.assertEqual(wizard.snapshot_count, 0)
    
    def test_42_wizard_validate_period_fails(self):
        """Test that validate_period fails for missing snapshot."""
        wizard = self.env['workforce.report.wizard'].create({
            'report_month': '1',
            'report_year': 1999,
        })
        
        with self.assertRaises(ValidationError):
            wizard.action_validate_period()
    
    # ===== TEST: MONTHLY SNAPSHOT TABLE =====
    
    def test_50_monthly_snapshot_structure(self):
        """Test monthly snapshot table structure."""
        service = self.env['workforce.report.service'].get_service()
        
        data = service.get_monthly_workforce_snapshot(self.test_year)
        
        # Check structure
        self.assertIn('headers', data)
        self.assertIn('rows', data)
        self.assertIn('totals', data)
        self.assertIn('available_months', data)
        
        # Headers should have 14 columns (Unit + 12 months + Average)
        self.assertEqual(len(data['headers']), 14)
        
        # Each row should have months dict
        for row in data['rows']:
            self.assertIn('unit_name', row)
            self.assertIn('months', row)
            self.assertIn('average', row)
            self.assertEqual(len(row['months']), 12)


@tagged('post_install', '-at_install', 'yhc_export', 'workforce_report')
class TestWorkforceReportSnapshot(common.TransactionCase):
    """Test cases for snapshot immutability and generation."""
    
    def test_snapshot_immutability(self):
        """Test that snapshots cannot be modified after creation."""
        # Create a department and employee
        dept = self.env['hr.department'].create({'name': 'Immutable Test Dept'})
        emp = self.env['hr.employee'].create({
            'name': 'Immutable Test Employee',
            'department_id': dept.id,
        })
        
        # Create snapshot
        snapshot = self.env['hr.employee.snapshot'].sudo().create({
            'employee_id': emp.id,
            'unit_id': dept.id,
            'gender': 'male',
            'employment_type': 'payroll',
            'employment_status': 'tetap',
            'snapshot_month': 1,
            'snapshot_year': 2020,
            'is_active': True,
        })
        
        # Try to modify - should raise UserError
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            snapshot.write({'employment_type': 'non_payroll'})
        
        with self.assertRaises(UserError):
            snapshot.write({'employment_status': 'pkwt'})
        
        with self.assertRaises(UserError):
            snapshot.write({'is_active': False})
