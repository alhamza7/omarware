# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


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
        """Re-sync this group from SAP to get all UoMs"""
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
            
            # Process each definition
            uom_sync_model = self.env['sap.uom.sync']
            created_count = 0
            updated_count = 0
            
            for defn in definitions:
                alternate_uom_entry = defn.get('AlternateUoM', 0)
                if not alternate_uom_entry:
                    continue
                
                # Check if exists
                existing = uom_sync_model.search([
                    ('backend_id', '=', self.backend_id.id),
                    ('sap_uom_entry', '=', alternate_uom_entry)
                ], limit=1)
                
                if not existing:
                    # Fetch UoM details and create
                    try:
                        uom_detail = connection.get(f'UnitOfMeasurements({alternate_uom_entry})', {})
                        uom_code = uom_detail.get('Code')
                        uom_name = uom_detail.get('Name', uom_code)
                        
                        # Calculate factor
                        base_qty = float(defn.get('BaseQuantity', 1.0))
                        alt_qty = float(defn.get('AlternateQuantity', 1.0))
                        factor = base_qty / alt_qty if alt_qty != 0 else 1.0
                        
                        # Create UoM in Odoo
                        odoo_uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
                        if not odoo_uom:
                            odoo_uom = self.env['uom.uom'].create({
                                'name': uom_name,
                                'factor': factor,
                                'rounding': 0.01,
                                'active': True,
                            })
                        
                        # Create sync record
                        uom_sync_model.create({
                            'backend_id': self.backend_id.id,
                            'sap_uom_id': uom_code,
                            'sap_uom_name': uom_name,
                            'sap_uom_entry': alternate_uom_entry,
                            'sap_group_ids': [(4, self.id)],  # Many2many link
                            'odoo_uom_id': odoo_uom.id,
                            'sync_direction': 'sap_to_odoo',
                            'sync_status': 'success',
                            'last_sync': fields.Datetime.now(),
                        })
                        
                        created_count += 1
                    except Exception as e:
                        _logger.error(f"Error creating UoM {alternate_uom_entry}: {str(e)}")
                else:
                    # Update existing - add to groups (Many2many)
                    if self.id not in existing.sap_group_ids.ids:
                        existing.write({
                            'sap_group_ids': [(4, self.id)]  # Add link
                        })
                        updated_count += 1
            
            # Update last sync
            self.last_sync = fields.Datetime.now()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Complete',
                    'message': f'Created {created_count} UoMs, Updated {updated_count} links',
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

