# -*- coding: utf-8 -*-

"""
Dashboard Controller untuk yhc_employee_export

Controller ini menyediakan endpoint untuk dashboard analytics
yang dapat diakses melalui REST API.
"""

import json
import logging
from datetime import date, datetime

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class DashboardController(http.Controller):
    """
    Controller untuk Dashboard Analytics.
    
    Menyediakan endpoint untuk:
    - Get dashboard data (KPI + Charts)
    - Get analytics summary
    - Get department list for filter
    """
    
    def _json_response(self, data, status=200):
        """Helper untuk JSON response."""
        return Response(
            json.dumps(data, default=str),
            status=status,
            content_type='application/json'
        )
    
    def _check_access(self):
        """Check user access untuk dashboard."""
        user = request.env.user
        if not user or user._is_public():
            return False
        return True
    
    # ===== Dashboard Data Endpoints =====
    
    @http.route(
        '/api/dashboard/data',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_dashboard_data(self, **kwargs):
        """
        Get complete dashboard data.
        
        Query Parameters:
            department_id (int): Filter by department (optional)
            
        Returns:
            JSON: Complete dashboard data including KPI and chart data
        """
        try:
            if not self._check_access():
                return self._json_response({
                    'success': False,
                    'error': 'Access denied'
                }, 403)
            
            department_id = kwargs.get('department_id')
            if department_id:
                department_id = int(department_id)
            else:
                department_id = False
            
            # Get data from analytics model
            analytics = request.env['hr.employee.analytics'].sudo()
            data = analytics.get_dashboard_data(department_id=department_id)
            
            return self._json_response({
                'success': True,
                'data': data,
            })
            
        except Exception as e:
            _logger.exception("Error getting dashboard data")
            return self._json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    @http.route(
        '/api/dashboard/kpi',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_kpi_data(self, **kwargs):
        """
        Get only KPI data for quick loading.
        
        Returns:
            JSON: KPI data only
        """
        try:
            if not self._check_access():
                return self._json_response({
                    'success': False,
                    'error': 'Access denied'
                }, 403)
            
            department_id = kwargs.get('department_id')
            if department_id:
                department_id = int(department_id)
            else:
                department_id = False
            
            analytics = request.env['hr.employee.analytics'].sudo()
            full_data = analytics.get_dashboard_data(department_id=department_id)
            
            return self._json_response({
                'success': True,
                'data': full_data.get('kpi', {}),
            })
            
        except Exception as e:
            _logger.exception("Error getting KPI data")
            return self._json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    @http.route(
        '/api/dashboard/departments',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_departments(self, **kwargs):
        """
        Get list of departments for filter dropdown.
        
        Returns:
            JSON: List of departments with id and name
        """
        try:
            if not self._check_access():
                return self._json_response({
                    'success': False,
                    'error': 'Access denied'
                }, 403)
            
            departments = request.env['hr.department'].sudo().search_read(
                [],
                ['id', 'name'],
                order='name'
            )
            
            return self._json_response({
                'success': True,
                'data': departments,
            })
            
        except Exception as e:
            _logger.exception("Error getting departments")
            return self._json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    @http.route(
        '/api/dashboard/chart/<string:chart_type>',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_chart_data(self, chart_type, **kwargs):
        """
        Get specific chart data.
        
        Path Parameters:
            chart_type: Type of chart (gender, age, department, education, etc.)
            
        Returns:
            JSON: Chart-specific data
        """
        try:
            if not self._check_access():
                return self._json_response({
                    'success': False,
                    'error': 'Access denied'
                }, 403)
            
            valid_charts = [
                'gender', 'age_groups', 'departments', 'education',
                'employment_type', 'service_length', 'bpjs', 'religion', 'marital'
            ]
            
            if chart_type not in valid_charts:
                return self._json_response({
                    'success': False,
                    'error': f'Invalid chart type. Valid types: {", ".join(valid_charts)}'
                }, 400)
            
            department_id = kwargs.get('department_id')
            if department_id:
                department_id = int(department_id)
            else:
                department_id = False
            
            analytics = request.env['hr.employee.analytics'].sudo()
            full_data = analytics.get_dashboard_data(department_id=department_id)
            
            return self._json_response({
                'success': True,
                'chart_type': chart_type,
                'data': full_data.get(chart_type, {}),
            })
            
        except Exception as e:
            _logger.exception(f"Error getting chart data for {chart_type}")
            return self._json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    @http.route(
        '/api/dashboard/export-stats',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_export_stats(self, **kwargs):
        """
        Get export statistics/history.
        
        Query Parameters:
            date_from (str): Start date (YYYY-MM-DD)
            date_to (str): End date (YYYY-MM-DD)
            
        Returns:
            JSON: Export statistics
        """
        try:
            if not self._check_access():
                return self._json_response({
                    'success': False,
                    'error': 'Access denied'
                }, 403)
            
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            analytics = request.env['hr.employee.analytics'].sudo()
            data = analytics.get_export_analytics(
                date_from=date_from,
                date_to=date_to
            )
            
            return self._json_response({
                'success': True,
                'data': data,
            })
            
        except Exception as e:
            _logger.exception("Error getting export stats")
            return self._json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    # ===== Summary Endpoint =====
    
    @http.route(
        '/api/dashboard/summary',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_summary(self, **kwargs):
        """
        Get quick summary for widgets.
        
        Returns:
            JSON: Quick summary data
        """
        try:
            if not self._check_access():
                return self._json_response({
                    'success': False,
                    'error': 'Access denied'
                }, 403)
            
            Employee = request.env['hr.employee'].sudo()
            
            total = Employee.search_count([('active', 'in', [True, False])])
            active = Employee.search_count([('active', '=', True)])
            male = Employee.search_count([
                ('active', '=', True),
                ('gender', '=', 'male')
            ])
            female = Employee.search_count([
                ('active', '=', True),
                ('gender', '=', 'female')
            ])
            
            return self._json_response({
                'success': True,
                'data': {
                    'total_employees': total,
                    'active_employees': active,
                    'inactive_employees': total - active,
                    'male_employees': male,
                    'female_employees': female,
                    'last_updated': datetime.now().isoformat(),
                }
            })
            
        except Exception as e:
            _logger.exception("Error getting summary")
            return self._json_response({
                'success': False,
                'error': str(e)
            }, 500)
