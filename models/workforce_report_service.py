# -*- coding: utf-8 -*-
"""
Model: Workforce Report Service (ORM Wrapper)
Provides ORM access to the workforce report service.

This is the model wrapper that allows other models and wizards
to access the WorkforceReportService class.
"""

from odoo import api, fields, models, _

from ..services.workforce_report_service import WorkforceReportService


class WorkforceReportServiceModel(models.TransientModel):
    """
    Transient model wrapper for WorkforceReportService.
    
    Provides ORM access to the workforce report service.
    """
    
    _name = 'workforce.report.service'
    _description = 'Workforce Report Service'
    
    @api.model
    def get_service(self):
        """Get instance of WorkforceReportService."""
        return WorkforceReportService(self.env)
    
    @api.model
    def validate_snapshot(self, year, month):
        """Validate snapshot exists for period."""
        service = self.get_service()
        return service.validate_snapshot_exists(year, month)
    
    @api.model
    def generate_report_data(self, year, month):
        """Generate complete report data."""
        service = self.get_service()
        return service.generate_complete_report_data(year, month)
    
    @api.model
    def get_payroll_table(self, year, month):
        """Get payroll vs non-payroll table data."""
        service = self.get_service()
        return service.get_payroll_vs_non_payroll_table(year, month)
    
    @api.model
    def get_payroll_chart(self, year, month):
        """Get payroll vs non-payroll chart data."""
        service = self.get_service()
        return service.get_payroll_vs_non_payroll_chart(year, month)
    
    @api.model
    def get_total_workforce_chart(self, year, month):
        """Get total workforce per unit chart data."""
        service = self.get_service()
        return service.get_total_workforce_per_unit(year, month)
    
    @api.model
    def get_monthly_snapshot_table(self, year):
        """Get monthly workforce snapshot table."""
        service = self.get_service()
        return service.get_monthly_workforce_snapshot(year)
    
    @api.model
    def get_status_distribution(self, year, month):
        """Get employment status distribution chart."""
        service = self.get_service()
        return service.get_employment_status_distribution(year, month)
