# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SapUomGroupLine(models.Model):
    """
    Stores the SAP UoMGroupDefinitionCollection entries for a group.

    Each row records how many AlternateQty units of a given UoM equal
    BaseQty units of the group's base UoM.  From this we derive
    ``base_equiv`` = BaseQty / AlternateQty, which expresses "how many
    base-UoM units is one unit of this UoM worth".

    Examples for group "كارتون 108 ق" (base = درزن):
        درزن  : alt=1  base=1  → base_equiv = 1.0   (the base unit itself)
        قطعه  : alt=12 base=1  → base_equiv = 1/12 ≈ 0.0833
        كارتون: alt=1  base=9  → base_equiv = 9.0
        10كارتون: alt=1 base=90 → base_equiv = 90.0
    """
    _name = 'sap.uom.group.line'
    _description = 'SAP UoM Group Definition Line'
    _order = 'sap_base_equiv asc'

    group_id = fields.Many2one(
        'sap.uom.group', string='UoM Group',
        required=True, ondelete='cascade', index=True,
    )
    odoo_uom_id = fields.Many2one(
        'uom.uom', string='Odoo UoM',
        required=True, index=True,
    )
    sap_uom_entry = fields.Integer('SAP UoM Entry', index=True)

    # SAP UoMGroupDefinitionCollection fields
    sap_alt_qty = fields.Float(
        'Alternate Qty', default=1.0,
        help="AlternateQuantity from SAP: number of this UoM units",
    )
    sap_base_qty = fields.Float(
        'Base Qty', default=1.0,
        help="BaseQuantity from SAP: number of base-UoM units",
    )
    sap_base_equiv = fields.Float(
        'Base Equivalent', compute='_compute_base_equiv',
        store=True, digits=(16, 6),
        help="sap_base_qty / sap_alt_qty — how many base-UoM units = 1 of this UoM",
    )

    _sql_constraints = [
        ('unique_group_uom', 'UNIQUE(group_id, odoo_uom_id)',
         'A definition line for this UoM already exists in this group.'),
    ]

    @api.depends('sap_alt_qty', 'sap_base_qty')
    def _compute_base_equiv(self):
        for rec in self:
            rec.sap_base_equiv = (
                rec.sap_base_qty / rec.sap_alt_qty
                if rec.sap_alt_qty else 1.0
            )


