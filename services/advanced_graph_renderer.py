# -*- coding: utf-8 -*-
"""
Service: Advanced Graph Renderer
Service untuk rendering grafik ke SVG/PNG untuk PDF export.

PRINSIP:
- Backend rendering menggunakan matplotlib
- SVG sebagai format utama (vector, scalable)
- PNG sebagai fallback dengan resolusi ≥300 DPI
- Konsisten dengan data dari EmployeeAnalyticsService
"""

import base64
import logging
import io
from datetime import datetime, date

from odoo.exceptions import UserError
from odoo import _

_logger = logging.getLogger(__name__)

# Check matplotlib availability
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.figure import Figure
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    _logger.warning("matplotlib not installed. Install with: pip install matplotlib numpy")


class AdvancedGraphRenderer:
    """
    Advanced graph renderer untuk PDF export.
    
    Mendukung:
    - Bar Chart (single & stacked)
    - Line Chart (single & multi-series)
    - Pie Chart
    - Horizontal Bar Chart
    
    Output:
    - SVG (default, vector format)
    - PNG (fallback, ≥300 DPI)
    """
    
    # Default configuration
    DEFAULT_DPI = 300
    DEFAULT_FIGSIZE = (10, 6)
    FONT_FAMILY = 'sans-serif'
    TITLE_FONTSIZE = 14
    LABEL_FONTSIZE = 10
    VALUE_FONTSIZE = 9
    
    def __init__(self, env):
        """Initialize renderer."""
        self.env = env
        self.dpi = self.DEFAULT_DPI
        self.figsize = self.DEFAULT_FIGSIZE
        
        if not HAS_MATPLOTLIB:
            _logger.warning("Matplotlib not available. Graph rendering will be limited.")
    
    def set_dpi(self, dpi):
        """Set DPI untuk output."""
        self.dpi = max(dpi, 150)  # Minimum 150 DPI
        return self
    
    def set_figsize(self, width, height):
        """Set figure size in inches."""
        self.figsize = (width, height)
        return self
    
    def render_chart(self, graph_def, data, output_format='svg'):
        """
        Render chart berdasarkan definisi grafik.
        
        Args:
            graph_def: Definisi grafik dari GRAPH_REGISTRY
            data: Data dari EmployeeAnalyticsService
            output_format: 'svg' atau 'png'
            
        Returns:
            tuple: (bytes, mimetype)
        """
        if not HAS_MATPLOTLIB:
            return self._fallback_render(graph_def, data)
        
        chart_type = graph_def.get('chart_type', 'bar')
        
        # Route ke method yang sesuai
        if chart_type == 'bar':
            if graph_def.get('is_stacked') or 'datasets' in data:
                return self._render_stacked_bar(graph_def, data, output_format)
            return self._render_bar(graph_def, data, output_format)
        elif chart_type == 'line':
            return self._render_line(graph_def, data, output_format)
        elif chart_type == 'pie':
            return self._render_pie(graph_def, data, output_format)
        elif chart_type == 'horizontal_bar':
            return self._render_horizontal_bar(graph_def, data, output_format)
        else:
            return self._render_bar(graph_def, data, output_format)
    
    def _render_bar(self, graph_def, data, output_format='svg'):
        """Render simple bar chart."""
        fig, ax = plt.subplots(figsize=self.figsize)
        
        labels = data.get('labels', [])
        values = data.get('data', [])
        colors = data.get('colors', graph_def.get('colors', ['#714B67']))
        
        if not labels or not values:
            return self._render_empty_chart(graph_def, output_format)
        
        # Create bars
        x = np.arange(len(labels))
        bars = ax.bar(x, values, color=colors[:len(labels)])
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.annotate(
                f'{int(val)}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=self.VALUE_FONTSIZE
            )
        
        # Configure axes
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=self.LABEL_FONTSIZE)
        ax.set_ylabel('Jumlah', fontsize=self.LABEL_FONTSIZE)
        ax.set_title(graph_def.get('name', 'Chart'), fontsize=self.TITLE_FONTSIZE, fontweight='bold')
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig, output_format)
    
    def _render_stacked_bar(self, graph_def, data, output_format='svg'):
        """Render stacked/grouped bar chart."""
        fig, ax = plt.subplots(figsize=self.figsize)
        
        labels = data.get('labels', [])
        datasets = data.get('datasets', [])
        colors = data.get('colors', graph_def.get('colors', ['#714B67', '#017E84']))
        
        if not labels or not datasets:
            return self._render_empty_chart(graph_def, output_format)
        
        x = np.arange(len(labels))
        width = 0.35
        multiplier = 0
        
        for i, dataset in enumerate(datasets):
            offset = width * multiplier
            values = dataset.get('data', [])
            color = colors[i % len(colors)]
            
            bars = ax.bar(
                x + offset, values, width,
                label=dataset.get('label', f'Series {i+1}'),
                color=color
            )
            
            # Add value labels
            for bar, val in zip(bars, values):
                height = bar.get_height()
                if height > 0:
                    ax.annotate(
                        f'{int(val)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=self.VALUE_FONTSIZE - 1
                    )
            
            multiplier += 1
        
        # Configure axes
        ax.set_xticks(x + width * (len(datasets) - 1) / 2)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=self.LABEL_FONTSIZE)
        ax.set_ylabel('Jumlah', fontsize=self.LABEL_FONTSIZE)
        ax.set_title(graph_def.get('name', 'Chart'), fontsize=self.TITLE_FONTSIZE, fontweight='bold')
        ax.legend(loc='upper right', fontsize=self.LABEL_FONTSIZE - 1)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig, output_format)
    
    def _render_line(self, graph_def, data, output_format='svg'):
        """Render line chart."""
        fig, ax = plt.subplots(figsize=self.figsize)
        
        labels = data.get('labels', [])
        datasets = data.get('datasets', [])
        
        # Handle single dataset format
        if 'data' in data and not datasets:
            datasets = [{'label': 'Data', 'data': data['data']}]
        
        colors = data.get('colors', graph_def.get('colors', ['#714B67']))
        
        if not labels:
            return self._render_empty_chart(graph_def, output_format)
        
        x = np.arange(len(labels))
        
        for i, dataset in enumerate(datasets):
            values = dataset.get('data', [])
            color = dataset.get('borderColor', colors[i % len(colors)])
            
            ax.plot(
                x, values,
                marker='o',
                label=dataset.get('label', f'Series {i+1}'),
                color=color,
                linewidth=2,
                markersize=6
            )
            
            # Add value labels at points
            for j, val in enumerate(values):
                ax.annotate(
                    f'{int(val)}',
                    xy=(j, val),
                    xytext=(0, 8),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=self.VALUE_FONTSIZE - 1
                )
        
        # Configure axes
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=self.LABEL_FONTSIZE)
        ax.set_ylabel('Jumlah', fontsize=self.LABEL_FONTSIZE)
        ax.set_title(graph_def.get('name', 'Chart'), fontsize=self.TITLE_FONTSIZE, fontweight='bold')
        
        if len(datasets) > 1:
            ax.legend(loc='upper left', fontsize=self.LABEL_FONTSIZE - 1)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig, output_format)
    
    def _render_pie(self, graph_def, data, output_format='svg'):
        """Render pie chart."""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        labels = data.get('labels', [])
        values = data.get('data', [])
        colors = data.get('colors', graph_def.get('colors', ['#714B67', '#017E84']))
        
        if not labels or not values or sum(values) == 0:
            return self._render_empty_chart(graph_def, output_format)
        
        # Filter out zero values
        filtered = [(l, v, c) for l, v, c in zip(labels, values, colors[:len(labels)]) if v > 0]
        if not filtered:
            return self._render_empty_chart(graph_def, output_format)
        
        labels, values, colors = zip(*filtered)
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,  # We'll add custom labels
            autopct=lambda pct: f'{pct:.1f}%' if pct >= 5 else '',
            colors=colors,
            startangle=90,
            pctdistance=0.75
        )
        
        # Style autotexts
        for autotext in autotexts:
            autotext.set_fontsize(self.VALUE_FONTSIZE)
            autotext.set_fontweight('bold')
        
        # Add legend
        legend_labels = [f'{l}: {v}' for l, v in zip(labels, values)]
        ax.legend(
            wedges, legend_labels,
            title="Kategori",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=self.LABEL_FONTSIZE - 1
        )
        
        ax.set_title(graph_def.get('name', 'Chart'), fontsize=self.TITLE_FONTSIZE, fontweight='bold')
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig, output_format)
    
    def _render_horizontal_bar(self, graph_def, data, output_format='svg'):
        """Render horizontal bar chart."""
        fig, ax = plt.subplots(figsize=self.figsize)
        
        labels = data.get('labels', [])
        values = data.get('data', [])
        colors = data.get('colors', graph_def.get('colors', ['#714B67']))
        
        if not labels or not values:
            return self._render_empty_chart(graph_def, output_format)
        
        y = np.arange(len(labels))
        bars = ax.barh(y, values, color=colors[:len(labels)])
        
        # Add value labels
        for bar, val in zip(bars, values):
            width = bar.get_width()
            ax.annotate(
                f'{int(val)}',
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(5, 0),
                textcoords="offset points",
                ha='left', va='center',
                fontsize=self.VALUE_FONTSIZE
            )
        
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=self.LABEL_FONTSIZE)
        ax.set_xlabel('Jumlah', fontsize=self.LABEL_FONTSIZE)
        ax.set_title(graph_def.get('name', 'Chart'), fontsize=self.TITLE_FONTSIZE, fontweight='bold')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig, output_format)
    
    def _render_empty_chart(self, graph_def, output_format='svg'):
        """Render placeholder untuk chart kosong."""
        fig, ax = plt.subplots(figsize=self.figsize)
        
        ax.text(
            0.5, 0.5,
            'Tidak ada data tersedia',
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes,
            fontsize=14,
            color='gray'
        )
        
        ax.set_title(graph_def.get('name', 'Chart'), fontsize=self.TITLE_FONTSIZE, fontweight='bold')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        plt.tight_layout()
        
        return self._fig_to_bytes(fig, output_format)
    
    def _fig_to_bytes(self, fig, output_format='svg'):
        """Convert matplotlib figure to bytes."""
        buffer = io.BytesIO()
        
        if output_format == 'svg':
            fig.savefig(buffer, format='svg', bbox_inches='tight')
            mimetype = 'image/svg+xml'
        else:
            fig.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight')
            mimetype = 'image/png'
        
        plt.close(fig)
        buffer.seek(0)
        
        return buffer.getvalue(), mimetype
    
    def _fallback_render(self, graph_def, data):
        """Fallback rendering jika matplotlib tidak tersedia."""
        # Return simple placeholder SVG
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
    <rect width="100%" height="100%" fill="#f5f5f5"/>
    <text x="400" y="50" text-anchor="middle" font-size="18" font-weight="bold">
        {graph_def.get('name', 'Chart')}
    </text>
    <text x="400" y="300" text-anchor="middle" font-size="14" fill="#666">
        Grafik tidak tersedia (matplotlib tidak terinstall)
    </text>
    <text x="400" y="330" text-anchor="middle" font-size="12" fill="#999">
        Total: {data.get('total', 0)} records
    </text>
</svg>'''
        
        return svg.encode('utf-8'), 'image/svg+xml'
    
    def render_multiple_charts(self, charts_config, output_format='svg'):
        """
        Render multiple charts dan return sebagai list.
        
        Args:
            charts_config: List of dicts with 'graph_def' and 'data'
            output_format: 'svg' or 'png'
            
        Returns:
            list: List of (bytes, mimetype, graph_code) tuples
        """
        results = []
        
        for config in charts_config:
            graph_def = config.get('graph_def', {})
            data = config.get('data', {})
            
            try:
                content, mimetype = self.render_chart(graph_def, data, output_format)
                results.append({
                    'content': content,
                    'mimetype': mimetype,
                    'code': graph_def.get('code', 'unknown'),
                    'name': graph_def.get('name', 'Chart'),
                    'description': graph_def.get('description', ''),
                    'base64': base64.b64encode(content).decode('utf-8'),
                })
            except Exception as e:
                _logger.error(f"Error rendering chart {graph_def.get('code')}: {e}")
                # Add error placeholder
                results.append({
                    'content': None,
                    'mimetype': None,
                    'code': graph_def.get('code', 'unknown'),
                    'name': graph_def.get('name', 'Chart'),
                    'error': str(e),
                })
        
        return results
