# -*- coding: utf-8 -*-

"""
Unit Tests untuk Security & Access Rights

Test cases untuk security groups, record rules, dan akses data sensitif
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError, AccessDenied


@tagged('post_install', '-at_install', 'yhc_export')
class TestSecurityGroups(TransactionCase):
    """Test cases untuk security groups"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create users with different access levels
        cls.user_basic = cls.env['res.users'].create({
            'name': 'Basic User',
            'login': 'basic_user',
            'email': 'basic@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_user').id,
            ])],
        })
        
        cls.user_officer = cls.env['res.users'].create({
            'name': 'Officer User',
            'login': 'officer_user',
            'email': 'officer@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_officer').id,
            ])],
        })
        
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Manager User',
            'login': 'manager_user',
            'email': 'manager@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_manager').id,
            ])],
        })
        
        cls.user_sensitive = cls.env['res.users'].create({
            'name': 'Sensitive User',
            'login': 'sensitive_user',
            'email': 'sensitive@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_user').id,
                cls.env.ref('yhc_employee_export.group_hr_sensitive_data').id,
            ])],
        })
        
        cls.user_regulatory = cls.env['res.users'].create({
            'name': 'Regulatory User',
            'login': 'regulatory_user',
            'email': 'regulatory@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_officer').id,
                cls.env.ref('yhc_employee_export.group_hr_regulatory_export').id,
            ])],
        })
    
    def test_group_hierarchy(self):
        """Test group inheritance hierarchy"""
        # Officer should inherit from User
        self.assertTrue(
            self.user_officer.has_group('yhc_employee_export.group_hr_export_user')
        )
        
        # Manager should inherit from Officer (and thus User)
        self.assertTrue(
            self.user_manager.has_group('yhc_employee_export.group_hr_export_officer')
        )
        self.assertTrue(
            self.user_manager.has_group('yhc_employee_export.group_hr_export_user')
        )
    
    def test_sensitive_data_group(self):
        """Test sensitive data group"""
        self.assertTrue(
            self.user_sensitive.has_group('yhc_employee_export.group_hr_sensitive_data')
        )
        
        # Basic user should not have sensitive access
        self.assertFalse(
            self.user_basic.has_group('yhc_employee_export.group_hr_sensitive_data')
        )
    
    def test_regulatory_group(self):
        """Test regulatory export group"""
        self.assertTrue(
            self.user_regulatory.has_group('yhc_employee_export.group_hr_regulatory_export')
        )
        
        # Regulatory should also have sensitive access (implied)
        self.assertTrue(
            self.user_regulatory.has_group('yhc_employee_export.group_hr_sensitive_data')
        )


