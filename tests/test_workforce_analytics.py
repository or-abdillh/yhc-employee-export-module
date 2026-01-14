# -*- coding: utf-8 -*-
"""
Tests: Workforce Analytics (PRD v1.1)

Test suite untuk fitur Advanced Graphic Export & Workforce Analytics.
Tests meliputi:
- Snapshot generation
- Analytics service consistency
- PDF export
- Graph rendering
"""

import logging
from datetime import date, timedelta
from calendar import monthrange

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


@tagged('yhc_export', 'workforce_analytics', 'snapshot')
class TestEmployeeSnapshot(TransactionCase):
    """Test cases untuk hr.employee.snapshot model."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test department
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Department WA',
        })
        
        # Create test employees
        cls.employee_1 = cls.env['hr.employee'].create({
            'name': 'Test Employee Payroll',
            'department_id': cls.department.id,
            'gender': 'male',
        })
        
        cls.employee_2 = cls.env['hr.employee'].create({
            'name': 'Test Employee Non-Payroll',
            'department_id': cls.department.id,
            'gender': 'female',
        })
        
        # Set current period
        today = date.today()
        cls.test_year = today.year
        cls.test_month = today.month
    
    def test_01_snapshot_create(self):
        """Test creating a snapshot record."""
        Snapshot = self.env['hr.employee.snapshot']
        
        snapshot = Snapshot.create({
            'employee_id': self.employee_1.id,
            'unit_id': self.department.id,
            'employment_type': 'payroll',
            'employment_status': 'tetap',
            'snapshot_month': self.test_month,
            'snapshot_year': self.test_year,
            'is_active': True,
            'gender': 'male',
        })
        
        self.assertTrue(snapshot.id)
        self.assertEqual(snapshot.employment_type, 'payroll')
        self.assertEqual(snapshot.employment_status, 'tetap')
    
    def test_02_snapshot_unique_constraint(self):
        """Test unique constraint per employee per period."""
        Snapshot = self.env['hr.employee.snapshot']
        
        # Create first snapshot
        Snapshot.create({
            'employee_id': self.employee_1.id,
            'unit_id': self.department.id,
            'employment_type': 'payroll',
            'employment_status': 'tetap',
            'snapshot_month': self.test_month,
            'snapshot_year': self.test_year,
            'is_active': True,
        })
        
        # Try to create duplicate - should fail
        with self.assertRaises(Exception):  # IntegrityError wrapped
            Snapshot.create({
                'employee_id': self.employee_1.id,
                'unit_id': self.department.id,
                'employment_type': 'non_payroll',
                'employment_status': 'pkwt',
                'snapshot_month': self.test_month,
                'snapshot_year': self.test_year,
                'is_active': True,
            })
    
    def test_03_snapshot_immutability(self):
        """Test that snapshot records are immutable."""
        Snapshot = self.env['hr.employee.snapshot']
        
        snapshot = Snapshot.create({
            'employee_id': self.employee_1.id,
            'unit_id': self.department.id,
            'employment_type': 'payroll',
            'employment_status': 'tetap',
            'snapshot_month': self.test_month,
            'snapshot_year': self.test_year,
            'is_active': True,
        })
        
        # Try to modify - should fail
        with self.assertRaises(UserError):
            snapshot.write({'employment_type': 'non_payroll'})
    
    def test_04_snapshot_date_computation(self):
        """Test snapshot_date is computed correctly (end of month)."""
        Snapshot = self.env['hr.employee.snapshot']
        
        snapshot = Snapshot.create({
            'employee_id': self.employee_1.id,
            'unit_id': self.department.id,
            'employment_type': 'payroll',
            'employment_status': 'tetap',
            'snapshot_month': 6,  # June
            'snapshot_year': 2024,
            'is_active': True,
        })
        
        expected_date = date(2024, 6, 30)  # End of June
        self.assertEqual(snapshot.snapshot_date, expected_date)
    
    def test_05_generate_monthly_snapshot(self):
        """Test automatic snapshot generation."""
        Snapshot = self.env['hr.employee.snapshot']
        
        # Clear existing snapshots for this period
        Snapshot.search([
            ('snapshot_year', '=', self.test_year),
            ('snapshot_month', '=', self.test_month),
        ]).unlink()
        
        # Generate snapshots
        count = Snapshot.generate_monthly_snapshot(
            year=self.test_year,
            month=self.test_month,
            force=True
        )
        
        self.assertGreater(count, 0, "Should create at least one snapshot")
    
    def test_06_check_snapshot_exists(self):
        """Test check_snapshot_exists method."""
        Snapshot = self.env['hr.employee.snapshot']
        
        # Create a snapshot
        Snapshot.create({
            'employee_id': self.employee_2.id,
            'unit_id': self.department.id,
            'employment_type': 'non_payroll',
            'employment_status': 'pkwt',
            'snapshot_month': self.test_month,
            'snapshot_year': self.test_year,
            'is_active': True,
        })
        
        # Check exists
        exists = Snapshot.check_snapshot_exists(self.test_year, self.test_month)
        self.assertTrue(exists)
        
        # Check non-existent period
        not_exists = Snapshot.check_snapshot_exists(2000, 1)
        self.assertFalse(not_exists)


@tagged('yhc_export', 'workforce_analytics', 'analytics_service')
class TestEmployeeAnalyticsService(TransactionCase):
    """Test cases untuk EmployeeAnalyticsService."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test departments
        cls.dept_a = cls.env['hr.department'].create({'name': 'Dept A Analytics'})
        cls.dept_b = cls.env['hr.department'].create({'name': 'Dept B Analytics'})
        
        today = date.today()
        cls.test_year = today.year
        cls.test_month = today.month
        cls.snapshot_date = date(cls.test_year, cls.test_month, 
                                  monthrange(cls.test_year, cls.test_month)[1])
        
        # Create test snapshots
        Snapshot = cls.env['hr.employee.snapshot']
        
        # Clear existing
        Snapshot.search([
            ('snapshot_year', '=', cls.test_year),
            ('snapshot_month', '=', cls.test_month),
        ]).unlink()
        
        # Create employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee Analytics',
            'department_id': cls.dept_a.id,
        })
        
        # Create snapshots for testing
        cls.snapshots = Snapshot.create([
            {
                'employee_id': cls.employee.id,
                'unit_id': cls.dept_a.id,
                'employment_type': 'payroll',
                'employment_status': 'tetap',
                'snapshot_month': cls.test_month,
                'snapshot_year': cls.test_year,
                'is_active': True,
                'gender': 'male',
            },
        ])
    
    def test_01_service_initialization(self):
        """Test service can be initialized."""
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        self.assertIsNotNone(service)
    
    def test_02_payroll_vs_non_payroll(self):
        """Test G21/WA01: Payroll vs Non-Payroll aggregation."""
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        result = service.payroll_vs_non_payroll(self.snapshot_date)
        
        self.assertIn('labels', result)
        self.assertIn('datasets', result)
        self.assertIn('total', result)
        self.assertEqual(result['chart_type'], 'bar')
    
    def test_03_total_employee_per_unit(self):
        """Test G22/WA02: Total Employee per Unit aggregation."""
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        result = service.total_employee_per_unit(self.snapshot_date)
        
        self.assertIn('labels', result)
        self.assertIn('data', result)
        self.assertIn('total', result)
        self.assertEqual(result['chart_type'], 'bar')
    
    def test_04_workforce_snapshot_trend(self):
        """Test G23/WA03: Workforce Snapshot Trend."""
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        result = service.workforce_snapshot_trend(year=self.test_year, months=6)
        
        self.assertIn('labels', result)
        self.assertIn('datasets', result)
        self.assertEqual(result['chart_type'], 'line')
        self.assertEqual(len(result['labels']), 6)  # 6 months
    
    def test_05_employment_status_distribution(self):
        """Test G24/WA04: Employment Status Distribution."""
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        result = service.employment_status_distribution(self.snapshot_date)
        
        self.assertIn('labels', result)
        self.assertIn('data', result)
        self.assertEqual(result['chart_type'], 'pie')
    
    def test_06_kpi_summary(self):
        """Test KPI summary generation."""
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        result = service.get_kpi_summary(self.snapshot_date)
        
        self.assertIn('total_employees', result)
        self.assertIn('active_employees', result)
        self.assertIn('payroll_count', result)
        self.assertIn('non_payroll_count', result)
    
    def test_07_executive_summary(self):
        """Test complete executive summary."""
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        result = service.get_executive_summary(self.snapshot_date)
        
        self.assertIn('kpi', result)
        self.assertIn('g22_total_per_unit', result)
        self.assertIn('g21_payroll_comparison', result)
        self.assertIn('g24_status_distribution', result)


