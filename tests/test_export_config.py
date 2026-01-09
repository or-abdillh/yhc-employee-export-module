# -*- coding: utf-8 -*-

"""
Unit Tests untuk Model Export Config

Test cases untuk model hr.employee.export.config
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, AccessError


@tagged('post_install', '-at_install', 'yhc_export')
class TestExportConfig(TransactionCase):
    """Test cases untuk hr.employee.export.config"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test user with export user group
        cls.export_user = cls.env['res.users'].create({
            'name': 'Test Export User',
            'login': 'test_export_user',
            'email': 'export_user@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_user').id,
            ])],
        })
        
        # Create test user with export officer group
        cls.export_officer = cls.env['res.users'].create({
            'name': 'Test Export Officer',
            'login': 'test_export_officer',
            'email': 'export_officer@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_officer').id,
            ])],
        })
        
        # Create test user with export manager group
        cls.export_manager = cls.env['res.users'].create({
            'name': 'Test Export Manager',
            'login': 'test_export_manager',
            'email': 'export_manager@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_manager').id,
            ])],
        })
        
        # Create test department
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Department',
        })
        
        # Create test employees
        cls.employees = cls.env['hr.employee'].create([
            {
                'name': 'Employee 1',
                'department_id': cls.department.id,
                'gender': 'male',
            },
            {
                'name': 'Employee 2',
                'department_id': cls.department.id,
                'gender': 'female',
            },
        ])
    
    def test_create_export_config(self):
        """Test creating export config"""
        config = self.env['hr.employee.export.config'].create({
            'name': 'Test Config',
            'export_format': 'xlsx',
            'department_ids': [(6, 0, [self.department.id])],
        })
        
        self.assertTrue(config.id)
        self.assertEqual(config.name, 'Test Config')
        self.assertEqual(config.export_format, 'xlsx')
    
    def test_export_config_default_values(self):
        """Test default values for export config"""
        config = self.env['hr.employee.export.config'].create({
            'name': 'Default Test',
        })
        
        self.assertEqual(config.export_format, 'xlsx')
        self.assertTrue(config.active)
    
    def test_export_config_copy(self):
        """Test copying export config"""
        config = self.env['hr.employee.export.config'].create({
            'name': 'Original Config',
            'export_format': 'csv',
        })
        
        config_copy = config.copy()
        
        self.assertIn('(Copy)', config_copy.name)
        self.assertEqual(config_copy.export_format, 'csv')
    
    def test_export_config_access_user(self):
        """Test access rights for export user"""
        Config = self.env['hr.employee.export.config'].with_user(self.export_user)
        
        # User should be able to read
        configs = Config.search([])
        self.assertIsNotNone(configs)
    
    def test_export_config_access_officer(self):
        """Test access rights for export officer"""
        Config = self.env['hr.employee.export.config'].with_user(self.export_officer)
        
        # Officer should be able to create
        config = Config.create({
            'name': 'Officer Config',
            'export_format': 'xlsx',
        })
        
        self.assertTrue(config.id)
    
    def test_export_config_access_manager(self):
        """Test access rights for export manager"""
        Config = self.env['hr.employee.export.config'].with_user(self.export_manager)
        
        # Manager should have full access
        config = Config.create({
            'name': 'Manager Config',
            'export_format': 'pdf',
        })
        
        self.assertTrue(config.id)
        
        # Manager should be able to delete
        config.unlink()
    
    def test_get_selected_fields(self):
        """Test get_selected_fields method"""
        config = self.env['hr.employee.export.config'].create({
            'name': 'Field Test Config',
            'include_identity': True,
            'include_employment': True,
            'include_bpjs': False,
        })
        
        fields = config.get_selected_fields()
        
        self.assertIsInstance(fields, list)
        # Should include identity and employment fields
        self.assertIn('name', fields)
    
    def test_get_filtered_employees(self):
        """Test get_filtered_employees method"""
        config = self.env['hr.employee.export.config'].create({
            'name': 'Filter Test',
            'department_ids': [(6, 0, [self.department.id])],
            'include_inactive': False,
        })
        
        employees = config.get_filtered_employees()
        
        self.assertEqual(len(employees), 2)
        self.assertIn(self.employees[0], employees)
