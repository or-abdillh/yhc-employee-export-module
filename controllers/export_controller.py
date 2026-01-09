# -*- coding: utf-8 -*-
"""
API Controller untuk yhc_employee_export.

Controller ini menyediakan REST API endpoints untuk:
- Export data karyawan ke berbagai format
- Download file hasil export
- API untuk dashboard analytics
"""

import json
import base64
import logging
from datetime import datetime

from odoo import http, _
from odoo.http import request, Response
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)


class EmployeeExportController(http.Controller):
    """
    REST API Controller untuk Employee Export.
    
    Endpoints:
    - /api/employee/export - Export data karyawan
    - /api/employee/export/download/<int:id> - Download file export
    - /api/employee/analytics - Get analytics data
    """
    
    # ===========================================
    # Export Endpoints
    # ===========================================
    
    @http.route('/api/employee/export', type='json', auth='user', methods=['POST'])
    def api_export(self, **kwargs):
        """
        Export data karyawan via API.
        
        Request body:
        {
            "format": "xlsx|csv|json|pdf",
            "categories": ["identity", "employment", ...],
            "filters": {
                "department_ids": [1, 2, 3],
                "employment_status": "active",
                "date_from": "2024-01-01",
                "date_to": "2024-12-31"
            },
            "options": {
                "include_header": true,
                "delimiter": ","
            }
        }
        
        Returns:
            dict: {
                "success": true,
                "data": "base64_encoded_file",
                "filename": "export_karyawan_20240101.xlsx",
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        """
        try:
            # Validate access
            self._check_export_access()
            
            # Get parameters
            export_format = kwargs.get('format', 'xlsx')
            categories = kwargs.get('categories', ['identity', 'employment'])
            filters = kwargs.get('filters', {})
            options = kwargs.get('options', {})
            
            # Get employees based on filters
            employees = self._get_filtered_employees(filters)
            
            if not employees:
                return {
                    'success': False,
                    'error': 'Tidak ada data karyawan yang sesuai filter'
                }
            
            # Export based on format
            file_data, filename = self._do_export(
                employees, export_format, categories, options
            )
            
            # Encode to base64
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            # Get mimetype
            mimetype = self._get_mimetype(export_format)
            
            return {
                'success': True,
                'data': file_base64,
                'filename': filename,
                'mimetype': mimetype,
                'total_records': len(employees),
            }
            
        except AccessError as e:
            _logger.warning(f"Access denied for export: {str(e)}")
            return {'success': False, 'error': 'Akses ditolak'}
        except Exception as e:
            _logger.error(f"Export error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/employee/export/regulatory', type='json', auth='user', methods=['POST'])
    def api_export_regulatory(self, **kwargs):
        """
        Export data ke format regulatory (BPJS, SPT, dll).
        
        Request body:
        {
            "type": "bpjs_kes|bpjs_tk|spt|wlk",
            "subtype": "active|new|update|...",
            "filters": {...},
            "options": {...}
        }
        """
        try:
            self._check_export_access()
            
            export_type = kwargs.get('type', 'bpjs_kes')
            subtype = kwargs.get('subtype', 'active')
            filters = kwargs.get('filters', {})
            options = kwargs.get('options', {})
            
            employees = self._get_filtered_employees(filters)
            
            if not employees:
                return {
                    'success': False,
                    'error': 'Tidak ada data karyawan yang sesuai filter'
                }
            
            # Use regulatory export service
            from ..services import EmployeeExportRegulatory
            service = EmployeeExportRegulatory(request.env)
            
            file_data, filename = service.export(
                employees, export_type, subtype, **options
            )
            
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            return {
                'success': True,
                'data': file_base64,
                'filename': filename,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'total_records': len(employees),
            }
            
        except Exception as e:
            _logger.error(f"Regulatory export error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/employee/export/download', type='http', auth='user', methods=['GET'])
    def api_download(self, format='xlsx', **kwargs):
        """
        Download export file directly.
        
        Query parameters:
        - format: xlsx|csv|json|pdf
        - categories: comma-separated list
        - department_ids: comma-separated list
        - employment_status: active|resign|pension
        """
        try:
            self._check_export_access()
            
            # Parse parameters
            export_format = format
            categories = kwargs.get('categories', 'identity,employment').split(',')
            
            filters = {}
            if kwargs.get('department_ids'):
                filters['department_ids'] = [int(x) for x in kwargs['department_ids'].split(',')]
            if kwargs.get('employment_status'):
                filters['employment_status'] = kwargs['employment_status']
            
            employees = self._get_filtered_employees(filters)
            
            if not employees:
                return Response("No data found", status=404)
            
            # Export
            file_data, filename = self._do_export(
                employees, export_format, categories, {}
            )
            
            mimetype = self._get_mimetype(export_format)
            
            # Return as file download
            return request.make_response(
                file_data,
                headers=[
                    ('Content-Type', mimetype),
                    ('Content-Disposition', f'attachment; filename="{filename}"'),
                    ('Content-Length', len(file_data)),
                ]
            )
            
        except AccessError:
            return Response("Access Denied", status=403)
        except Exception as e:
            _logger.error(f"Download error: {str(e)}")
            return Response(str(e), status=500)
    
    # ===========================================
    # Analytics Endpoints
    # ===========================================
    
    @http.route('/api/employee/analytics', type='json', auth='user', methods=['GET', 'POST'])
    def api_analytics(self, **kwargs):
        """
        Get employee analytics data for dashboard.
        
        Returns:
            dict: Analytics data including counts, distributions, trends
        """
        try:
            self._check_export_access()
            
            filters = kwargs.get('filters', {})
            employees = self._get_filtered_employees(filters)
            
            analytics = self._calculate_analytics(employees)
            
            return {
                'success': True,
                'data': analytics,
            }
            
        except Exception as e:
            _logger.error(f"Analytics error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/employee/analytics/gender', type='json', auth='user', methods=['GET'])
    def api_analytics_gender(self, **kwargs):
        """Get gender distribution."""
        try:
            self._check_export_access()
            employees = self._get_filtered_employees({})
            
            gender_data = {'male': 0, 'female': 0}
            for emp in employees:
                gender = emp.gender or 'male'
                if gender in gender_data:
                    gender_data[gender] += 1
            
            return {
                'success': True,
                'data': gender_data,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/employee/analytics/department', type='json', auth='user', methods=['GET'])
    def api_analytics_department(self, **kwargs):
        """Get department distribution."""
        try:
            self._check_export_access()
            employees = self._get_filtered_employees({})
            
            dept_data = {}
            for emp in employees:
                dept_name = emp.department_id.name if emp.department_id else 'Tidak Ada Departemen'
                dept_data[dept_name] = dept_data.get(dept_name, 0) + 1
            
            return {
                'success': True,
                'data': dept_data,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/employee/analytics/age', type='json', auth='user', methods=['GET'])
    def api_analytics_age(self, **kwargs):
        """Get age distribution."""
        try:
            self._check_export_access()
            employees = self._get_filtered_employees({})
            
            age_groups = {
                '< 25': 0,
                '25-34': 0,
                '35-44': 0,
                '45-54': 0,
                '>= 55': 0,
            }
            
            for emp in employees:
                age = emp.age if hasattr(emp, 'age') else 0
                if age < 25:
                    age_groups['< 25'] += 1
                elif age < 35:
                    age_groups['25-34'] += 1
                elif age < 45:
                    age_groups['35-44'] += 1
                elif age < 55:
                    age_groups['45-54'] += 1
                else:
                    age_groups['>= 55'] += 1
            
            return {
                'success': True,
                'data': age_groups,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ===========================================
    # Template Endpoints
    # ===========================================
    
    @http.route('/api/employee/export/templates', type='json', auth='user', methods=['GET'])
    def api_get_templates(self, **kwargs):
        """Get available export templates."""
        try:
            self._check_export_access()
            
            Template = request.env['hr.employee.export.template']
            templates = Template.search([('is_active', '=', True)])
            
            result = []
            for t in templates:
                result.append({
                    'id': t.id,
                    'name': t.name,
                    'code': t.template_type,
                    'description': t.description or '',
                    'is_system': t.is_system,
                })
            
            return {
                'success': True,
                'data': result,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route('/api/employee/export/configs', type='json', auth='user', methods=['GET'])
    def api_get_configs(self, **kwargs):
        """Get available export configurations."""
        try:
            self._check_export_access()
            
            Config = request.env['hr.employee.export.config']
            configs = Config.search([('is_active', '=', True)])
            
            result = []
            for c in configs:
                result.append({
                    'id': c.id,
                    'name': c.name,
                    'description': c.description or '',
                    'categories': c.selected_categories_count,
                })
            
            return {
                'success': True,
                'data': result,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ===========================================
    # Helper Methods
    # ===========================================
    
    def _check_export_access(self):
        """Check if user has export access."""
        if not request.env.user.has_group('yhc_employee_export.group_hr_export_user'):
            raise AccessError(_("Anda tidak memiliki akses untuk export data karyawan"))
    
    def _get_filtered_employees(self, filters):
        """Get employees based on filters."""
        Employee = request.env['hr.employee']
        domain = []
        
        # Department filter
        if filters.get('department_ids'):
            domain.append(('department_id', 'in', filters['department_ids']))
        
        # Employment status filter
        if filters.get('employment_status'):
            status = filters['employment_status']
            if status == 'active':
                domain.append(('employment_status', 'in', ['Aktif', 'aktif', 'active']))
            elif status == 'resign':
                domain.append(('employment_status', 'in', ['Resign', 'resign']))
            elif status == 'pension':
                domain.append(('employment_status', 'in', ['Pensiun', 'pensiun', 'pension']))
        
        # Date range filter
        if filters.get('date_from'):
            domain.append(('first_contract_date', '>=', filters['date_from']))
        if filters.get('date_to'):
            domain.append(('first_contract_date', '<=', filters['date_to']))
        
        # Employee IDs filter
        if filters.get('employee_ids'):
            domain.append(('id', 'in', filters['employee_ids']))
        
        return Employee.search(domain)
    
    def _do_export(self, employees, export_format, categories, options):
        """Perform export using appropriate service."""
        from ..services import (
            EmployeeExportXlsx, EmployeeExportCsv,
            EmployeeExportJson, EmployeeExportPdf
        )
        
        if export_format == 'xlsx':
            service = EmployeeExportXlsx(request.env)
            return service.export(employees, categories)
        elif export_format == 'csv':
            delimiter = options.get('delimiter', ',')
            service = EmployeeExportCsv(request.env)
            return service.export(employees, categories, delimiter=delimiter)
        elif export_format == 'json':
            pretty = options.get('pretty', True)
            service = EmployeeExportJson(request.env)
            return service.export(employees, categories, pretty=pretty)
        elif export_format == 'pdf':
            service = EmployeeExportPdf(request.env)
            return service.export(employees, categories)
        else:
            raise ValueError(f"Format tidak didukung: {export_format}")
    
    def _get_mimetype(self, export_format):
        """Get MIME type for export format."""
        mimetypes = {
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv; charset=utf-8',
            'json': 'application/json',
            'pdf': 'application/pdf',
        }
        return mimetypes.get(export_format, 'application/octet-stream')
    
    def _calculate_analytics(self, employees):
        """Calculate analytics data for employees."""
        analytics = {
            'summary': {
                'total': len(employees),
                'active': 0,
                'inactive': 0,
            },
            'gender': {'male': 0, 'female': 0},
            'department': {},
            'age_groups': {
                '< 25': 0,
                '25-34': 0,
                '35-44': 0,
                '45-54': 0,
                '>= 55': 0,
            },
            'education': {},
            'employment_type': {},
            'service_length': {
                '< 1 tahun': 0,
                '1-3 tahun': 0,
                '3-5 tahun': 0,
                '5-10 tahun': 0,
                '> 10 tahun': 0,
            },
            'bpjs': {
                'kesehatan': {'yes': 0, 'no': 0},
                'ketenagakerjaan': {'yes': 0, 'no': 0},
            },
        }
        
        for emp in employees:
            # Status
            status = emp.employment_status or ''
            if status.lower() in ['aktif', 'active']:
                analytics['summary']['active'] += 1
            else:
                analytics['summary']['inactive'] += 1
            
            # Gender
            gender = emp.gender or 'male'
            if gender in analytics['gender']:
                analytics['gender'][gender] += 1
            
            # Department
            dept = emp.department_id.name if emp.department_id else 'Tidak Ada'
            analytics['department'][dept] = analytics['department'].get(dept, 0) + 1
            
            # Age
            age = emp.age if hasattr(emp, 'age') else 0
            if age < 25:
                analytics['age_groups']['< 25'] += 1
            elif age < 35:
                analytics['age_groups']['25-34'] += 1
            elif age < 45:
                analytics['age_groups']['35-44'] += 1
            elif age < 55:
                analytics['age_groups']['45-54'] += 1
            else:
                analytics['age_groups']['>= 55'] += 1
            
            # Education
            if hasattr(emp, 'education_ids') and emp.education_ids:
                edu = emp.education_ids[0].certificate or 'Lainnya'
                analytics['education'][edu] = analytics['education'].get(edu, 0) + 1
            
            # Employment type
            emp_type = emp.employee_type_id.name if hasattr(emp, 'employee_type_id') and emp.employee_type_id else 'Tidak Ada'
            analytics['employment_type'][emp_type] = analytics['employment_type'].get(emp_type, 0) + 1
            
            # Service length
            service = emp.service_length if hasattr(emp, 'service_length') else 0
            if service < 1:
                analytics['service_length']['< 1 tahun'] += 1
            elif service < 3:
                analytics['service_length']['1-3 tahun'] += 1
            elif service < 5:
                analytics['service_length']['3-5 tahun'] += 1
            elif service < 10:
                analytics['service_length']['5-10 tahun'] += 1
            else:
                analytics['service_length']['> 10 tahun'] += 1
            
            # BPJS
            has_bpjs_kes = False
            has_bpjs_tk = False
            if hasattr(emp, 'bpjs_ids') and emp.bpjs_ids:
                for bpjs in emp.bpjs_ids:
                    if bpjs.bpjs_type == 'kesehatan':
                        has_bpjs_kes = True
                    elif bpjs.bpjs_type == 'ketenagakerjaan':
                        has_bpjs_tk = True
            
            analytics['bpjs']['kesehatan']['yes' if has_bpjs_kes else 'no'] += 1
            analytics['bpjs']['ketenagakerjaan']['yes' if has_bpjs_tk else 'no'] += 1
        
        return analytics
