# -*- coding: utf-8 -*-
"""
Graph Registry untuk yhc_employee_export.

Registry terpusat untuk definisi grafik yang digunakan oleh:
- Dashboard OWL
- Export PDF berbasis grafik

Single source of truth untuk semua grafik analytics.
"""

# Warna default untuk chart (Odoo-like palette)
CHART_COLORS = [
    '#714B67',  # Odoo purple
    '#017E84',  # Teal
    '#E6007E',  # Pink
    '#F39C12',  # Orange
    '#27AE60',  # Green
    '#3498DB',  # Blue
    '#9B59B6',  # Purple
    '#E74C3C',  # Red
    '#1ABC9C',  # Cyan
    '#34495E',  # Dark gray
]

# Registry definisi grafik
GRAPH_REGISTRY = {
    # ===== Grafik Demografis =====
    'G01': {
        'code': 'G01',
        'name': 'Distribusi Gender',
        'chart_type': 'pie',
        'method': 'get_gender_distribution',
        'description': 'Perbandingan karyawan pria vs wanita',
        'category': 'demographic',
        'colors': ['#714B67', '#017E84', '#E6007E'],
    },
    'G02': {
        'code': 'G02',
        'name': 'Distribusi Usia',
        'chart_type': 'bar',
        'method': 'get_age_distribution',
        'description': 'Pengelompokan usia karyawan (< 25, 25-34, dst)',
        'category': 'demographic',
        'colors': CHART_COLORS,
    },
    'G03': {
        'code': 'G03',
        'name': 'Distribusi Agama',
        'chart_type': 'pie',
        'method': 'get_religion_distribution',
        'description': 'Komposisi agama karyawan',
        'category': 'demographic',
        'colors': CHART_COLORS,
    },
    'G04': {
        'code': 'G04',
        'name': 'Status Pernikahan',
        'chart_type': 'pie',
        'method': 'get_marital_distribution',
        'description': 'Distribusi status pernikahan (Kawin, Lajang, Cerai)',
        'category': 'demographic',
        'colors': ['#27AE60', '#3498DB', '#E74C3C', '#F39C12'],
    },
    
    # ===== Grafik Ketenagakerjaan =====
    'G06': {
        'code': 'G06',
        'name': 'Karyawan per Departemen',
        'chart_type': 'bar',
        'method': 'get_department_distribution',
        'description': 'Jumlah karyawan tiap unit kerja',
        'category': 'employment',
        'colors': CHART_COLORS,
    },
    'G08': {
        'code': 'G08',
        'name': 'Distribusi Golongan',
        'chart_type': 'bar',
        'method': 'get_golongan_distribution',
        'description': 'Jumlah per golongan pegawai',
        'category': 'employment',
        'colors': CHART_COLORS,
    },
    'G09': {
        'code': 'G09',
        'name': 'Distribusi Grade',
        'chart_type': 'bar',
        'method': 'get_grade_distribution',
        'description': 'Jumlah per grade/pangkat',
        'category': 'employment',
        'colors': CHART_COLORS,
    },
    'G10': {
        'code': 'G10',
        'name': 'Status Kepegawaian',
        'chart_type': 'pie',
        'method': 'get_employment_status_distribution',
        'description': 'Distribusi status (Aktif, Non-aktif, Pensiun)',
        'category': 'employment',
        'colors': ['#27AE60', '#E74C3C', '#F39C12', '#3498DB'],
    },
    'G13': {
        'code': 'G13',
        'name': 'Masa Kerja',
        'chart_type': 'bar',
        'method': 'get_tenure_distribution',
        'description': 'Pengelompokan masa kerja (0-5th, 6-10th, dst)',
        'category': 'employment',
        'colors': CHART_COLORS,
    },
    'G14': {
        'code': 'G14',
        'name': 'Trend Rekrutmen',
        'chart_type': 'line',
        'method': 'get_recruitment_trend',
        'description': 'Jumlah karyawan masuk per bulan',
        'category': 'employment',
        'colors': ['#714B67'],
    },
    
    # ===== Grafik Pendidikan =====
    'G16': {
        'code': 'G16',
        'name': 'Level Pendidikan',
        'chart_type': 'bar',
        'method': 'get_education_distribution',
        'description': 'Distribusi jenjang pendidikan (SD-S3)',
        'category': 'education',
        'colors': CHART_COLORS,
    },
    
    # ===== Grafik Pelatihan =====
    'G20': {
        'code': 'G20',
        'name': 'Pelatihan per Jenis',
        'chart_type': 'pie',
        'method': 'get_training_type_distribution',
        'description': 'Distribusi jenis pelatihan',
        'category': 'training',
        'colors': ['#714B67', '#017E84', '#F39C12', '#27AE60'],
    },
    'G21': {
        'code': 'G21',
        'name': 'Pelatihan per Metode',
        'chart_type': 'pie',
        'method': 'get_training_method_distribution',
        'description': 'Distribusi metode pelatihan (Tatap Muka, Daring, Blended)',
        'category': 'training',
        'colors': ['#3498DB', '#E6007E', '#27AE60'],
    },
}

# Kategori grafik untuk grouping di UI
GRAPH_CATEGORIES = {
    'demographic': {
        'name': 'Demografis',
        'description': 'Grafik data demografis karyawan',
        'graphs': ['G01', 'G02', 'G03', 'G04'],
    },
    'employment': {
        'name': 'Ketenagakerjaan',
        'description': 'Grafik data ketenagakerjaan',
        'graphs': ['G06', 'G08', 'G09', 'G10', 'G13', 'G14'],
    },
    'education': {
        'name': 'Pendidikan',
        'description': 'Grafik data pendidikan',
        'graphs': ['G16'],
    },
    'training': {
        'name': 'Pelatihan',
        'description': 'Grafik data pelatihan',
        'graphs': ['G20', 'G21'],
    },
}


def get_graph_by_code(code):
    """
    Mendapatkan definisi grafik berdasarkan kode.
    
    Args:
        code: Kode grafik (misal: 'G01')
        
    Returns:
        dict: Definisi grafik atau None
    """
    return GRAPH_REGISTRY.get(code)


def get_graphs_by_category(category):
    """
    Mendapatkan daftar grafik berdasarkan kategori.
    
    Args:
        category: Kategori grafik ('demographic', 'employment', dll)
        
    Returns:
        list: List definisi grafik
    """
    cat_info = GRAPH_CATEGORIES.get(category, {})
    graph_codes = cat_info.get('graphs', [])
    return [GRAPH_REGISTRY[code] for code in graph_codes if code in GRAPH_REGISTRY]


def get_all_graph_codes():
    """
    Mendapatkan semua kode grafik yang tersedia.
    
    Returns:
        list: List kode grafik
    """
    return list(GRAPH_REGISTRY.keys())


def get_graph_selection():
    """
    Mendapatkan list tuple untuk Selection field.
    
    Returns:
        list: List of tuples (code, name)
    """
    return [(code, graph['name']) for code, graph in GRAPH_REGISTRY.items()]
