# -*- coding: utf-8 -*-
"""
Model: hr.employee.export.template
Template laporan untuk export data karyawan.

Model ini menyimpan template yang mendefinisikan field-field
yang akan di-export dan format header-nya.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import logging

_logger = logging.getLogger(__name__)

# ==================== Field Mapping Constants ====================
FIELD_MAPPING = {
    'identity': {
        'nrp': 'NRP',
        'name': 'Nama Lengkap',
        'gelar': 'Gelar',
        'nama_ktp': 'Nama KTP',
        'nik': 'NIK',
        'no_kk': 'No. KK',
        'no_akta_lahir': 'No. Akta Lahir',
        'alamat_ktp': 'Alamat KTP',
        'place_of_birth': 'Tempat Lahir',
        'birthday': 'Tanggal Lahir',
        'age': 'Usia',
        'gender': 'Jenis Kelamin',
        'blood_type': 'Golongan Darah',
        'religion': 'Agama',
        'status_kawin': 'Status Pernikahan',
    },
    'employment': {
        'department_id.name': 'Unit Kerja',
        'job_id.name': 'Jabatan',
        'area_kerja_id.name': 'Area Kerja',
        'golongan_id.name': 'Golongan',
        'grade_id.name': 'Grade',
        'employee_type_id.name': 'Tipe Pegawai',
        'employee_category_id.name': 'Jenis Pegawai',
        'employment_status': 'Status Kepegawaian',
        'first_contract_date': 'Tanggal Masuk',
        'service_length': 'Masa Kerja (Tahun)',
    },
    'family': {
        'status_kawin': 'Status Pernikahan',
        'spouse_name': 'Nama Pasangan',
        'spouse_nik': 'NIK Pasangan',
        'spouse_birthday': 'Tanggal Lahir Pasangan',
        'jlh_anggota_keluarga': 'Jumlah Anggota Keluarga',
    },
    'bpjs': {
        'bpjs_ids.bpjs_type': 'Jenis BPJS',
        'bpjs_ids.number': 'Nomor BPJS',
        'bpjs_ids.faskes_tk1': 'Faskes Tingkat 1',
        'bpjs_ids.kelas': 'Kelas BPJS',
    },
    'education': {
        'education_ids.certificate': 'Jenjang Pendidikan',
        'education_ids.study_school': 'Institusi',
        'education_ids.major': 'Jurusan',
        'education_ids.date_start': 'Tahun Masuk',
        'education_ids.date_end': 'Tahun Lulus',
    },
    'payroll': {
        'payroll_id.bank_name': 'Nama Bank',
        'payroll_id.bank_account': 'Nomor Rekening',
        'payroll_id.npwp': 'NPWP',
        'payroll_id.efin': 'EFIN',
    },
    'training': {
        'training_certificate_ids.name': 'Nama Pelatihan',
        'training_certificate_ids.jenis_pelatihan': 'Jenis Pelatihan',
        'training_certificate_ids.metode': 'Metode',
        'training_certificate_ids.date_start': 'Tanggal Mulai',
        'training_certificate_ids.date_end': 'Tanggal Selesai',
    },
    'reward_punishment': {
        'reward_punishment_ids.type': 'Tipe',
        'reward_punishment_ids.name': 'Nama',
        'reward_punishment_ids.date': 'Tanggal',
        'reward_punishment_ids.description': 'Keterangan',
    },
}


class HrEmployeeExportTemplate(models.Model):
    """
    Model untuk menyimpan template export data karyawan.
    
    Template ini mendefinisikan field apa saja yang akan di-export
    dan bagaimana format headernya.
    """
    _name = 'hr.employee.export.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Template Export Karyawan'
    _order = 'sequence, name'

    # ==================== Basic Information ====================
    name = fields.Char(
        string='Nama Template',
        required=True,
        tracking=True,
        help='Nama template laporan'
    )
    code = fields.Char(
        string='Kode Template',
        required=True,
        help='Kode unik untuk mengidentifikasi template'
    )
    sequence = fields.Integer(
        string='Urutan',
        default=10,
        help='Urutan tampil di daftar'
    )
    active = fields.Boolean(
        string='Aktif',
        default=True,
        help='Jika tidak aktif, template tidak akan muncul di daftar pilihan'
    )
    description = fields.Text(
        string='Deskripsi',
        help='Deskripsi tentang template ini'
    )
    is_system = fields.Boolean(
        string='Template Sistem',
        default=False,
        help='Template sistem tidak dapat dihapus'
    )
    is_default = fields.Boolean(
        string='Template Default',
        default=False,
        help='Template default yang tersedia untuk semua user'
    )

    # ==================== Template Type ====================
    template_type = fields.Selection(
        selection=[
            ('demographic', 'Demografi'),
            ('employment', 'Kepegawaian'),
            ('bpjs', 'BPJS'),
            ('education', 'Pendidikan'),
            ('payroll', 'Payroll'),
            ('family', 'Keluarga'),
            ('training', 'Pelatihan'),
            ('reward_punishment', 'Reward & Punishment'),
            ('complete', 'Lengkap'),
            ('regulatory', 'Regulasi'),
        ],
        string='Tipe Template',
        required=True,
        tracking=True,
        help='Kategori template berdasarkan jenis data'
    )

    # ==================== Field Mapping ====================
    field_mapping = fields.Text(
        string='Field Mapping (JSON)',
        help='Mapping field dalam format JSON. Keys adalah field name, values adalah header label.'
    )
    field_ids = fields.Many2many(
        comodel_name='ir.model.fields',
        relation='hr_export_template_field_rel',
        column1='template_id',
        column2='field_id',
        string='Fields',
        domain="[('model', '=', 'hr.employee')]",
        help='Fields yang akan di-export'
    )

    # ==================== Export Options ====================
    include_header = fields.Boolean(
        string='Sertakan Header',
        default=True,
        help='Sertakan baris header pada hasil export'
    )
    date_format = fields.Char(
        string='Format Tanggal',
        default='%d/%m/%Y',
        help='Format untuk field tanggal (Python strftime)'
    )
    empty_value = fields.Char(
        string='Nilai Kosong',
        default='-',
        help='Nilai yang ditampilkan untuk field kosong'
    )

    # ==================== Regulatory Options ====================
    regulatory_type = fields.Selection(
        selection=[
            ('bpjs_kes', 'BPJS Kesehatan'),
            ('bpjs_tk', 'BPJS Ketenagakerjaan'),
            ('pajak', 'Pajak (1721-A1)'),
            ('disnaker', 'Wajib Lapor Ketenagakerjaan'),
        ],
        string='Tipe Regulasi',
        help='Tipe format regulasi (hanya untuk template regulatory)'
    )

    # ==================== Computed Fields ====================
    field_count = fields.Integer(
        string='Jumlah Field',
        compute='_compute_field_count',
        help='Jumlah field yang di-mapping'
    )

    # ==================== Constraints ====================
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Kode template harus unik!'),
    ]

    # ==================== Compute Methods ====================
    @api.depends('field_mapping')
    def _compute_field_count(self):
        """Menghitung jumlah field dalam mapping."""
        for record in self:
            if record.field_mapping:
                try:
                    mapping = json.loads(record.field_mapping)
                    record.field_count = len(mapping)
                except (json.JSONDecodeError, TypeError):
                    record.field_count = 0
            else:
                record.field_count = 0

    # ==================== Onchange Methods ====================
    @api.onchange('template_type')
    def _onchange_template_type(self):
        """Auto-fill field mapping berdasarkan tipe template."""
        if self.template_type and not self.field_mapping:
            self.field_mapping = self._get_default_mapping_for_type(self.template_type)

    # ==================== CRUD Methods ====================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create untuk auto-generate mapping jika kosong."""
        for vals in vals_list:
            if not vals.get('field_mapping') and vals.get('template_type'):
                vals['field_mapping'] = self._get_default_mapping_for_type(vals['template_type'])
        return super().create(vals_list)

    def unlink(self):
        """Prevent deletion of system templates."""
        for record in self:
            if record.is_system:
                raise UserError(_(
                    "Template sistem '%s' tidak dapat dihapus."
                ) % record.name)
        return super().unlink()

    # ==================== Action Methods ====================
    def action_duplicate_template(self):
        """Duplikasi template dengan nama baru."""
        self.ensure_one()
        new_code = f"{self.code}_COPY"
        counter = 1
        while self.search_count([('code', '=', new_code)]) > 0:
            counter += 1
            new_code = f"{self.code}_COPY_{counter}"
        
        new_template = self.copy({
            'name': _("%s (Copy)") % self.name,
            'code': new_code,
            'is_system': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.export.template',
            'res_id': new_template.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_reset_mapping(self):
        """Reset field mapping ke default."""
        self.ensure_one()
        self.field_mapping = self._get_default_mapping_for_type(self.template_type)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Berhasil'),
                'message': _('Field mapping direset ke default.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_open_mapping_editor(self):
        """Buka editor mapping (TODO: implementasi wizard)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Info'),
                'message': _('Editor mapping visual akan tersedia di versi berikutnya.'),
                'type': 'info',
                'sticky': False,
            }
        }

    # ==================== Helper Methods ====================
    def _get_default_mapping_for_type(self, template_type):
        """
        Mendapatkan default field mapping berdasarkan tipe template.
        
        Args:
            template_type (str): Tipe template
            
        Returns:
            str: JSON string field mapping
        """
        mapping = {}
        
        if template_type == 'demographic':
            mapping = FIELD_MAPPING.get('identity', {})
        elif template_type == 'employment':
            mapping = FIELD_MAPPING.get('employment', {})
        elif template_type == 'bpjs':
            # Gabungkan identity dasar dengan bpjs
            mapping = {
                'nrp': 'NRP',
                'name': 'Nama Lengkap',
                'nik': 'NIK',
            }
            mapping.update(FIELD_MAPPING.get('bpjs', {}))
        elif template_type == 'education':
            mapping = {
                'nrp': 'NRP',
                'name': 'Nama Lengkap',
            }
            mapping.update(FIELD_MAPPING.get('education', {}))
        elif template_type == 'payroll':
            mapping = {
                'nrp': 'NRP',
                'name': 'Nama Lengkap',
                'nik': 'NIK',
            }
            mapping.update(FIELD_MAPPING.get('payroll', {}))
        elif template_type == 'family':
            mapping = {
                'nrp': 'NRP',
                'name': 'Nama Lengkap',
            }
            mapping.update(FIELD_MAPPING.get('family', {}))
        elif template_type == 'training':
            mapping = {
                'nrp': 'NRP',
                'name': 'Nama Lengkap',
                'department_id.name': 'Unit Kerja',
            }
            mapping.update(FIELD_MAPPING.get('training', {}))
        elif template_type == 'reward_punishment':
            mapping = {
                'nrp': 'NRP',
                'name': 'Nama Lengkap',
                'department_id.name': 'Unit Kerja',
            }
            mapping.update(FIELD_MAPPING.get('reward_punishment', {}))
        elif template_type == 'complete':
            # Gabungkan semua mapping
            for category in ['identity', 'employment', 'bpjs', 'education', 'payroll', 'family', 'training', 'reward_punishment']:
                mapping.update(FIELD_MAPPING.get(category, {}))
        elif template_type == 'regulatory':
            # Mapping dasar untuk regulasi
            mapping = {
                'nik': 'NIK',
                'name': 'Nama Lengkap',
                'birthday': 'Tanggal Lahir',
                'gender': 'Jenis Kelamin',
            }
        
        return json.dumps(mapping, indent=2, ensure_ascii=False)

    def get_field_mapping(self):
        """
        Parse dan return field mapping sebagai dictionary.
        
        Returns:
            dict: Field mapping dictionary
        """
        self.ensure_one()
        if self.field_mapping:
            try:
                return json.loads(self.field_mapping)
            except (json.JSONDecodeError, TypeError):
                _logger.warning(f"Invalid JSON in field_mapping for template {self.code}")
                return {}
        return {}

    def get_headers(self):
        """
        Mendapatkan list header untuk export.
        
        Returns:
            list: List of header strings
        """
        mapping = self.get_field_mapping()
        return list(mapping.values())

    def get_fields(self):
        """
        Mendapatkan list field untuk export.
        
        Returns:
            list: List of field names
        """
        mapping = self.get_field_mapping()
        return list(mapping.keys())

    def get_export_data(self, employees, config=None):
        """
        Mengambil data dari employees sesuai template.
        
        Args:
            employees (recordset): hr.employee recordset
            config (recordset): hr.employee.export.config optional
            
        Returns:
            list: List of dictionaries dengan data export
        """
        self.ensure_one()
        mapping = self.get_field_mapping()
        result = []
        
        for employee in employees:
            row = {}
            for field_path, header in mapping.items():
                value = self._get_field_value(employee, field_path)
                row[header] = value if value else self.empty_value
            result.append(row)
        
        return result

    def _get_field_value(self, record, field_path):
        """
        Mengambil nilai field dari record, support dot notation.
        
        Args:
            record: Odoo record
            field_path (str): Path field dengan dot notation (e.g., 'department_id.name')
            
        Returns:
            str: Nilai field
        """
        try:
            parts = field_path.split('.')
            value = record
            
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
                
                # Handle empty recordset
                if hasattr(value, '_name') and not value:
                    return None
            
            # Format nilai
            if isinstance(value, bool):
                return 'Ya' if value else 'Tidak'
            elif hasattr(value, 'strftime'):  # Date/Datetime
                return value.strftime(self.date_format or '%d/%m/%Y')
            elif hasattr(value, '_name'):  # Recordset
                if len(value) > 1:
                    return ', '.join(value.mapped('name') if 'name' in value._fields else value.mapped('display_name'))
                return value.name if hasattr(value, 'name') else str(value.display_name if value else '')
            else:
                return str(value) if value else None
                
        except Exception as e:
            _logger.warning(f"Error getting field value for {field_path}: {e}")
            return None

    def toggle_active(self):
        """Toggle status aktif template."""
        for record in self:
            record.active = not record.active

    # TODO: Implementasi field_mapping dan method generate di Fase 3