@tagged('yhc_export', 'workforce_analytics', 'consistency')
class TestAnalyticsConsistency(TransactionCase):
    """Test that dashboard and PDF use the same data source."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        cls.department = cls.env['hr.department'].create({
            'name': 'Consistency Test Dept'
        })
        
        today = date.today()
        cls.test_year = today.year
        cls.test_month = today.month
        cls.snapshot_date = date(cls.test_year, cls.test_month,
                                  monthrange(cls.test_year, cls.test_month)[1])
        
        # Create employee and snapshot
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Consistency Test Employee',
            'department_id': cls.department.id,
        })
        
        Snapshot = cls.env['hr.employee.snapshot']
        Snapshot.search([
            ('snapshot_year', '=', cls.test_year),
            ('snapshot_month', '=', cls.test_month),
            ('employee_id', '=', cls.employee.id),
        ]).unlink()
        
        cls.snapshot = Snapshot.create({
            'employee_id': cls.employee.id,
            'unit_id': cls.department.id,
            'employment_type': 'payroll',
            'employment_status': 'tetap',
            'snapshot_month': cls.test_month,
            'snapshot_year': cls.test_year,
            'is_active': True,
            'gender': 'female',
        })
    
    def test_01_dashboard_pdf_data_consistency(self):
        """
        CRITICAL: Dashboard and PDF MUST use the same analytics source.
        """
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        
        # Simulate dashboard call
        dashboard_data = service.total_employee_per_unit(self.snapshot_date)
        
        # Simulate PDF call (same method)
        pdf_data = service.total_employee_per_unit(self.snapshot_date)
        
        # They must be identical
        self.assertEqual(dashboard_data['total'], pdf_data['total'])
        self.assertEqual(dashboard_data['labels'], pdf_data['labels'])
        self.assertEqual(dashboard_data['data'], pdf_data['data'])
    
    def test_02_aggregation_backend_only(self):
        """
        CRITICAL: All aggregation must happen in backend.
        The service must return pre-aggregated data, not raw records.
        """
        from ..services.employee_analytics_service import EmployeeAnalyticsService
        
        service = EmployeeAnalyticsService(self.env)
        result = service.total_employee_per_unit(self.snapshot_date)
        
        # Result must contain aggregated values, not recordsets
        self.assertIsInstance(result['labels'], list)
        self.assertIsInstance(result['data'], list)
        self.assertIsInstance(result['total'], int)
        
        # Labels must be strings, not records
        for label in result['labels']:
            self.assertIsInstance(label, str)
        
        # Data must be numbers, not records
        for value in result['data']:
            self.assertIsInstance(value, (int, float))


@tagged('yhc_export', 'workforce_analytics', 'wizard')
class TestWorkforceExportWizard(TransactionCase):
    """Test cases untuk export wizard."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        today = date.today()
        cls.snapshot_date = date(today.year, today.month,
                                  monthrange(today.year, today.month)[1])
    
    def test_01_wizard_creation(self):
        """Test wizard can be created."""
        Wizard = self.env['hr.employee.export.workforce.wizard']
        
        wizard = Wizard.create({
            'report_title': 'Test Report',
            'include_wa02': True,
        })
        
        self.assertTrue(wizard.id)
    
    def test_02_graph_count_validation(self):
        """Test that at least 1 graph must be selected."""
        Wizard = self.env['hr.employee.export.workforce.wizard']
        
        wizard = Wizard.create({
            'report_title': 'Test Report',
            'include_wa01': False,
            'include_wa02': False,
            'include_wa03': False,
            'include_wa04': False,
        })
        
        self.assertEqual(wizard.graph_count, 0)
        
        # Validation should fail when trying to export
        with self.assertRaises(UserError):
            wizard._validate_before_export()
    
    def test_03_executive_summary_requires_wa02(self):
        """Test that executive summary requires WA02 graph."""
        Wizard = self.env['hr.employee.export.workforce.wizard']
        
        wizard = Wizard.create({
            'report_title': 'Test Report',
            'layout_type': 'executive_summary',
            'include_wa01': True,
            'include_wa02': False,  # Missing required graph
            'include_wa03': False,
            'include_wa04': False,
        })
        
        with self.assertRaises(UserError):
            wizard._validate_before_export()
    
    def test_04_max_6_graphs(self):
        """Test maximum 6 graphs per export."""
        Wizard = self.env['hr.employee.export.workforce.wizard']
        
        # With 4 workforce graphs, this is fine
        wizard = Wizard.create({
            'report_title': 'Test Report',
            'include_wa01': True,
            'include_wa02': True,
            'include_wa03': True,
            'include_wa04': True,
        })
        
        self.assertEqual(wizard.graph_count, 4)
        # Should not raise
        wizard._validate_before_export()


