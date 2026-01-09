# -*- coding: utf-8 -*-

"""
Unit Tests untuk Export Services

Test cases untuk semua export services (XLSX, CSV, PDF, JSON)
"""

import base64
import json
from io import BytesIO

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'yhc_export')
class TestExportServices(TransactionCase):
    """Test cases untuk export services"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test department
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Export Dept',
        })
        
        # Create test employees with various data
        cls.employees = cls.env['hr.employee'].create([
            {
                'name': 'John Doe',
                'department_id': cls.department.id,
                'gender': 'male',
                'birthday': '1990-05-15',
                'marital': 'married',
            },
            {
                'name': 'Jane Smith',
                'department_id': cls.department.id,
                'gender': 'female',
                'birthday': '1985-08-20',
                'marital': 'single',
            },
            {
                'name': 'Bob Wilson',
                'department_id': cls.department.id,
                'gender': 'male',
                'birthday': '1995-12-01',
                'marital': 'single',
            },
        ])
        
        # Define test fields
        cls.test_fields = ['name', 'department_id.name', 'gender', 'birthday', 'marital']
        cls.test_headers = ['Nama', 'Departemen', 'Gender', 'Tanggal Lahir', 'Status']
    
    def test_export_base_format_value(self):
        """Test format_value method in base service"""
        from ..services.export_base import EmployeeExportBase
        
        service = EmployeeExportBase(self.env)
        
        # Test None/False
        self.assertEqual(service.format_value(None), '-')
        self.assertEqual(service.format_value(False), '-')
        
        # Test boolean
        self.assertEqual(service.format_value(True), 'Ya')
        self.assertEqual(service.format_value(False), '-')  # False treated as empty
        
        # Test date
        from datetime import date
        test_date = date(2024, 1, 15)
        self.assertEqual(service.format_value(test_date), '15/01/2024')
        
        # Test float
        self.assertEqual(service.format_value(100.0), '100')
        self.assertEqual(service.format_value(99.99), '99.99')
        
        # Test list
        self.assertEqual(service.format_value(['a', 'b', 'c']), 'a, b, c')
    
    def test_export_base_generate_filename(self):
        """Test generate_filename method"""
        from ..services.export_base import EmployeeExportBase
        
        service = EmployeeExportBase(self.env)
        
        filename = service.generate_filename('test', 'xlsx')
        
        self.assertTrue(filename.startswith('test_'))
        self.assertTrue(filename.endswith('.xlsx'))
    
    def test_export_xlsx_basic(self):
        """Test basic XLSX export"""
        from ..services.export_xlsx import EmployeeExportXlsx
        
        service = EmployeeExportXlsx(self.env)
        
        result = service.export(
            employees=self.employees,
            fields=self.test_fields,
            headers=self.test_headers,
            filename='test_export.xlsx'
        )
        
        self.assertIn('file', result)
        self.assertIn('filename', result)
        self.assertTrue(result['filename'].endswith('.xlsx'))
        
        # Verify it's valid base64
        try:
            decoded = base64.b64decode(result['file'])
            self.assertTrue(len(decoded) > 0)
        except Exception:
            self.fail("Invalid base64 content")
    
    def test_export_csv_basic(self):
        """Test basic CSV export"""
        from ..services.export_csv import EmployeeExportCsv
        
        service = EmployeeExportCsv(self.env)
        
        result = service.export(
            employees=self.employees,
            fields=self.test_fields,
            headers=self.test_headers,
            filename='test_export.csv'
        )
        
        self.assertIn('file', result)
        self.assertIn('filename', result)
        self.assertTrue(result['filename'].endswith('.csv'))
        
        # Verify CSV content
        decoded = base64.b64decode(result['file']).decode('utf-8-sig')
        lines = decoded.strip().split('\n')
        
        # Should have header + 3 employees
        self.assertEqual(len(lines), 4)
        
        # Check header
        self.assertIn('Nama', lines[0])
    
    def test_export_json_basic(self):
        """Test basic JSON export"""
        from ..services.export_json import EmployeeExportJson
        
        service = EmployeeExportJson(self.env)
        
        result = service.export(
            employees=self.employees,
            fields=self.test_fields,
            headers=self.test_headers,
            filename='test_export.json'
        )
        
        self.assertIn('file', result)
        self.assertTrue(result['filename'].endswith('.json'))
        
        # Verify JSON content
        decoded = base64.b64decode(result['file']).decode('utf-8')
        data = json.loads(decoded)
        
        self.assertIn('data', data)
        self.assertEqual(len(data['data']), 3)
    
    def test_export_empty_employees(self):
        """Test export with no employees"""
        from ..services.export_xlsx import EmployeeExportXlsx
        
        service = EmployeeExportXlsx(self.env)
        
        with self.assertRaises(UserError):
            service.export(
                employees=self.env['hr.employee'].browse(),
                fields=self.test_fields,
                headers=self.test_headers,
            )
    
    def test_export_with_custom_date_format(self):
        """Test export with custom date format"""
        from ..services.export_csv import EmployeeExportCsv
        
        service = EmployeeExportCsv(self.env)
        service.set_date_format('%Y-%m-%d')
        
        result = service.export(
            employees=self.employees,
            fields=['name', 'birthday'],
            headers=['Nama', 'Tanggal Lahir'],
        )
        
        decoded = base64.b64decode(result['file']).decode('utf-8-sig')
        
        # Should contain date in YYYY-MM-DD format
        self.assertIn('1990-05-15', decoded)
    
    def test_export_relational_field(self):
        """Test export with relational fields"""
        from ..services.export_csv import EmployeeExportCsv
        
        service = EmployeeExportCsv(self.env)
        
        result = service.export(
            employees=self.employees,
            fields=['name', 'department_id.name'],
            headers=['Nama', 'Departemen'],
        )
        
        decoded = base64.b64decode(result['file']).decode('utf-8-sig')
        
        self.assertIn('Test Export Dept', decoded)


@tagged('post_install', '-at_install', 'yhc_export')
class TestExportWizard(TransactionCase):
    """Test cases untuk export wizard"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.department = cls.env['hr.department'].create({
            'name': 'Wizard Test Dept',
        })
        
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Wizard Test Employee',
            'department_id': cls.department.id,
        })
    
    def test_wizard_create(self):
        """Test creating export wizard"""
        wizard = self.env['hr.employee.export.wizard'].create({
            'export_format': 'xlsx',
        })
        
        self.assertTrue(wizard.id)
        self.assertEqual(wizard.export_format, 'xlsx')
    
    def test_wizard_default_values(self):
        """Test wizard default values"""
        wizard = self.env['hr.employee.export.wizard'].create({})
        
        self.assertEqual(wizard.export_format, 'xlsx')
        self.assertTrue(wizard.include_identity)
        self.assertTrue(wizard.include_employment)
    
    def test_wizard_action_export(self):
        """Test wizard export action"""
        wizard = self.env['hr.employee.export.wizard'].create({
            'export_format': 'csv',
            'department_ids': [(6, 0, [self.department.id])],
        })
        
        result = wizard.action_export()
        
        # Should return download action
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
    
    def test_wizard_preview(self):
        """Test wizard preview action"""
        wizard = self.env['hr.employee.export.wizard'].create({
            'department_ids': [(6, 0, [self.department.id])],
        })
        
        result = wizard.action_preview()
        
        # Should return action to show preview
        self.assertIsNotNone(result)