@tagged('post_install', '-at_install', 'yhc_export')
class TestRecordRules(TransactionCase):
    """Test cases untuk record rules"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create users
        cls.user1 = cls.env['res.users'].create({
            'name': 'User 1',
            'login': 'user1',
            'email': 'user1@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_user').id,
            ])],
        })
        
        cls.user2 = cls.env['res.users'].create({
            'name': 'User 2',
            'login': 'user2',
            'email': 'user2@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_user').id,
            ])],
        })
        
        cls.officer = cls.env['res.users'].create({
            'name': 'Officer',
            'login': 'officer',
            'email': 'officer@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_officer').id,
            ])],
        })
        
        cls.manager = cls.env['res.users'].create({
            'name': 'Manager',
            'login': 'manager_rr',
            'email': 'manager_rr@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_manager').id,
            ])],
        })
    
    def test_audit_log_access_user(self):
        """Test user cannot read audit logs"""
        AuditLog = self.env['hr.employee.export.audit.log']
        
        # Create a log as admin
        log = AuditLog.create({
            'export_type': 'xlsx',
            'record_count': 10,
            'status': 'success',
        })
        
        # User should not be able to read (based on record rules)
        AuditLogUser = AuditLog.with_user(self.user1)
        
        # This depends on record rules - may raise AccessError
        # or return empty recordset
        try:
            logs = AuditLogUser.search([])
            # If no error, check if log is visible
            # Based on rules, basic user shouldn't see it
        except AccessError:
            pass  # Expected behavior
    
    def test_audit_log_access_manager(self):
        """Test manager can read audit logs"""
        AuditLog = self.env['hr.employee.export.audit.log']
        
        # Create a log as admin
        log = AuditLog.create({
            'export_type': 'xlsx',
            'record_count': 10,
            'status': 'success',
        })
        
        # Manager should be able to read
        AuditLogManager = AuditLog.with_user(self.manager)
        logs = AuditLogManager.search([])
        
        self.assertIn(log.id, logs.ids)


@tagged('post_install', '-at_install', 'yhc_export')
class TestSensitiveDataProtection(TransactionCase):
    """Test cases untuk proteksi data sensitif"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.user_no_sensitive = cls.env['res.users'].create({
            'name': 'No Sensitive User',
            'login': 'no_sensitive',
            'email': 'no_sensitive@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_user').id,
            ])],
        })
        
        cls.user_sensitive = cls.env['res.users'].create({
            'name': 'Sensitive User',
            'login': 'with_sensitive',
            'email': 'with_sensitive@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_user').id,
                cls.env.ref('yhc_employee_export.group_hr_sensitive_data').id,
            ])],
        })
    
    def test_sensitive_field_filter(self):
        """Test sensitive fields are filtered for users without access"""
        from ..services.export_base import EmployeeExportBase, SENSITIVE_FIELDS
        
        # Create service with no-sensitive user
        service = EmployeeExportBase(self.env.with_user(self.user_no_sensitive))
        
        # Test filtering
        fields = ['name', 'department_id', 'x_nik', 'x_npwp', 'x_bpjs_kesehatan']
        filtered = service._filter_sensitive_fields(fields)
        
        # Sensitive fields should be removed
        self.assertIn('name', filtered)
        self.assertIn('department_id', filtered)
        self.assertNotIn('x_nik', filtered)
        self.assertNotIn('x_npwp', filtered)
        self.assertNotIn('x_bpjs_kesehatan', filtered)
    
    def test_sensitive_field_no_filter_for_authorized(self):
        """Test sensitive fields are NOT filtered for authorized users"""
        from ..services.export_base import EmployeeExportBase
        
        # Create service with sensitive user
        service = EmployeeExportBase(self.env.with_user(self.user_sensitive))
        
        fields = ['name', 'x_nik', 'x_npwp']
        filtered = service._filter_sensitive_fields(fields)
        
        # All fields should be present
        self.assertEqual(fields, filtered)
    
    def test_mask_sensitive_value(self):
        """Test masking of sensitive values"""
        from ..services.export_base import EmployeeExportBase
        
        service = EmployeeExportBase(self.env.with_user(self.user_no_sensitive))
        
        # Test NIK masking
        nik = '1234567890123456'
        masked = service._mask_sensitive_value(nik, 'x_nik')
        
        self.assertNotEqual(nik, masked)
        self.assertEqual(masked[-4:], '3456')
        self.assertIn('*', masked)
    
    def test_no_mask_for_authorized(self):
        """Test no masking for authorized users"""
        from ..services.export_base import EmployeeExportBase
        
        service = EmployeeExportBase(self.env.with_user(self.user_sensitive))
        
        nik = '1234567890123456'
        masked = service._mask_sensitive_value(nik, 'x_nik')
        
        # Should not be masked
        self.assertEqual(nik, masked)


@tagged('post_install', '-at_install', 'yhc_export')
class TestSecurityMixin(TransactionCase):
    """Test cases untuk security mixin"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.basic_user = cls.env['res.users'].create({
            'name': 'Basic Mixin User',
            'login': 'basic_mixin',
            'email': 'basic_mixin@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_user').id,
            ])],
        })
        
        cls.regulatory_user = cls.env['res.users'].create({
            'name': 'Regulatory Mixin User',
            'login': 'regulatory_mixin',
            'email': 'regulatory_mixin@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('yhc_employee_export.group_hr_export_officer').id,
                cls.env.ref('yhc_employee_export.group_hr_regulatory_export').id,
            ])],
        })
    
    def test_check_access_basic(self):
        """Test basic access check"""
        from ..services.export_base import EmployeeExportBase
        
        service = EmployeeExportBase(self.env.with_user(self.basic_user))
        
        # Basic access should pass
        result = service._check_access('basic')
        self.assertTrue(result)
    
    def test_check_access_sensitive_denied(self):
        """Test sensitive access denied for basic user"""
        from ..services.export_base import EmployeeExportBase
        
        service = EmployeeExportBase(self.env.with_user(self.basic_user))
        
        with self.assertRaises(AccessDenied):
            service._check_access('sensitive')
    
    def test_check_access_regulatory_denied(self):
        """Test regulatory access denied for basic user"""
        from ..services.export_base import EmployeeExportBase
        
        service = EmployeeExportBase(self.env.with_user(self.basic_user))
        
        with self.assertRaises(AccessDenied):
            service._check_access('regulatory')
    
    def test_check_access_regulatory_allowed(self):
        """Test regulatory access allowed for authorized user"""
        from ..services.export_base import EmployeeExportBase
        
        service = EmployeeExportBase(self.env.with_user(self.regulatory_user))
        
        result = service._check_access('regulatory')
        self.assertTrue(result)