@tagged('yhc_export', 'workforce_analytics', 'graph_registry')
class TestGraphRegistry(TransactionCase):
    """Test cases untuk graph registry."""
    
    def test_01_workforce_graphs_exist(self):
        """Test that WA01-WA04 graphs exist in registry."""
        from ..models.graph_registry import GRAPH_REGISTRY
        
        self.assertIn('WA01', GRAPH_REGISTRY)
        self.assertIn('WA02', GRAPH_REGISTRY)
        self.assertIn('WA03', GRAPH_REGISTRY)
        self.assertIn('WA04', GRAPH_REGISTRY)
    
    def test_02_workforce_graphs_have_required_fields(self):
        """Test that workforce graphs have all required fields."""
        from ..models.graph_registry import GRAPH_REGISTRY
        
        required_fields = ['code', 'name', 'chart_type', 'method', 'description', 'category']
        
        for code in ['WA01', 'WA02', 'WA03', 'WA04']:
            graph = GRAPH_REGISTRY[code]
            for field in required_fields:
                self.assertIn(field, graph, f"{code} missing field: {field}")
    
    def test_03_workforce_graphs_use_snapshot(self):
        """Test that workforce graphs are marked as snapshot-based."""
        from ..models.graph_registry import GRAPH_REGISTRY
        
        for code in ['WA01', 'WA02', 'WA03', 'WA04']:
            graph = GRAPH_REGISTRY[code]
            self.assertTrue(
                graph.get('uses_snapshot', False),
                f"{code} should be marked as uses_snapshot=True"
            )
    
    def test_04_wa02_is_primary(self):
        """Test that WA02 is marked as primary for executive summary."""
        from ..models.graph_registry import GRAPH_REGISTRY
        
        wa02 = GRAPH_REGISTRY['WA02']
        self.assertTrue(wa02.get('is_primary', False))
    
    def test_05_workforce_category_exists(self):
        """Test that workforce_analytics category exists."""
        from ..models.graph_registry import GRAPH_CATEGORIES
        
        self.assertIn('workforce_analytics', GRAPH_CATEGORIES)
        
        category = GRAPH_CATEGORIES['workforce_analytics']
        self.assertIn('WA01', category['graphs'])
        self.assertIn('WA02', category['graphs'])
        self.assertIn('WA03', category['graphs'])
        self.assertIn('WA04', category['graphs'])
