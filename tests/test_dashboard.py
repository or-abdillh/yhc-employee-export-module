# -*- coding: utf-8 -*-

"""
Unit Tests untuk Dashboard Analytics

Test cases untuk model hr.employee.analytics dan dashboard data
"""

from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'yhc_export')
class TestDashboardAnalytics(TransactionCase):
    """Test cases untuk dashboard analytics"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test departments
        cls.dept_it = cls.env['hr.department'].create({
            'name': 'IT Department',
        })
        cls.dept_hr = cls.env['hr.department'].create({
            'name': 'HR Department',
        })
        
        # Create test employees with various attributes
        today = date.today()
        
        cls.employees = cls.env['hr.employee'].create([
            {
                'name': 'Employee IT 1',
                'department_id': cls.dept_it.id,
                'gender': 'male',
                'birthday': date(1990, 5, 15),
                'marital': 'married',
            },
            {
                'name': 'Employee IT 2',
                'department_id': cls.dept_it.id,
                'gender': 'female',
                'birthday': date(1985, 8, 20),
                'marital': 'single',
            },
            {
                'name': 'Employee HR 1',
                'department_id': cls.dept_hr.id,
                'gender': 'male',
                'birthday': date(1995, 12, 1),
                'marital': 'married',
            },
            {
                'name': 'Employee HR 2',
                'department_id': cls.dept_hr.id,
                'gender': 'female',
                'birthday': date(1988, 3, 10),
                'marital': 'single',
            },
            {
                'name': 'Inactive Employee',
                'department_id': cls.dept_hr.id,
                'gender': 'male',
                'active': False,
            },
        ])
    
    def test_get_dashboard_data(self):
        """Test get_dashboard_data returns all required keys"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data()
        
        # Check all required keys exist
        required_keys = [
            'kpi', 'gender', 'age_groups', 'departments',
            'education', 'employment_type', 'service_length',
            'bpjs', 'religion', 'marital'
        ]
        
        for key in required_keys:
            self.assertIn(key, data, f"Missing key: {key}")
    
    def test_kpi_data(self):
        """Test KPI data calculations"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data()
        kpi = data['kpi']
        
        # Total should include inactive
        self.assertEqual(kpi['totalEmployees'], 5)
        
        # Active should exclude inactive
        self.assertEqual(kpi['activeEmployees'], 4)
        
        # Inactive count
        self.assertEqual(kpi['inactiveEmployees'], 1)
        
        # Gender counts
        self.assertEqual(kpi['maleCount'], 2)  # 2 active males
        self.assertEqual(kpi['femaleCount'], 2)  # 2 active females
    
    def test_gender_data(self):
        """Test gender distribution data"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data()
        gender = data['gender']
        
        self.assertEqual(gender['male'], 2)
        self.assertEqual(gender['female'], 2)
    
    def test_department_data(self):
        """Test department distribution data"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data()
        departments = data['departments']
        
        self.assertIn('IT Department', departments)
        self.assertIn('HR Department', departments)
        self.assertEqual(departments['IT Department'], 2)
        self.assertEqual(departments['HR Department'], 2)  # excluding inactive
    
    def test_age_groups_data(self):
        """Test age groups distribution"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data()
        age_groups = data['age_groups']
        
        # Check all age group keys exist
        expected_groups = ['< 25', '25-34', '35-44', '45-54', '55+']
        for group in expected_groups:
            self.assertIn(group, age_groups)
    
    def test_marital_data(self):
        """Test marital status distribution"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data()
        marital = data['marital']
        
        self.assertIn('Menikah', marital)
        self.assertIn('Belum Menikah', marital)
        self.assertEqual(marital['Menikah'], 2)
        self.assertEqual(marital['Belum Menikah'], 2)
    
    def test_filter_by_department(self):
        """Test filtering by department"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data(department_id=self.dept_it.id)
        
        # Should only include IT department employees
        self.assertEqual(data['kpi']['activeEmployees'], 2)
        self.assertEqual(data['departments'].get('IT Department', 0), 2)
        self.assertNotIn('HR Department', data['departments'])
    
    def test_bpjs_data(self):
        """Test BPJS registration data"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data()
        bpjs = data['bpjs']
        
        # Check structure
        self.assertIn('kesehatan', bpjs)
        self.assertIn('ketenagakerjaan', bpjs)
        self.assertIn('registered', bpjs['kesehatan'])
        self.assertIn('not_registered', bpjs['kesehatan'])
    
    def test_service_length_data(self):
        """Test service length distribution"""
        Analytics = self.env['hr.employee.analytics']
        
        data = Analytics.get_dashboard_data()
        service_length = data['service_length']
        
        # Check all service length keys exist
        expected_keys = ['< 1 Tahun', '1-3 Tahun', '3-5 Tahun', '5-10 Tahun', '> 10 Tahun']
        for key in expected_keys:
            self.assertIn(key, service_length)


@tagged('post_install', '-at_install', 'yhc_export')
class TestAuditLog(TransactionCase):
    """Test cases untuk audit log"""
    
    def test_create_audit_log(self):
        """Test creating audit log"""
        log = self.env['hr.employee.export.audit.log'].create({
            'export_type': 'xlsx',
            'record_count': 100,
            'status': 'success',
        })
        
        self.assertTrue(log.id)
        self.assertEqual(log.export_type, 'xlsx')
        self.assertEqual(log.record_count, 100)
        self.assertEqual(log.user_id, self.env.user)
    
    def test_log_export_helper(self):
        """Test log_export helper method"""
        AuditLog = self.env['hr.employee.export.audit.log']
        
        log = AuditLog.log_export(
            export_type='csv',
            record_count=50,
            status='success',
            include_sensitive=True,
        )
        
        self.assertTrue(log.id)
        self.assertEqual(log.export_type, 'csv')
        self.assertTrue(log.include_sensitive)
    
    def test_get_user_export_history(self):
        """Test get_user_export_history method"""
        AuditLog = self.env['hr.employee.export.audit.log']
        
        # Create some logs
        for i in range(5):
            AuditLog.create({
                'export_type': 'xlsx',
                'record_count': 10 * (i + 1),
                'status': 'success',
            })
        
        history = AuditLog.get_user_export_history()
        
        self.assertEqual(len(history), 5)
        self.assertIsInstance(history[0], dict)
        self.assertIn('export_type', history[0])
    
    def test_get_export_statistics(self):
        """Test get_export_statistics method"""
        AuditLog = self.env['hr.employee.export.audit.log']
        
        # Create logs with different types
        AuditLog.create({'export_type': 'xlsx', 'record_count': 100, 'status': 'success'})
        AuditLog.create({'export_type': 'csv', 'record_count': 50, 'status': 'success'})
        AuditLog.create({'export_type': 'xlsx', 'record_count': 75, 'status': 'failed'})
        
        stats = AuditLog.get_export_statistics()
        
        self.assertEqual(stats['total_exports'], 3)
        self.assertEqual(stats['total_records'], 225)
        self.assertIn('by_type', stats)
        self.assertIn('by_status', stats)
