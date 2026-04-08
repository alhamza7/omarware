# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapUomSync(models.Model):
    _name = 'sap.uom.sync'
    _description = 'SAP Unit of Measure Synchronizer'
    _order = 'last_sync desc'
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    connector_id = fields.Many2one('sap.connector', 'Connector')
    odoo_uom_id = fields.Many2one('uom.uom', 'Odoo UoM')
    sap_uom_id = fields.Char('SAP UoM ID', required=True)
    sap_uom_name = fields.Char('SAP UoM Name')
    sap_uom_entry = fields.Integer('SAP UoM Entry', help="SAP UoM Entry number (used in UoMPrices)")
    
    # Group relation - Many2many to allow UoM in multiple groups
    sap_group_ids = fields.Many2many(
        'sap.uom.group',
        'sap_uom_sync_group_rel',
        'uom_sync_id',
        'group_id',
        string='SAP UoM Groups',
        help="The UoM groups this UoM belongs to in SAP (can be multiple)"
    )
    
    # Keep old field for backward compatibility (will be primary group)
    sap_group_id = fields.Many2one(
        'sap.uom.group',
        string='Primary SAP UoM Group',
        compute='_compute_primary_group',
        store=True,
        help="Primary group (first one)"
    )
    
    # Computed fields for display
    odoo_uom_factor = fields.Float(
        string='Conversion Factor',
        compute='_compute_odoo_uom_factor',
        digits=(16, 6),
        help="Conversion factor from Odoo UoM (for display)"
    )
    
    # Sync information
    last_sync = fields.Datetime('Last Sync', readonly=True)
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], 'Sync Status', default='pending', readonly=True)
    sync_direction = fields.Selection([
        ('sap_to_odoo', 'SAP to Odoo'),
        ('odoo_to_sap', 'Odoo to SAP'),
        ('bidirectional', 'Bidirectional'),
    ], 'Sync Direction', default='sap_to_odoo')
    
    # Error handling
    error_message = fields.Text('Error Message', readonly=True)
    retry_count = fields.Integer('Retry Count', default=0)
    max_retries = fields.Integer('Max Retries', default=3)
    
    # Data mapping
    sap_data = fields.Text('SAP Data (JSON)', help="Raw data from SAP")
    odoo_data = fields.Text('Odoo Data (JSON)', help="Raw data from Odoo")
    
    # SQL Constraints to prevent duplicates
    _sql_constraints = [
        ('unique_backend_sap_uom', 'UNIQUE(backend_id, sap_uom_id)',
         'A UoM sync record with this SAP UoM ID already exists for this backend!'),
    ]
    
    @api.depends('sap_group_ids')
    def _compute_primary_group(self):
        """Compute primary group (first one) for backward compatibility"""
        for record in self:
            if record.sap_group_ids:
                record.sap_group_id = record.sap_group_ids[0].id
            else:
                record.sap_group_id = False
    
    @api.depends('odoo_uom_id', 'odoo_uom_id.factor')
    def _compute_odoo_uom_factor(self):
        """Compute conversion factor from Odoo UoM for display"""
        for record in self:
            if record.odoo_uom_id:
                record.odoo_uom_factor = record.odoo_uom_id.factor
            else:
                record.odoo_uom_factor = 0.0
    
    @api.model
    def create(self, vals_list):
        """Override create to set default values"""
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        for vals in vals_list:
            if not vals.get('backend_id') and vals.get('connector_id'):
                connector = self.env['sap.connector'].browse(vals['connector_id'])
                vals['backend_id'] = connector.backend_id.id
        
        return super(SapUomSync, self).create(vals_list)
    
    def sync_from_sap(self):
        """Sync UoM from SAP to Odoo"""
        try:
            # For now, we'll create UoMs based on common SAP UoMs
            # In a real implementation, you would get UoM data from SAP
            uom_data = self._get_sap_uom_data(self.sap_uom_id)
            self.sap_data = str(uom_data)
            
            # Process UoM data
            uom = self._process_uom_data(uom_data)
            
            self.odoo_uom_id = uom.id
            self.sap_uom_name = uom_data.get('name', '')
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced UoM {self.sap_uom_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing UoM {self.sap_uom_id}: {str(e)}")
            raise
    
    def _get_sap_uom_data(self, sap_uom_id):
        """Get UoM data from SAP (simplified for now)"""
        # Common SAP UoM mappings
        uom_mappings = {
            'PCS': {'name': 'Pieces', 'category': 'unit', 'factor': 1.0},
            'KG': {'name': 'Kilogram', 'category': 'weight', 'factor': 1.0},
            'G': {'name': 'Gram', 'category': 'weight', 'factor': 0.001},
            'T': {'name': 'Ton', 'category': 'weight', 'factor': 1000.0},
            'M': {'name': 'Meter', 'category': 'length', 'factor': 1.0},
            'CM': {'name': 'Centimeter', 'category': 'length', 'factor': 0.01},
            'MM': {'name': 'Millimeter', 'category': 'length', 'factor': 0.001},
            'L': {'name': 'Liter', 'category': 'volume', 'factor': 1.0},
            'ML': {'name': 'Milliliter', 'category': 'volume', 'factor': 0.001},
            'BOX': {'name': 'Box', 'category': 'unit', 'factor': 1.0},
            'PKG': {'name': 'Package', 'category': 'unit', 'factor': 1.0},
        }
        
        return uom_mappings.get(sap_uom_id, {
            'name': sap_uom_id,
            'category': 'unit',
            'factor': 1.0
        })
    
    def _process_uom_data(self, uom_data):
        """Process UoM data from SAP and create/update Odoo UoM"""
        try:
            # Map SAP data to Odoo format
            uom_vals = self._map_sap_to_odoo(uom_data)
            
            # Check if UoM already exists
            uom = self.env['uom.uom'].search([
                ('name', '=', uom_data['name'])
            ], limit=1)
            
            if uom:
                # Update existing UoM
                uom.write(uom_vals)
                _logger.info(f"Updated existing UoM: {uom.name}")
            else:
                # Create new UoM
                uom = self.env['uom.uom'].create(uom_vals)
                _logger.info(f"Created new UoM: {uom.name}")
            
            return uom
            
        except Exception as e:
            _logger.error(f"Error processing UoM data: {str(e)}")
            raise
    
    def _map_sap_to_odoo(self, sap_data):
        """Map SAP UoM data to Odoo UoM format"""
        # Get reference UoM
        relative_uom_id = self._get_reference_uom(sap_data['category'])
        
        return {
            'name': sap_data['name'],
            'relative_uom_id': relative_uom_id,
            'relative_factor': sap_data['factor'],
        }
    
    def _get_reference_uom(self, category_type):
        """Get reference UoM by category type"""
        # Map categories to their reference UoM external IDs
        reference_uom_mapping = {
            'unit': 'uom.product_uom_unit',
            'weight': 'uom.product_uom_gram',
            'length': 'uom.product_uom_millimeter',
            'volume': 'uom.product_uom_milliliter',
            'time': 'uom.product_uom_hour',
        }
        
        uom_xmlid = reference_uom_mapping.get(category_type, 'uom.product_uom_unit')
        try:
            return self.env.ref(uom_xmlid).id
        except ValueError:
            # If reference UoM not found, return None (will create a base UoM)
            _logger.warning(f"Reference UoM {uom_xmlid} not found, creating independent UoM")
            return False
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    def sync_to_sap(self):
        """Sync UoM from Odoo to SAP"""
        # Implementation for syncing to SAP
        pass
    
    def button_sync_from_sap(self):
        """Button to sync UoM from SAP"""
        self.ensure_one()
        try:
            self.sync_from_sap()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'UoM {self.sap_uom_name or self.sap_uom_id} synced successfully',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(f"Error syncing UoM: {str(e)}")
    
    @api.model
    def import_all_uoms_from_sap(self, backend):
        """Import all UoMs and UoM Groups from SAP Service Layer"""
        try:
            # Support both backend ID (int) and backend object
            if isinstance(backend, int):
                backend = self.env['sap.backend'].browse(backend)
            
            _logger.info(f"Importing all UoMs and UoM Groups from SAP backend {backend.name}")
            
            # Get connection to SAP
            connection = backend.get_connection()
            if not connection:
                raise UserError("Could not establish connection to SAP backend")
            
            # STEP 1: Get all individual UoMs from SAP FIRST (to create sync records)
            endpoint = "UnitOfMeasurements"
            _logger.info(f"STEP 1: Fetching all UoMs from {endpoint}...")
            uoms_data = connection.get(endpoint, {})
            uoms_data = uoms_data.get('value', [])
            _logger.info(f"✓ Found {len(uoms_data)} UoMs in SAP")
            
            imported_count = 0
            for uom_data in uoms_data:
                try:
                    uom_code = uom_data.get('Code')
                    uom_name = uom_data.get('Name', uom_code)
                    uom_abs_entry = uom_data.get('AbsEntry', 0)  # ✅ Get AbsEntry!
                    
                    _logger.info(f"Processing UoM: {uom_code} (Entry: {uom_abs_entry})")
                    
                    # Check if sync record exists
                    sync_record = self.search([
                        ('backend_id', '=', backend.id),
                        ('sap_uom_id', '=', uom_code)
                    ], limit=1)
                    
                    if not sync_record:
                        sync_record = self.create({
                            'backend_id': backend.id,
                            'sap_uom_id': uom_code,
                            'sap_uom_name': uom_name,
                            'sap_uom_entry': uom_abs_entry,  # ✅ Save Entry!
                            'sync_direction': 'sap_to_odoo',
                        })
                    
                    # Process UoM
                    processed_data = {
                        'name': uom_name,
                        'category': 'unit',  # Default category
                        'factor': 1.0
                    }
                    uom = sync_record._process_uom_data(processed_data)
                    
                    sync_record.write({
                        'odoo_uom_id': uom.id,
                        'sap_uom_name': uom_name,
                        'sap_uom_entry': uom_abs_entry,  # ✅ Save Entry!
                        'sync_status': 'success',
                        'last_sync': fields.Datetime.now(),
                    })
                    
                    imported_count += 1
                    
                except Exception as e:
                    _logger.error(f"Error importing UoM {uom_code}: {str(e)}")
                    continue
            
            _logger.info(f"✓ STEP 1 Complete: Successfully imported {imported_count} UoMs from SAP")
            
            # STEP 2: Now get all UoM Groups and link them to UoMs
            _logger.info(f"STEP 2: Importing UoM Groups and linking to UoMs...")
            uom_groups_data = self._import_uom_groups_from_sap(backend, connection)
            
            _logger.info(f"✓ STEP 2 Complete: Imported {len(uom_groups_data)} UoM Groups from SAP")
            return imported_count
            
        except Exception as e:
            _logger.error(f"Error importing all UoMs: {str(e)}")
            raise
    
    def _import_uom_groups_from_sap(self, backend, connection):
        """Import UoM Groups with conversion factors from SAP"""
        try:
            _logger.info(f"Importing UoM Groups from SAP backend {backend.name}")
            
            # Get all UoM Groups from SAP - fetch ALL without limit
            endpoint = "UnitOfMeasurementGroups"
            _logger.info(f"Fetching ALL UoM Groups from: {endpoint}")
            
            all_groups = []
            skip = 0
            top = 100  # Fetch in batches
            
            while True:
                params = {
                    '$top': top,
                    '$skip': skip,
                    '$orderby': 'Code',
                    '$select': 'AbsEntry,Code,Name,BaseUoM'  # Get basic info only, we'll fetch details separately
                }
                batch_data = connection.get(endpoint, params)
                batch = batch_data.get('value', [])
                
                if not batch:
                    _logger.info(f"No more groups to fetch (empty batch at skip={skip})")
                    break
                
                all_groups.extend(batch)
                _logger.info(f"Fetched {len(batch)} groups (total so far: {len(all_groups)}, skip was: {skip})")
                
                # Increase skip by the number of records fetched (not by top!)
                skip += len(batch)
                
                # Note: SAP may return batches smaller than $top even when more data exists
                # So we DON'T break on len(batch) < top, only on empty batch
                
                # Safety limit
                if skip > 10000:
                    _logger.warning("Reached safety limit of 10000 groups")
                    break
            
            groups_data = all_groups
            _logger.info(f"✓ Found {len(groups_data)} UoM Groups in SAP total")
            
            _logger.info(f"✓ Found {len(groups_data)} UoM Groups in SAP")
            
            imported_groups = []
            total_groups = len(groups_data)
            
            for idx, group_data in enumerate(groups_data, 1):
                try:
                    group_code = group_data.get('Code')
                    group_name = group_data.get('Name', group_code)
                    base_uom = group_data.get('BaseUoM')
                    abs_entry = group_data.get('AbsEntry')
                    
                    _logger.info(f"[{idx}/{total_groups}] Processing: {group_code} - {group_name} (AbsEntry: {abs_entry}, Base: {base_uom})")
                    
                    # Create or get SAP UoM Group record
                    group_record = self._get_or_create_group(
                        backend, group_code, group_name, base_uom, abs_entry
                    )
                    
                    # Fetch full group details with UoMGroupDefinitionCollection
                    uom_definitions = []
                    
                    if abs_entry is not None and abs_entry != -1:
                        try:
                            _logger.info(f"  Fetching full details for group {abs_entry}...")
                            group_endpoint = f"UnitOfMeasurementGroups({abs_entry})"
                            full_group_data = connection.get(group_endpoint, {})
                            
                            # Log the keys in response for debugging
                            response_keys = list(full_group_data.keys()) if isinstance(full_group_data, dict) else []
                            _logger.info(f"  Response keys: {response_keys}")
                            
                            # الاسم الصحيح هو UoMGroupDefinitionCollection (وليس UnitOfMeasurement...)
                            uom_definitions = full_group_data.get('UoMGroupDefinitionCollection', [])
                            
                            if uom_definitions:
                                _logger.info(f"  ✓ Found {len(uom_definitions)} UoM definitions!")
                                # Log first definition for debugging
                                if len(uom_definitions) > 0:
                                    _logger.info(f"    First definition keys: {list(uom_definitions[0].keys())}")
                            else:
                                _logger.warning(f"  ⚠ No UoMGroupDefinitionCollection in response (tried key: 'UoMGroupDefinitionCollection')")
                        except Exception as e:
                            _logger.error(f"  ❌ Error fetching group details: {str(e)}")
                    
                    # Create or get UoM category in Odoo
                    uom_category = self._get_or_create_uom_category(group_name, group_code)
                    
                    # If still no definitions, try alternative method using UnitOfMeasurements
                    if not uom_definitions:
                        _logger.warning(f"  ⚠ No UoM definitions found for group {group_code}")
                        _logger.info(f"  Trying alternative method: UnitOfMeasurements with UoMGroupEntry filter...")
                        try:
                            # Get UoMs that belong to this group using UoMGroupEntry
                            if abs_entry is not None and abs_entry != -1:
                                uom_endpoint = "UnitOfMeasurements"
                                uom_params = {
                                    '$filter': f"UoMGroupEntry eq {abs_entry}",
                                    '$top': 100
                                }
                                uoms_response = connection.get(uom_endpoint, uom_params)
                                alternative_uoms = uoms_response.get('value', [])
                                
                                if alternative_uoms:
                                    _logger.info(f"  ✓ Found {len(alternative_uoms)} UoMs via UnitOfMeasurements filter")
                                    # Convert to definition format
                                    uom_definitions = []
                                    for uom in alternative_uoms:
                                        uom_definitions.append({
                                            'UoMCode': uom.get('Code'),
                                            'UoMName': uom.get('Name', uom.get('Code')),
                                            'UoMEntry': uom.get('AbsEntry', 0),
                                            'AlternateQuantity': 1.0,  # Default, will be updated from products
                                            'BaseQuantity': 1.0
                                        })
                        except Exception as e:
                            _logger.warning(f"  ⚠ Alternative method failed: {str(e)}")
                    
                    # If still no definitions after alternative method, skip this group
                    if not uom_definitions:
                        _logger.warning(f"  ⚠ Skipping group {group_code} - no UoMs found")
                        imported_groups.append({
                            'code': group_code,
                            'name': group_name,
                            'base_uom': base_uom,
                            'uom_count': 0
                        })
                        continue
                    
                    # Process each UoM in the group
                    base_uom_record = None
                    for uom_def in uom_definitions:
                        try:
                            # Get UoM Entry - the field name is AlternateUoM!
                            alternate_uom_entry = uom_def.get('AlternateUoM', 0)
                            alt_quantity = float(uom_def.get('AlternateQuantity', 1.0))
                            base_quantity = float(uom_def.get('BaseQuantity', 1.0))
                            
                            if not alternate_uom_entry:
                                _logger.warning(f"  ⚠ No AlternateUoM in definition, skipping")
                                continue
                            
                            # Find the UoM sync record by Entry
                            uom_sync_existing = self.search([
                                ('backend_id', '=', backend.id),
                                ('sap_uom_entry', '=', alternate_uom_entry)
                            ], limit=1)
                            
                            if not uom_sync_existing:
                                # UoM doesn't exist yet - CREATE IT!
                                _logger.info(f"  Creating new UoM sync for Entry {alternate_uom_entry}...")
                                
                                # We need to find the UoM code from UnitOfMeasurements
                                try:
                                    uom_detail = connection.get(f'UnitOfMeasurements({alternate_uom_entry})', {})
                                    uom_code_new = uom_detail.get('Code', f'UOM_{alternate_uom_entry}')
                                    uom_name_new = uom_detail.get('Name', uom_code_new)
                                    
                                    # Create UoM sync record
                                    uom_sync_existing = self.create({
                                        'backend_id': backend.id,
                                        'sap_uom_id': uom_code_new,
                                        'sap_uom_name': uom_name_new,
                                        'sap_uom_entry': alternate_uom_entry,
                                        'sync_direction': 'sap_to_odoo',
                                        'sync_status': 'pending',
                                    })
                                    
                                    _logger.info(f"  ✓ Created UoM sync: {uom_code_new} (Entry: {alternate_uom_entry})")
                                    
                                except Exception as create_error:
                                    _logger.error(f"  ❌ Cannot create UoM sync for Entry {alternate_uom_entry}: {str(create_error)}")
                                    continue
                            
                            uom_code = uom_sync_existing.sap_uom_id
                            uom_name = uom_sync_existing.sap_uom_name or uom_code
                            
                            # Calculate conversion factor
                            # In SAP: base_quantity (base UoM) = alt_quantity (this UoM)
                            # In Odoo: factor = how many base units in 1 of this unit
                            # Example: BaseQty=12, AltQty=1 means 1 unit = 12 base units, factor = 12.0
                            factor = base_quantity / alt_quantity if alt_quantity != 0 else 1.0
                            
                            is_base = (alternate_uom_entry == base_uom)
                            
                            _logger.info(f"  Processing UoM: {uom_code} (Entry:{alternate_uom_entry}, Factor:{factor:.4f}, {alt_quantity}={base_quantity} base, Base:{is_base})")
                            
                            # Update UoM factor in Odoo
                            if uom_sync_existing.odoo_uom_id:
                                uom_record = uom_sync_existing.odoo_uom_id
                                
                                # Update factor if different
                                if abs(uom_record.factor - factor) > 0.001:
                                    try:
                                        uom_record.sudo().write({'factor': factor})
                                        _logger.info(f"    ✓ Updated factor: {uom_record.name} = {factor:.4f}")
                                    except Exception as e:
                                        _logger.warning(f"    ⚠ Cannot update factor: {str(e)[:80]}")
                            else:
                                # Create UoM if doesn't exist
                                uom_record = self._create_or_update_uom_in_category(
                                    uom_code=uom_code,
                                    uom_name=uom_name,
                                    category=uom_category,
                                    factor=factor,
                                    is_base=is_base
                                )
                                uom_sync_existing.odoo_uom_id = uom_record.id
                            
                            # Track base UoM
                            if is_base:
                                base_uom_record = uom_record
                            
                            # Update the existing sync record with group link
                            # Add to sap_group_ids (Many2many - allows multiple groups)
                            if group_record.id not in uom_sync_existing.sap_group_ids.ids:
                                uom_sync_existing.write({
                                    'sap_group_ids': [(4, group_record.id)],  # Add link
                                    'sync_status': 'success',
                                    'last_sync': fields.Datetime.now(),
                                })
                                _logger.info(f"    ✓ Linked to group {group_record.name}")
                                
                        except Exception as e:
                            _logger.error(f"  Error processing UoM entry {alternate_uom_entry} in group {group_code}: {str(e)}")
                            continue
                    
                    imported_groups.append({
                        'code': group_code,
                        'name': group_name,
                        'base_uom': base_uom,
                        'uom_count': len(uom_definitions)
                    })
                    
                except Exception as e:
                    _logger.error(f"Error importing UoM group {group_code}: {str(e)}")
                    continue
            
            _logger.info(f"Successfully imported {len(imported_groups)} UoM Groups from SAP")
            return imported_groups
            
        except Exception as e:
            _logger.error(f"Error importing UoM groups: {str(e)}")
            return []
    
    def _get_or_create_uom_category(self, category_name, category_code):
        """Get or create UoM category in Odoo
        Note: In Odoo 19, uom.category was removed. This method now returns None
        as categories are handled differently in the new UoM system.
        """
        _logger.info(f"UoM category requested: {category_name} ({category_code}) - Using Odoo 19 UoM system without categories")
        return None  # Categories not used in Odoo 19
    
    def _create_or_update_uom_in_category(self, uom_code, uom_name, category, factor, is_base=False):
        """Create or update a UoM with conversion factor
        Note: In Odoo 19, categories are not used. UoMs are linked directly via relative_uom_id."""
        try:
            # Search for existing UoM
            uom = self.env['uom.uom'].search([
                ('name', '=', uom_name)
            ], limit=1)
            
            if not uom:
                # Try by code in name
                uom = self.env['uom.uom'].search([
                    ('name', 'ilike', uom_code)
                ], limit=1)
            
            if uom:
                # UoM exists - just update factor if needed
                update_vals = {}
                
                # Only update factor if it's not the base UoM and different from current
                if not is_base and abs(uom.factor - factor) > 0.001:
                    update_vals['factor'] = factor
                    _logger.info(f"Updating UoM: {uom.name} with factor {factor}")
                
                if update_vals:
                    try:
                        uom.write(update_vals)
                        _logger.info(f"Updated existing UoM: {uom.name} (Factor: {factor})")
                    except Exception as e:
                        # Skip update if UoM is in use
                        _logger.warning(f"Cannot update UoM {uom.name}: {str(e)}")
            else:
                # Create new UoM
                uom_vals = {
                    'name': uom_name,
                    'active': True,
                    'factor': factor,
                    'rounding': 0.01,
                }
                
                # Link to a reference unit if not base
                if not is_base:
                    # Try to find a suitable reference UoM (factor = 1.0)
                    ref_uom = self.env['uom.uom'].search([('factor', '=', 1.0)], limit=1)
                    if ref_uom:
                        uom_vals['relative_uom_id'] = ref_uom.id
                
                uom = self.env['uom.uom'].create(uom_vals)
                _logger.info(f"Created new UoM: {uom.name} (Factor: {factor})")
            
            return uom
            
        except Exception as e:
            _logger.error(f"Error creating/updating UoM {uom_name}: {str(e)}")
            # Return default UoM
            return self.env.ref('uom.product_uom_unit')
    
    @api.model
    def sync_all_uoms(self, backend_id):
        """Sync all UoMs from SAP"""
        try:
            # Common SAP UoMs to sync
            sap_uoms = ['PCS', 'KG', 'G', 'T', 'M', 'CM', 'MM', 'L', 'ML', 'BOX', 'PKG']
            
            synced_count = 0
            for sap_uom_id in sap_uoms:
                # Check if sync record already exists
                sync_record = self.search([
                    ('backend_id', '=', backend_id),
                    ('sap_uom_id', '=', sap_uom_id)
                ])
                
                if not sync_record:
                    # Create new sync record
                    sync_record = self.create({
                        'backend_id': backend_id,
                        'sap_uom_id': sap_uom_id,
                        'sync_direction': 'sap_to_odoo',
                    })
                
                # Sync the UoM
                sync_record.sync_from_sap()
                synced_count += 1
            
            _logger.info(f"Synced {synced_count} UoMs from SAP")
            return synced_count
            
        except Exception as e:
            _logger.error(f"Error syncing all UoMs: {str(e)}")
            raise
    
    def _get_or_create_group(self, backend, group_code, group_name, base_uom_code, abs_entry):
        """Get or create SAP UoM Group record"""
        try:
            # Search for existing group
            group = self.env['sap.uom.group'].search([
                ('sap_group_code', '=', group_code),
                ('backend_id', '=', backend.id)
            ], limit=1)
            
            if group:
                # Update existing group
                group.write({
                    'name': group_name,
                    'base_uom_code': base_uom_code,
                    'sap_abs_entry': abs_entry,
                    'sync_status': 'success',
                    'last_sync': fields.Datetime.now(),
                })
                _logger.info(f"  Updated existing group: {group_name}")
                return group
            
            # Create new group
            group = self.env['sap.uom.group'].create({
                'name': group_name,
                'sap_group_code': group_code,
                'sap_abs_entry': abs_entry,
                'base_uom_code': base_uom_code,
                'backend_id': backend.id,
                'sync_status': 'success',
                'last_sync': fields.Datetime.now(),
            })
            
            _logger.info(f"  Created new group: {group_name}")
            return group
            
        except Exception as e:
            _logger.error(f"Error creating/updating group {group_code}: {str(e)}")
            # Return a dummy group to avoid breaking the flow
            return self.env['sap.uom.group'].browse()


