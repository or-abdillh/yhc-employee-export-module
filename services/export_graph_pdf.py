# -*- coding: utf-8 -*-
"""
Export Service: Graph PDF
Service untuk export grafik analytics ke PDF.

Menggunakan matplotlib untuk rendering chart ke image,
kemudian inject ke PDF template.
"""

import base64
import logging
import tempfile
import os
from datetime import datetime, date
from io import BytesIO

from odoo.exceptions import UserError
from odoo import _

from .export_base import EmployeeExportBase
from ..models.graph_registry import GRAPH_REGISTRY, CHART_COLORS

_logger = logging.getLogger(__name__)

# Check matplotlib availability
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    _logger.warning("matplotlib not installed. Graph export will use fallback.")


class EmployeeExportGraphPdf(EmployeeExportBase):
    """
    Service untuk export grafik dashboard ke PDF.
    
    Features:
    - Render chart menggunakan matplotlib
    - Generate PDF dengan grafik high-resolution
    - Multiple layout options
    - Cover page dan summary
    """
    
    def __init__(self, env):
        """Initialize graph PDF export service."""
        super().__init__(env)
        self.dpi = 150  # DPI untuk grafik
        self.figure_size = (8, 6)  # Ukuran default grafik (inches)
    
    def export(self, employees, graphs, options=None):
        """
        Export grafik ke PDF.
        
        Args:
            employees: hr.employee recordset
            graphs: List of graph definitions from GRAPH_REGISTRY
            options: Dict with export options
            
        Returns:
            tuple: (bytes, filename)
        """
        if options is None:
            options = {}
        
        self.validate_employees(employees)
        
        if not graphs:
            raise UserError(_('Minimal 1 grafik harus dipilih!'))
        
        try:
            # Get analytics data
            analytics_data = self._get_analytics_data(employees)
            
            # Render charts to images
            chart_images = self._render_charts(graphs, analytics_data)
            
            # Generate PDF
            pdf_content = self._generate_pdf(employees, graphs, chart_images, analytics_data, options)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"laporan_grafik_{timestamp}.pdf"
            
            return pdf_content, filename
            
        except Exception as e:
            _logger.error(f"Error exporting graph PDF: {str(e)}")
            raise
    
    def _get_analytics_data(self, employees):
        """
        Mengambil data analytics dari employees.
        
        Args:
            employees: hr.employee recordset
            
        Returns:
            dict: Data analytics untuk semua chart
        """
        Analytics = self.env['hr.employee.analytics']
        
        # Get basic analytics
        data = {
            'total': len(employees),
            'active': len(employees.filtered(lambda e: e.active)),
        }
        
        # Gender distribution
        data['gender'] = self._calc_gender_distribution(employees)
        
        # Age distribution
        data['age'] = self._calc_age_distribution(employees)
        
        # Department distribution
        data['department'] = self._calc_department_distribution(employees)
        
        # Religion distribution
        data['religion'] = self._calc_religion_distribution(employees)
        
        # Marital status distribution
        data['marital'] = self._calc_marital_distribution(employees)
        
        # Employment status
        data['employment_status'] = self._calc_employment_status(employees)
        
        # Tenure distribution
        data['tenure'] = self._calc_tenure_distribution(employees)
        
        # Education distribution
        data['education'] = self._calc_education_distribution(employees)
        
        # Golongan distribution
        data['golongan'] = self._calc_golongan_distribution(employees)
        
        # Grade distribution
        data['grade'] = self._calc_grade_distribution(employees)
        
        # Training type
        data['training_type'] = self._calc_training_type_distribution(employees)
        
        # Training method
        data['training_method'] = self._calc_training_method_distribution(employees)
        
        # KPI summary
        data['kpi'] = self._calc_kpi_summary(employees)
        
        return data
    
    def _calc_gender_distribution(self, employees):
        """Hitung distribusi gender."""
        male = len(employees.filtered(lambda e: e.gender == 'male'))
        female = len(employees.filtered(lambda e: e.gender == 'female'))
        other = len(employees) - male - female
        
        return {
            'labels': ['Pria', 'Wanita', 'Lainnya'] if other > 0 else ['Pria', 'Wanita'],
            'data': [male, female, other] if other > 0 else [male, female],
        }
    
    def _calc_age_distribution(self, employees):
        """Hitung distribusi usia."""
        from dateutil.relativedelta import relativedelta
        today = date.today()
        
        age_groups = {
            '< 25': 0,
            '25-34': 0,
            '35-44': 0,
            '45-54': 0,
            '≥ 55': 0,
        }
        
        for emp in employees:
            if emp.birthday:
                age = relativedelta(today, emp.birthday).years
                if age < 25:
                    age_groups['< 25'] += 1
                elif age < 35:
                    age_groups['25-34'] += 1
                elif age < 45:
                    age_groups['35-44'] += 1
                elif age < 55:
                    age_groups['45-54'] += 1
                else:
                    age_groups['≥ 55'] += 1
        
        return {
            'labels': list(age_groups.keys()),
            'data': list(age_groups.values()),
        }
    
    def _calc_department_distribution(self, employees):
        """Hitung distribusi per departemen."""
        dept_count = {}
        for emp in employees:
            dept_name = emp.department_id.name if emp.department_id else 'Tidak Ada'
            dept_count[dept_name] = dept_count.get(dept_name, 0) + 1
        
        # Sort by count descending, limit top 10
        sorted_depts = sorted(dept_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'labels': [d[0] for d in sorted_depts],
            'data': [d[1] for d in sorted_depts],
        }
    
    def _calc_religion_distribution(self, employees):
        """Hitung distribusi agama."""
        religion_map = {
            'islam': 'Islam',
            'kristen': 'Kristen',
            'katolik': 'Katolik',
            'hindu': 'Hindu',
            'budha': 'Buddha',
            'konghucu': 'Konghucu',
        }
        
        religion_count = {}
        for emp in employees:
            religion = getattr(emp, 'religion', False)
            if religion:
                label = religion_map.get(religion, religion.title())
                religion_count[label] = religion_count.get(label, 0) + 1
        
        return {
            'labels': list(religion_count.keys()) or ['Tidak Ada Data'],
            'data': list(religion_count.values()) or [0],
        }
    
    def _calc_marital_distribution(self, employees):
        """Hitung distribusi status pernikahan."""
        marital_map = {
            'single': 'Lajang',
            'married': 'Menikah',
            'cohabitant': 'Tinggal Bersama',
            'widower': 'Duda/Janda',
            'divorced': 'Cerai',
        }
        
        marital_count = {}
        for emp in employees:
            marital = emp.marital or 'single'
            label = marital_map.get(marital, marital.title())
            marital_count[label] = marital_count.get(label, 0) + 1
        
        return {
            'labels': list(marital_count.keys()),
            'data': list(marital_count.values()),
        }
    
    def _calc_employment_status(self, employees):
        """Hitung distribusi status kepegawaian."""
        status_count = {'Aktif': 0, 'Non-aktif': 0}
        
        for emp in employees:
            if emp.active:
                status_count['Aktif'] += 1
            else:
                status_count['Non-aktif'] += 1
        
        return {
            'labels': list(status_count.keys()),
            'data': list(status_count.values()),
        }
    
    def _calc_tenure_distribution(self, employees):
        """Hitung distribusi masa kerja."""
        from dateutil.relativedelta import relativedelta
        today = date.today()
        
        tenure_groups = {
            '< 1 tahun': 0,
            '1-3 tahun': 0,
            '3-5 tahun': 0,
            '5-10 tahun': 0,
            '> 10 tahun': 0,
        }
        
        for emp in employees:
            join_date = getattr(emp, 'first_contract_date', None)
            
            if join_date:
                tenure = relativedelta(today, join_date)
                years = tenure.years + (tenure.months / 12)
                
                if years < 1:
                    tenure_groups['< 1 tahun'] += 1
                elif years < 3:
                    tenure_groups['1-3 tahun'] += 1
                elif years < 5:
                    tenure_groups['3-5 tahun'] += 1
                elif years < 10:
                    tenure_groups['5-10 tahun'] += 1
                else:
                    tenure_groups['> 10 tahun'] += 1
        
        return {
            'labels': list(tenure_groups.keys()),
            'data': list(tenure_groups.values()),
        }
    
    def _calc_education_distribution(self, employees):
        """Hitung distribusi tingkat pendidikan."""
        edu_order = ['SD', 'SMP', 'SMA/SMK', 'D1', 'D2', 'D3', 'D4/S1', 'S2', 'S3']
        edu_count = {level: 0 for level in edu_order}
        
        for emp in employees:
            if hasattr(emp, 'education_ids') and emp.education_ids:
                # Get highest education
                for edu in emp.education_ids:
                    cert = getattr(edu, 'certificate', '')
                    if cert in edu_count:
                        edu_count[cert] += 1
                        break
        
        # Filter out zeros
        filtered = {k: v for k, v in edu_count.items() if v > 0}
        
        return {
            'labels': list(filtered.keys()) or ['Tidak Ada Data'],
            'data': list(filtered.values()) or [0],
        }
    
    def _calc_golongan_distribution(self, employees):
        """Hitung distribusi golongan."""
        gol_count = {}
        
        for emp in employees:
            if hasattr(emp, 'golongan_id') and emp.golongan_id:
                gol_name = emp.golongan_id.name
                gol_count[gol_name] = gol_count.get(gol_name, 0) + 1
        
        return {
            'labels': list(gol_count.keys()) or ['Tidak Ada Data'],
            'data': list(gol_count.values()) or [0],
        }
    
    def _calc_grade_distribution(self, employees):
        """Hitung distribusi grade."""
        grade_count = {}
        
        for emp in employees:
            if hasattr(emp, 'grade_id') and emp.grade_id:
                grade_name = emp.grade_id.name
                grade_count[grade_name] = grade_count.get(grade_name, 0) + 1
        
        return {
            'labels': list(grade_count.keys()) or ['Tidak Ada Data'],
            'data': list(grade_count.values()) or [0],
        }
    
    def _calc_training_type_distribution(self, employees):
        """Hitung distribusi jenis pelatihan."""
        type_count = {}
        
        for emp in employees:
            if hasattr(emp, 'training_certificate_ids'):
                for training in emp.training_certificate_ids:
                    t_type = getattr(training, 'jenis_pelatihan', 'Lainnya') or 'Lainnya'
                    type_count[t_type] = type_count.get(t_type, 0) + 1
        
        return {
            'labels': list(type_count.keys()) or ['Tidak Ada Data'],
            'data': list(type_count.values()) or [0],
        }
    
    def _calc_training_method_distribution(self, employees):
        """Hitung distribusi metode pelatihan."""
        method_count = {}
        
        for emp in employees:
            if hasattr(emp, 'training_certificate_ids'):
                for training in emp.training_certificate_ids:
                    method = getattr(training, 'metode', 'Lainnya') or 'Lainnya'
                    method_count[method] = method_count.get(method, 0) + 1
        
        return {
            'labels': list(method_count.keys()) or ['Tidak Ada Data'],
            'data': list(method_count.values()) or [0],
        }
    
    def _calc_kpi_summary(self, employees):
        """Hitung KPI summary."""
        from dateutil.relativedelta import relativedelta
        today = date.today()
        
        active = employees.filtered(lambda e: e.active)
        
        # Average age
        ages = []
        for emp in active:
            if emp.birthday:
                ages.append(relativedelta(today, emp.birthday).years)
        avg_age = sum(ages) / len(ages) if ages else 0
        
        # Average tenure
        tenures = []
        for emp in active:
            join_date = getattr(emp, 'first_contract_date', None)
            if join_date:
                tenure = relativedelta(today, join_date)
                tenures.append(tenure.years + (tenure.months / 12))
        avg_tenure = sum(tenures) / len(tenures) if tenures else 0
        
        return {
            'total': len(employees),
            'active': len(active),
            'inactive': len(employees) - len(active),
            'avg_age': round(avg_age, 1),
            'avg_tenure': round(avg_tenure, 1),
        }
    
    def _render_charts(self, graphs, analytics_data):
        """
        Render semua chart ke images.
        
        Args:
            graphs: List of graph definitions
            analytics_data: Dict data analytics
            
        Returns:
            dict: {graph_code: base64_image}
        """
        chart_images = {}
        
        for graph in graphs:
            code = graph['code']
            chart_type = graph['chart_type']
            
            try:
                # Get data for this graph
                data = self._get_chart_data(code, analytics_data)
                
                if HAS_MATPLOTLIB:
                    # Render using matplotlib
                    img_data = self._render_matplotlib_chart(graph, data)
                else:
                    # Fallback: generate placeholder
                    img_data = self._render_placeholder_chart(graph, data)
                
                chart_images[code] = img_data
                
            except Exception as e:
                _logger.error(f"Error rendering chart {code}: {str(e)}")
                chart_images[code] = None
        
        return chart_images
    
    def _get_chart_data(self, code, analytics_data):
        """Get chart data based on code."""
        data_mapping = {
            'G01': analytics_data.get('gender', {}),
            'G02': analytics_data.get('age', {}),
            'G03': analytics_data.get('religion', {}),
            'G04': analytics_data.get('marital', {}),
            'G06': analytics_data.get('department', {}),
            'G08': analytics_data.get('golongan', {}),
            'G09': analytics_data.get('grade', {}),
            'G10': analytics_data.get('employment_status', {}),
            'G13': analytics_data.get('tenure', {}),
            'G14': analytics_data.get('tenure', {}),  # Trend uses same data
            'G16': analytics_data.get('education', {}),
            'G20': analytics_data.get('training_type', {}),
            'G21': analytics_data.get('training_method', {}),
        }
        return data_mapping.get(code, {'labels': [], 'data': []})
    
    def _render_matplotlib_chart(self, graph, data):
        """
        Render chart menggunakan matplotlib.
        
        Returns:
            bytes: PNG image data
        """
        code = graph['code']
        chart_type = graph['chart_type']
        title = graph['name']
        colors = graph.get('colors', CHART_COLORS)
        
        labels = data.get('labels', [])
        values = data.get('data', [])
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
        
        if chart_type == 'pie':
            if sum(values) > 0:
                wedges, texts, autotexts = ax.pie(
                    values, 
                    labels=labels,
                    autopct='%1.1f%%',
                    colors=colors[:len(values)],
                    startangle=90,
                )
                ax.axis('equal')
            else:
                ax.text(0.5, 0.5, 'Tidak ada data', ha='center', va='center', fontsize=14)
                ax.axis('off')
                
        elif chart_type == 'bar':
            x = range(len(labels))
            bars = ax.bar(x, values, color=colors[:len(values)])
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.set_ylabel('Jumlah')
            
            # Add value labels on bars
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                       str(val), ha='center', va='bottom', fontsize=9)
                
        elif chart_type == 'line':
            x = range(len(labels))
            ax.plot(x, values, marker='o', color=colors[0], linewidth=2)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.set_ylabel('Jumlah')
            ax.fill_between(x, values, alpha=0.3, color=colors[0])
        
        # Set title
        ax.set_title(title, fontsize=14, fontweight='bold', color='#714B67')
        
        # Tight layout
        plt.tight_layout()
        
        # Save to bytes
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close(fig)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _render_placeholder_chart(self, graph, data):
        """Generate placeholder jika matplotlib tidak tersedia."""
        # Return empty bytes - akan ditangani di PDF generation
        return None
    
    def _generate_pdf(self, employees, graphs, chart_images, analytics_data, options):
        """
        Generate PDF dengan grafik.
        
        Returns:
            bytes: PDF content
        """
        # Build HTML content
        html = self._build_html_report(employees, graphs, chart_images, analytics_data, options)
        
        # Convert to PDF using wkhtmltopdf
        return self._html_to_pdf(html, options)
    
    def _build_html_report(self, employees, graphs, chart_images, analytics_data, options):
        """Build HTML report content."""
        kpi = analytics_data.get('kpi', {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{options.get('report_title', 'Laporan Analytics')}</title>
            <style>
                @page {{
                    size: A4 landscape;
                    margin: 15mm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}
                .cover-page {{
                    text-align: center;
                    padding-top: 150px;
                    page-break-after: always;
                }}
                .cover-title {{
                    font-size: 28pt;
                    color: #714B67;
                    margin-bottom: 20px;
                }}
                .cover-subtitle {{
                    font-size: 14pt;
                    color: #666;
                    margin-bottom: 40px;
                }}
                .cover-info {{
                    font-size: 12pt;
                    color: #888;
                }}
                .summary-page {{
                    page-break-after: always;
                }}
                .summary-title {{
                    font-size: 18pt;
                    color: #714B67;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .kpi-grid {{
                    display: flex;
                    justify-content: center;
                    gap: 30px;
                    flex-wrap: wrap;
                    margin-bottom: 40px;
                }}
                .kpi-card {{
                    background: linear-gradient(135deg, #714B67, #8B5A7C);
                    color: white;
                    padding: 25px 40px;
                    border-radius: 10px;
                    text-align: center;
                    min-width: 150px;
                }}
                .kpi-value {{
                    font-size: 32pt;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .kpi-label {{
                    font-size: 11pt;
                    opacity: 0.9;
                }}
                .charts-container {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 20px;
                }}
                .chart-box {{
                    background: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 15px;
                    text-align: center;
                    width: 45%;
                    page-break-inside: avoid;
                }}
                .chart-box.single {{
                    width: 70%;
                    margin: 0 auto;
                    page-break-after: always;
                }}
                .chart-title {{
                    font-size: 14pt;
                    color: #714B67;
                    margin-bottom: 10px;
                    font-weight: bold;
                }}
                .chart-image {{
                    max-width: 100%;
                    height: auto;
                }}
                .chart-description {{
                    font-size: 10pt;
                    color: #666;
                    margin-top: 10px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #e0e0e0;
                    text-align: center;
                    font-size: 9pt;
                    color: #888;
                }}
                .page-break {{
                    page-break-after: always;
                }}
            </style>
        </head>
        <body>
        """
        
        # Cover page
        if options.get('include_cover', True):
            html += f"""
            <div class="cover-page">
                <div class="cover-title">{options.get('report_title', 'Laporan Analytics Karyawan')}</div>
                <div class="cover-subtitle">{self.env.company.name}</div>
                <div class="cover-info">
                    <p>Periode: {options.get('date_from', '-')} s/d {options.get('date_to', '-')}</p>
                    <p>Departemen: {options.get('department_names', 'Semua')}</p>
                    <p>Dicetak pada: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    <p>Oleh: {self.env.user.name}</p>
                </div>
            </div>
            """
        
        # Summary page
        if options.get('include_summary', True):
            html += f"""
            <div class="summary-page">
                <div class="summary-title">Ringkasan Karyawan</div>
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-value">{kpi.get('total', 0)}</div>
                        <div class="kpi-label">Total Karyawan</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{kpi.get('active', 0)}</div>
                        <div class="kpi-label">Karyawan Aktif</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{kpi.get('avg_age', 0)}</div>
                        <div class="kpi-label">Rata-rata Usia (th)</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{kpi.get('avg_tenure', 0)}</div>
                        <div class="kpi-label">Rata-rata Masa Kerja (th)</div>
                    </div>
                </div>
            </div>
            """
        
        # Charts
        layout = options.get('layout_type', 'two_columns')
        chart_class = 'single' if layout == 'single_column' else ''
        
        html += '<div class="charts-container">'
        
        for i, graph in enumerate(graphs):
            code = graph['code']
            img_data = chart_images.get(code)
            
            if img_data:
                img_b64 = base64.b64encode(img_data).decode('utf-8')
                html += f"""
                <div class="chart-box {chart_class}">
                    <div class="chart-title">{graph['name']}</div>
                    <img class="chart-image" src="data:image/png;base64,{img_b64}" alt="{graph['name']}"/>
                    <div class="chart-description">{graph.get('description', '')}</div>
                </div>
                """
            else:
                html += f"""
                <div class="chart-box {chart_class}">
                    <div class="chart-title">{graph['name']}</div>
                    <p style="color: #999; padding: 50px;">Grafik tidak tersedia</p>
                    <div class="chart-description">{graph.get('description', '')}</div>
                </div>
                """
            
            # Page break for single column layout
            if layout == 'single_column' and i < len(graphs) - 1:
                html += '<div class="page-break"></div>'
        
        html += '</div>'
        
        # Footer
        html += f"""
            <div class="footer">
                <p>Dokumen ini dihasilkan oleh sistem YHC Employee Export</p>
                <p>{self.env.company.name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _html_to_pdf(self, html_content, options):
        """
        Convert HTML to PDF using wkhtmltopdf.
        
        Returns:
            bytes: PDF content
        """
        import subprocess
        
        orientation = options.get('page_orientation', 'landscape')
        
        # Write HTML to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            html_path = f.name
        
        # Create temp file for PDF
        pdf_fd, pdf_path = tempfile.mkstemp(suffix='.pdf')
        os.close(pdf_fd)
        
        try:
            # Run wkhtmltopdf
            cmd = [
                'wkhtmltopdf',
                '--orientation', orientation.title(),
                '--page-size', 'A4',
                '--margin-top', '10mm',
                '--margin-bottom', '10mm',
                '--margin-left', '10mm',
                '--margin-right', '10mm',
                '--encoding', 'UTF-8',
                '--enable-local-file-access',
                '--quiet',
                html_path,
                pdf_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if result.returncode != 0:
                _logger.warning(f"wkhtmltopdf warning: {result.stderr.decode('utf-8', errors='ignore')}")
            
            # Read PDF content
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            if not pdf_content:
                raise UserError(_('Gagal generate PDF'))
            
            return pdf_content
            
        finally:
            # Cleanup
            if os.path.exists(html_path):
                os.unlink(html_path)
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
