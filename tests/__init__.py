# -*- coding: utf-8 -*-
"""
Tests package untuk yhc_employee_export.

Package ini berisi unit tests untuk:
- test_export_config: Test model konfigurasi export
- test_export_service: Test service export
- test_dashboard: Test method dashboard
- test_security: Test access rights
- test_workforce_analytics: Test workforce analytics (PRD v1.1)
- test_workforce_report: Test Workforce Report Engine (PRD v1.1)

Run tests dengan:
    ./odoo-bin -c odoo.conf -d testdb --test-tags yhc_export -i yhc_employee_export --stop-after-init
    
Run workforce analytics tests:
    ./odoo-bin -c odoo.conf -d testdb --test-tags workforce_analytics -i yhc_employee_export --stop-after-init

Run workforce report tests:
    ./odoo-bin -c odoo.conf -d testdb --test-tags workforce_report -i yhc_employee_export --stop-after-init
"""

from . import test_export_config
from . import test_export_service
from . import test_dashboard
from . import test_security
from . import test_workforce_analytics
from . import test_workforce_report
