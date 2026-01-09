# -*- coding: utf-8 -*-
"""
Export Service JSON untuk yhc_employee_export.

Service ini menangani export data karyawan ke format JSON
dengan fitur nested structure, pretty print, dan ISO date formatting.
"""

import json
from datetime import datetime, date
import logging

from .export_base import EmployeeExportBase, FIELD_MAPPINGS

_logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder untuk handle datetime objects."""
    
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class EmployeeExportJson(EmployeeExportBase):
    """
    Service untuk export data karyawan ke format JSON.
    
    Features:
    - Nested structure untuk data relasional
    - Pretty print dengan indentation
    - ISO 8601 date formatting
    - Metadata export
    """
    
    def __init__(self, env):
        """Initialize JSON export service."""
        super().__init__(env)
        self.pretty_print = True
        self.indent = 2
    
    def export(self, employees, categories=None, config=None, pretty=True):
        """
        Export data karyawan ke format JSON.
        
        Args:
            employees: hr.employee recordset
            categories (list): List kategori yang akan di-export
            config: hr.employee.export.config (optional)
            pretty (bool): Pretty print dengan indentation
            
        Returns:
            tuple: (bytes, filename)
        """
        self.validate_employees(employees)
        
        if categories is None:
            categories = ['identity', 'employment']
        
        self.pretty_print = pretty
        
        # Build JSON structure
        export_data = {
            'metadata': self._build_metadata(employees, categories),
            'employees': self._build_employees_data(employees, categories),
        }
        
        # Convert to JSON string
        if self.pretty_print:
            json_str = json.dumps(export_data, cls=DateTimeEncoder, 
                                  indent=self.indent, ensure_ascii=False)
        else:
            json_str = json.dumps(export_data, cls=DateTimeEncoder, 
                                  ensure_ascii=False)
        
        # Convert to bytes
        json_bytes = json_str.encode('utf-8')
        
        filename = self.generate_filename('export_karyawan', 'json')
        
        return json_bytes, filename
    
    def _build_metadata(self, employees, categories):
        """
        Build metadata untuk export.
        
        Args:
            employees: hr.employee recordset
            categories (list): List kategori
            
        Returns:
            dict: Metadata
        """
        return {
            'export_date': datetime.now().isoformat(),
            'exported_by': {
                'id': self.env.user.id,
                'name': self.env.user.name,
                'email': self.env.user.email or None,
            },
            'company': {
                'id': self.env.company.id,
                'name': self.env.company.name,
            },
            'total_employees': len(employees),
            'categories_exported': categories,
            'version': '1.0',
        }
    
    def _build_employees_data(self, employees, categories):
        """
        Build data karyawan untuk export.
        
        Args:
            employees: hr.employee recordset
            categories (list): List kategori
            
        Returns:
            list: List of employee data
        """
        employees_data = []
        
        for emp in employees:
            emp_data = self._build_employee_data(emp, categories)
            employees_data.append(emp_data)
        
        return employees_data
    
    def _build_employee_data(self, emp, categories):
        """
        Build data satu karyawan.
        
        Args:
            emp: hr.employee record
            categories (list): List kategori
            
        Returns:
            dict: Employee data
        """
        data = {
            'id': emp.id,
            'nrp': self._get_value(emp, 'nrp'),
            'name': self._get_value(emp, 'name'),
        }
        
        if 'identity' in categories:
            data['identity'] = self._get_identity_data(emp)
        
        if 'employment' in categories:
            data['employment'] = self._get_employment_data(emp)
        
        if 'family' in categories:
            data['family'] = self._get_family_data(emp)
        
        if 'bpjs' in categories:
            data['bpjs'] = self._get_bpjs_data(emp)
        
        if 'education' in categories:
            data['education'] = self._get_education_data(emp)
        
        if 'payroll' in categories:
            data['payroll'] = self._get_payroll_data(emp)
        
        if 'training' in categories:
            data['training'] = self._get_training_data(emp)
        
        if 'reward_punishment' in categories:
            data['reward_punishment'] = self._get_reward_punishment_data(emp)
        
        return data
    
    def _get_value(self, record, field_name):
        """
        Get field value dengan handling None dan konversi.
        
        Args:
            record: Odoo record
            field_name (str): Field name (supports dot notation)
            
        Returns:
            Value atau None
        """
        try:
            value = self.get_field_value(record, field_name)
            
            # Convert recordset to dict or id
            if hasattr(value, '_name'):
                return {'id': value.id, 'name': value.name} if value else None
            
            # Convert date/datetime
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            
            # Convert boolean
            if isinstance(value, bool):
                return value
            
            # Convert to string if needed
            return value if value else None
            
        except Exception:
            return None
    
    def _get_identity_data(self, emp):
        """Get identity data for JSON."""
        return {
            'nik': self._get_value(emp, 'nik'),
            'no_kk': self._get_value(emp, 'no_kk'),
            'gelar': self._get_value(emp, 'gelar'),
            'place_of_birth': self._get_value(emp, 'place_of_birth'),
            'birthday': self._get_value(emp, 'birthday'),
            'age': self._get_value(emp, 'age'),
            'gender': self._get_value(emp, 'gender'),
            'gender_label': self.get_selection_label(emp, 'gender'),
            'religion': self._get_value(emp, 'religion'),
            'religion_label': self.get_selection_label(emp, 'religion'),
            'blood_type': self._get_value(emp, 'blood_type'),
            'status_kawin': self._get_value(emp, 'status_kawin'),
            'alamat_ktp': self._get_value(emp, 'alamat_ktp'),
            'alamat_domisili': self._get_value(emp, 'alamat_domisili'),
        }
    
    def _get_employment_data(self, emp):
        """Get employment data for JSON."""
        return {
            'department': self._get_relation_data(emp, 'department_id'),
            'job': self._get_relation_data(emp, 'job_id'),
            'area_kerja': self._get_relation_data(emp, 'area_kerja_id'),
            'golongan': self._get_relation_data(emp, 'golongan_id'),
            'grade': self._get_relation_data(emp, 'grade_id'),
            'employee_type': self._get_relation_data(emp, 'employee_type_id'),
            'employee_category': self._get_relation_data(emp, 'employee_category_id'),
            'employment_status': self._get_value(emp, 'employment_status'),
            'first_contract_date': self._get_value(emp, 'first_contract_date'),
            'service_length': self._get_value(emp, 'service_length'),
            'work_email': self._get_value(emp, 'work_email'),
            'work_phone': self._get_value(emp, 'work_phone'),
            'mobile_phone': self._get_value(emp, 'mobile_phone'),
        }
    
    def _get_relation_data(self, record, field_name):
        """Get relational field data as dict."""
        try:
            value = getattr(record, field_name, None)
            if value:
                return {
                    'id': value.id,
                    'name': value.name if hasattr(value, 'name') else str(value),
                }
            return None
        except Exception:
            return None
    
    def _get_family_data(self, emp):
        """Get family data for JSON."""
        children = []
        if hasattr(emp, 'child_ids') and emp.child_ids:
            for child in emp.child_ids:
                children.append({
                    'id': child.id,
                    'name': self._get_value(child, 'name'),
                    'gender': self._get_value(child, 'gender'),
                    'birth_date': self._get_value(child, 'birth_date'),
                    'age': self._get_value(child, 'age') if hasattr(child, 'age') else None,
                    'status': self._get_value(child, 'status') if hasattr(child, 'status') else None,
                })
        
        return {
            'status_kawin': self._get_value(emp, 'status_kawin'),
            'spouse': {
                'name': self._get_value(emp, 'spouse_name'),
                'nik': self._get_value(emp, 'spouse_nik'),
                'birthday': self._get_value(emp, 'spouse_birthday'),
            } if self._get_value(emp, 'spouse_name') else None,
            'children': children,
            'children_count': len(children),
            'jlh_anggota_keluarga': self._get_value(emp, 'jlh_anggota_keluarga'),
        }
    
    def _get_bpjs_data(self, emp):
        """Get BPJS data for JSON."""
        bpjs_list = []
        
        if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
            for bpjs in emp.bpjs_ids:
                bpjs_list.append({
                    'id': bpjs.id,
                    'type': self._get_value(bpjs, 'bpjs_type'),
                    'number': self._get_value(bpjs, 'number'),
                    'faskes_tk1': self._get_value(bpjs, 'faskes_tk1'),
                    'kelas': self._get_value(bpjs, 'kelas'),
                    'status': self._get_value(bpjs, 'status') if hasattr(bpjs, 'status') else None,
                })
        
        return {
            'records': bpjs_list,
            'count': len(bpjs_list),
        }
    
    def _get_education_data(self, emp):
        """Get education data for JSON."""
        education_list = []
        
        if hasattr(emp, 'education_ids') and emp.education_ids:
            for edu in emp.education_ids:
                education_list.append({
                    'id': edu.id,
                    'certificate': self._get_value(edu, 'certificate'),
                    'study_school': self._get_value(edu, 'study_school'),
                    'major': self._get_value(edu, 'major'),
                    'date_start': self._get_value(edu, 'date_start'),
                    'date_end': self._get_value(edu, 'date_end'),
                })
        
        return {
            'records': education_list,
            'count': len(education_list),
            'highest': education_list[0] if education_list else None,
        }
    
    def _get_payroll_data(self, emp):
        """Get payroll data for JSON."""
        payroll = self.get_field_value(emp, 'payroll_id')
        
        if payroll:
            return {
                'id': payroll.id,
                'bank_name': self._get_value(payroll, 'bank_name'),
                'bank_account': self._get_value(payroll, 'bank_account'),
                'npwp': self._get_value(payroll, 'npwp'),
                'efin': self._get_value(payroll, 'efin'),
            }
        
        return None
    
    def _get_training_data(self, emp):
        """Get training data for JSON."""
        training_list = []
        
        if hasattr(emp, 'training_certificate_ids') and emp.training_certificate_ids:
            for training in emp.training_certificate_ids:
                training_list.append({
                    'id': training.id,
                    'name': self._get_value(training, 'name'),
                    'jenis_pelatihan': self._get_value(training, 'jenis_pelatihan'),
                    'metode': self._get_value(training, 'metode'),
                    'date_start': self._get_value(training, 'date_start'),
                    'date_end': self._get_value(training, 'date_end'),
                })
        
        return {
            'records': training_list,
            'count': len(training_list),
        }
    
    def _get_reward_punishment_data(self, emp):
        """Get reward/punishment data for JSON."""
        rp_list = []
        reward_count = 0
        punishment_count = 0
        
        if hasattr(emp, 'reward_punishment_ids') and emp.reward_punishment_ids:
            for rp in emp.reward_punishment_ids:
                rp_type = self._get_value(rp, 'type')
                if rp_type == 'reward':
                    reward_count += 1
                elif rp_type == 'punishment':
                    punishment_count += 1
                
                rp_list.append({
                    'id': rp.id,
                    'type': rp_type,
                    'name': self._get_value(rp, 'name'),
                    'date': self._get_value(rp, 'date'),
                    'description': self._get_value(rp, 'description'),
                })
        
        return {
            'records': rp_list,
            'count': len(rp_list),
            'reward_count': reward_count,
            'punishment_count': punishment_count,
        }
    
    def export_template(self, employees, template):
        """
        Export data karyawan menggunakan template.
        
        Args:
            employees: hr.employee recordset
            template: hr.employee.export.template record
            
        Returns:
            tuple: (bytes, filename)
        """
        self.validate_employees(employees)
        
        # Parse field mapping dari template
        field_mapping = template.get_parsed_field_mapping()
        
        # Build data berdasarkan field mapping
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'template_name': template.name,
                'template_code': template.template_type,
                'total_employees': len(employees),
            },
            'employees': [],
        }
        
        for emp in employees:
            emp_data = {'id': emp.id}
            
            for field_key, field_info in field_mapping.items():
                field_name = field_info.get('field', field_key)
                label = field_info.get('label', field_key)
                
                # Get value using dot notation
                value = self._get_value(emp, field_name)
                emp_data[field_key] = value
            
            export_data['employees'].append(emp_data)
        
        # Convert to JSON
        json_str = json.dumps(export_data, cls=DateTimeEncoder,
                              indent=self.indent, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        
        filename = self.generate_filename(f'export_{template.template_type}', 'json')
        
        return json_bytes, filename
    
    def export_for_api(self, employees, categories=None):
        """
        Export data untuk API response (tanpa bytes conversion).
        
        Args:
            employees: hr.employee recordset
            categories (list): List kategori
            
        Returns:
            dict: Export data sebagai dictionary
        """
        if categories is None:
            categories = ['identity', 'employment']
        
        return {
            'metadata': self._build_metadata(employees, categories),
            'employees': self._build_employees_data(employees, categories),
        }