class SapUomGroup(models.Model):
    """SAP Unit of Measure Group
    
    Represents a UoM Group from SAP that contains multiple related UoMs
    with conversion factors between them.
    
    In Odoo 19, uom.category was removed, so we use this model to maintain
    the SAP Group structure while using Odoo's native relative_uom_id system.
    """
    _name = 'sap.uom.group'
    _description = 'SAP UoM Group'
    _order = 'sap_group_code'
    
    # Basic Information
    name = fields.Char(
        string='Group Name',
        required=True,
        index=True,
        help="Name of the UoM group from SAP"
    )
    sap_group_code = fields.Char(
        string='SAP Group Code',
        required=True,
        index=True,
        help="Unique code for this UoM group in SAP"
    )
    sap_abs_entry = fields.Integer(
        string='SAP AbsEntry',
        help="SAP AbsEntry for this UoM group",
        index=True
    )
    
    # Base UoM
    base_uom_code = fields.Char(
        string='Base UoM Code',
        help="Code of the base/reference UoM in this group"
    )
    base_uom_id = fields.Many2one(
        'uom.uom',
        string='Base UoM',
        help="The reference UoM for this group in Odoo"
    )
    
    # Relations
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='cascade',
        index=True
    )
    uom_ids = fields.Many2many(
        'sap.uom.sync',
        'sap_uom_sync_group_rel',
        'group_id',
        'uom_sync_id',
        string='UoMs in Group',
        help="All UoMs that belong to this group (inverse of Many2many)"
    )
    line_ids = fields.One2many(
        'sap.uom.group.line', 'group_id',
        string='Conversion Factors',
        help="SAP UoMGroupDefinitionCollection — stores AlternateQty/BaseQty per UoM",
    )
    
    # Counts
    uom_count = fields.Integer(
        string='UoM Count',
        compute='_compute_uom_count',
        store=True,
        help="Number of UoMs in this group"
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], string='Sync Status', default='pending', readonly=True)
    
    # Timestamps
    last_sync = fields.Datetime(
        string='Last Sync',
        readonly=True
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_group_code_backend', 
         'UNIQUE(sap_group_code, backend_id)',
         'A UoM group with this code already exists for this backend.'),
    ]
    
    @api.depends('uom_ids')
    def _compute_uom_count(self):
        """Compute number of UoMs in this group"""
        for record in self:
            record.uom_count = len(record.uom_ids)
    
    def name_get(self):
        """Display name with UoM count"""
        result = []
        for record in self:
            name = f"{record.name} ({record.uom_count} UoMs)"
            result.append((record.id, name))
        return result
    
    def action_view_uoms(self):
        """Action to view UoMs in this group"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'UoMs in {self.name}',
            'res_model': 'sap.uom.sync',
            'view_mode': 'tree,form',
            'domain': [('sap_group_ids', 'in', [self.id])],  # Many2many domain
            'context': {
                'default_sap_group_ids': [(4, self.id)],
                'default_backend_id': self.backend_id.id,
            }
        }
    
    def action_sync_from_sap(self):
        """Re-sync this group from SAP to get all UoMs and store conversion factors."""
        self.ensure_one()
        try:
            connection = self.backend_id.get_connection()
            if not connection:
                raise UserError("Cannot connect to SAP")
            
            # Fetch group details
            group_data = connection.get(f'UnitOfMeasurementGroups({self.sap_abs_entry})', {})
            definitions = group_data.get('UoMGroupDefinitionCollection', [])

            if not definitions:
                raise UserError(f"No UoM definitions found for group {self.name}")

            uom_sync_model = self.env['sap.uom.sync']
            line_model = self.env['sap.uom.group.line']
            created_count = 0
            updated_count = 0

            for defn in definitions:
                alternate_uom_entry = defn.get('AlternateUoM', 0)
                if not alternate_uom_entry:
                    continue

                alt_qty = float(defn.get('AlternateQuantity', 1.0))
                base_qty = float(defn.get('BaseQuantity', 1.0))
                factor = base_qty / alt_qty if alt_qty != 0 else 1.0

                existing = uom_sync_model.search([
                    ('backend_id', '=', self.backend_id.id),
                    ('sap_uom_entry', '=', alternate_uom_entry)
                ], limit=1)

                if not existing:
                    try:
                        uom_detail = connection.get(f'UnitOfMeasurements({alternate_uom_entry})', {})
                        uom_code = uom_detail.get('Code')
                        uom_name = uom_detail.get('Name', uom_code)

                        odoo_uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
                        if not odoo_uom:
                            odoo_uom = self.env['uom.uom'].create({
                                'name': uom_name,
                                'factor': factor,
                                'rounding': 0.01,
                                'active': True,
                            })

                        existing = uom_sync_model.create({
                            'backend_id': self.backend_id.id,
                            'sap_uom_id': uom_code,
                            'sap_uom_name': uom_name,
                            'sap_uom_entry': alternate_uom_entry,
                            'sap_group_ids': [(4, self.id)],
                            'odoo_uom_id': odoo_uom.id,
                            'sync_direction': 'sap_to_odoo',
                            'sync_status': 'success',
                            'last_sync': fields.Datetime.now(),
                        })
                        created_count += 1
                    except Exception as e:
                        _logger.error(f"Error creating UoM {alternate_uom_entry}: {str(e)}")
                        continue
                else:
                    if self.id not in existing.sap_group_ids.ids:
                        existing.write({'sap_group_ids': [(4, self.id)]})
                        updated_count += 1

                # Create or update the group definition line (stores conversion factors)
                if existing and existing.odoo_uom_id:
                    existing_line = line_model.search([
                        ('group_id', '=', self.id),
                        ('odoo_uom_id', '=', existing.odoo_uom_id.id),
                    ], limit=1)
                    line_vals = {
                        'sap_uom_entry': alternate_uom_entry,
                        'sap_alt_qty': alt_qty,
                        'sap_base_qty': base_qty,
                    }
                    if existing_line:
                        existing_line.write(line_vals)
                    else:
                        line_model.create({
                            'group_id': self.id,
                            'odoo_uom_id': existing.odoo_uom_id.id,
                            **line_vals,
                        })

            self.last_sync = fields.Datetime.now()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Complete',
                    'message': f'Created {created_count} UoMs, Updated {updated_count} links, factors stored',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Failed',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

