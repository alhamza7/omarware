# -*- coding: utf-8 -*-
"""SAP Import Wizards - Comprehensive Import Tool"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapImportWizard(models.TransientModel):
    """Comprehensive SAP Import Wizard"""
    _name = 'sap.import.wizard'
    _description = 'Import Data from SAP'
    
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        default=lambda self: self.env['sap.backend'].search([], limit=1)
    )
    
    # Import Options
    import_customers = fields.Boolean(string='Import Customers', default=False)
    import_products = fields.Boolean(string='Import Products', default=False)
    import_uoms = fields.Boolean(string='Import Units of Measure', default=False)
    import_warehouses = fields.Boolean(string='Import Warehouses', default=False)
    import_pricelists = fields.Boolean(string='Import Pricelists', default=False)
    import_sales_orders = fields.Boolean(string='Import Sales Orders', default=False)
    import_quotations = fields.Boolean(string='Import Quotations', default=False)
    import_invoices = fields.Boolean(string='Import Invoices', default=False)
    
    # Filters
    customer_limit = fields.Integer(string='Customer Limit', default=0, help='Maximum number of customers to import (0 = unlimited)')
    product_limit = fields.Integer(string='Product Limit', default=0, help='Maximum number of products to import (0 = unlimited)')
    batch_size = fields.Integer(string='Batch Size', default=100, help='Number of records to fetch per batch')
    
    # Results and Logs
    result_message = fields.Text(string='Import Results', readonly=True)
    import_log = fields.Text(string='Detailed Import Log', readonly=True, help='Detailed log of import operations')
    show_logs = fields.Boolean(string='Show Detailed Logs', default=True)
    state = fields.Selection([
        ('draft', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('error', 'Error')
    ], string='Status', default='draft', readonly=True)
    
    def action_view_results(self):
        """Switch to Import Results tab and show logs"""
        self.show_logs = True
        # Just refresh the form
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sap.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def _add_log(self, message, level='INFO'):
        """Add message to import log"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        current_log = self.import_log or ""
        self.import_log = current_log + log_entry
        
        # Log to Odoo logger with safe encoding (remove special chars for file log)
        try:
            # Remove emoji and special characters for file logging
            safe_message = message.encode('ascii', 'ignore').decode('ascii')
            if safe_message.strip():  # Only log if there's content after removing special chars
                _logger.info(f"Import Wizard: {safe_message}")
        except Exception:
            # If logging fails, just skip it (the message is already in import_log field)
            pass
    
    def action_import_selected(self):
        """Import selected data types from SAP"""
        self.ensure_one()
        
        if not any([
            self.import_customers, self.import_products, self.import_uoms,
            self.import_warehouses, self.import_pricelists, self.import_sales_orders,
            self.import_quotations, self.import_invoices
        ]):
            raise UserError('Please select at least one import option.')
        
        # Set state to in progress
        self.state = 'in_progress'
        
        # Initialize logs
        self.import_log = ""
        self._add_log("=" * 80)
        self._add_log("SAP IMPORT WIZARD - Starting Import Process")
        self._add_log("=" * 80)
        self._add_log(f"Backend: {self.backend_id.name}")
        self._add_log(f"Backend URL: {self.backend_id.base_url}")
        self._add_log("")
        
        results = []
        errors = []
        total_imported = 0
        
        try:
            # Import UoMs first (dependency for other imports)
            if self.import_uoms:
                self._add_log("--- Starting UoM Import ---")
                try:
                    count = self._import_uoms()
                    total_imported += count
                    results.append(f'✓ Imported {count} Units of Measure')
                    self._add_log(f"SUCCESS: Imported {count} UoMs", "SUCCESS")
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f'✗ UoMs: {error_msg}')
                    self._add_log(f"ERROR importing UoMs: {error_msg}", "ERROR")
                self._add_log("")
            
            # Import Warehouses
            if self.import_warehouses:
                self._add_log("--- Starting Warehouse Import ---")
                try:
                    count = self._import_warehouses()
                    total_imported += count
                    results.append(f'✓ Imported {count} Warehouses')
                    self._add_log(f"SUCCESS: Imported {count} Warehouses", "SUCCESS")
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f'✗ Warehouses: {error_msg}')
                    self._add_log(f"ERROR importing Warehouses: {error_msg}", "ERROR")
                self._add_log("")
            
            # Import Customers
            if self.import_customers:
                self._add_log(f"--- Starting Customer Import (Limit: {self.customer_limit}) ---")
                try:
                    count = self._import_customers()
                    total_imported += count
                    results.append(f'✓ Imported {count} Customers')
                    self._add_log(f"SUCCESS: Imported {count} Customers", "SUCCESS")
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f'✗ Customers: {error_msg}')
                    self._add_log(f"ERROR importing Customers: {error_msg}", "ERROR")
                self._add_log("")
            
            # Import Products
            if self.import_products:
                self._add_log(f"--- Starting Product Import (Limit: {self.product_limit}) ---")
                try:
                    count = self._import_products()
                    total_imported += count
                    results.append(f'✓ Imported {count} Products')
                    self._add_log(f"SUCCESS: Imported {count} Products", "SUCCESS")
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f'✗ Products: {error_msg}')
                    self._add_log(f"ERROR importing Products: {error_msg}", "ERROR")
                self._add_log("")
            
            # Import Pricelists
            if self.import_pricelists:
                self._add_log("--- Starting Pricelist Import ---")
                try:
                    count = self._import_pricelists()
                    total_imported += count
                    results.append(f'✓ Imported {count} Pricelists')
                    self._add_log(f"SUCCESS: Imported {count} Pricelists", "SUCCESS")
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f'✗ Pricelists: {error_msg}')
                    self._add_log(f"ERROR importing Pricelists: {error_msg}", "ERROR")
                self._add_log("")
            
            # Import Sales Orders
            if self.import_sales_orders:
                self._add_log("--- Starting Sales Order Import ---")
                try:
                    count = self._import_sales_orders()
                    total_imported += count
                    results.append(f'✓ Imported {count} Sales Orders')
                    self._add_log(f"SUCCESS: Imported {count} Sales Orders", "SUCCESS")
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f'✗ Sales Orders: {error_msg}')
                    self._add_log(f"ERROR importing Sales Orders: {error_msg}", "ERROR")
                self._add_log("")
            
            # Import Quotations
            if self.import_quotations:
                self._add_log("--- Starting Quotation Import ---")
                try:
                    count = self._import_quotations()
                    total_imported += count
                    results.append(f'✓ Imported {count} Quotations')
                    self._add_log(f"SUCCESS: Imported {count} Quotations", "SUCCESS")
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f'✗ Quotations: {error_msg}')
                    self._add_log(f"ERROR importing Quotations: {error_msg}", "ERROR")
                self._add_log("")
            
            # Import Invoices
            if self.import_invoices:
                self._add_log("--- Starting Invoice Import ---")
                try:
                    count = self._import_invoices()
                    total_imported += count
                    results.append(f'✓ Imported {count} Invoices')
                    self._add_log(f"SUCCESS: Imported {count} Invoices", "SUCCESS")
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f'✗ Invoices: {error_msg}')
                    self._add_log(f"ERROR importing Invoices: {error_msg}", "ERROR")
                self._add_log("")
            
        except Exception as e:
            self.state = 'error'
            self._add_log(f"CRITICAL ERROR: {str(e)}", "ERROR")
            raise UserError(f"Import failed: {str(e)}")
        
        # Final summary
        self._add_log("=" * 80)
        self._add_log("IMPORT SUMMARY")
        self._add_log("=" * 80)
        self._add_log(f"Total records imported: {total_imported}")
        self._add_log(f"Successful operations: {len(results)}")
        self._add_log(f"Failed operations: {len(errors)}")
        
        # Prepare result message
        message = '\n'.join(results)
        if errors:
            message += '\n\nErrors:\n' + '\n'.join(errors)
        
        self.result_message = message
        self._add_log("=" * 80)
        self._add_log("Import process completed!")
        self._add_log("=" * 80)
        
        # Set state to done
        self.state = 'done' if not errors else 'error'
        
        # Force show logs after import
        self.show_logs = True
        
        # Show success message and keep wizard open
        message = f"""
╔══════════════════════════════════════════════════════════════╗
║              ✅ IMPORT COMPLETED SUCCESSFULLY                ║
╚══════════════════════════════════════════════════════════════╝

📊 Summary:
{chr(10).join('  ' + r for r in results)}
"""
        if errors:
            message += f"""
⚠️ Errors:
{chr(10).join('  ' + e for e in errors)}
"""
        
        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Go to "Import Results" tab to see detailed logs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Save and immediately reopen the wizard to show results
        self.env.cr.commit()  # Commit to ensure data is saved
        
        # Return action to reopen same wizard record
        return {
            'name': 'Import Results - SAP Import Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'sap.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': dict(self.env.context, default_show_logs=True),
            'flags': {'mode': 'readonly'},
        }
    
    def _import_uoms(self):
        """Import UoMs from SAP"""
        try:
            uom_model = self.env['sap.uom.sync']
            if hasattr(uom_model, 'import_all_uoms_from_sap'):
                return uom_model.import_all_uoms_from_sap(self.backend_id)
            else:
                _logger.warning("UoM import method not found")
                return 0
        except Exception as e:
            _logger.error(f"Error importing UoMs: {str(e)}")
            raise
    
    def _import_warehouses(self):
        """Import warehouses from SAP"""
        try:
            warehouse_model = self.env['sap.warehouse']
            if hasattr(warehouse_model, 'import_all_from_sap'):
                return warehouse_model.import_all_from_sap(self.backend_id)
            else:
                _logger.warning("Warehouse import method not found")
                return 0
        except Exception as e:
            _logger.error(f"Error importing warehouses: {str(e)}")
            raise
    
    def _import_customers(self):
        """Import customers from SAP with pagination"""
        try:
            self._add_log("Connecting to SAP to fetch customers...")
            customer_model = self.env['sap.customer.sync']
            connection = self.backend_id.get_connection()
            
            # Determine limit
            limit_msg = f"Limit: {self.customer_limit}" if self.customer_limit > 0 else "All records"
            self._add_log(f"Requesting customers from SAP ({limit_msg})...")
            
            # Initialize pagination
            skip = 0
            total_count = 0
            failed = 0
            has_more = True
            
            while has_more:
                try:
                    # Build query parameters
                    params = {
                        '$top': self.batch_size,
                        '$skip': skip,
                        '$filter': "CardType eq 'C'",  # Customer type
                        '$orderby': 'CardCode'
                    }
                    
                    # Fetch batch
                    customers_data = connection.get('BusinessPartners', params)
                    batch = customers_data.get('value', [])
                    
                    if not batch:
                        has_more = False
                        break
                    
                    batch_size = len(batch)
                    self._add_log(f"Processing batch: {skip + 1} to {skip + batch_size}")
                    
                    # Process each customer in batch
                    for idx, customer_data in enumerate(batch, 1):
                        card_code = None
                        try:
                            card_code = customer_data.get('CardCode')
                            card_name = customer_data.get('CardName', 'Unknown')
                            global_idx = skip + idx
                            self._add_log(f"  [{global_idx}] Importing customer: {card_code} - {card_name}")
                            
                            result = customer_model.import_record(self.backend_id, card_code)
                            if result:
                                total_count += 1
                                self._add_log(f"  ✓ Success: {card_name}", "INFO")
                            else:
                                failed += 1
                                self._add_log(f"  ✗ Failed: Not found in SAP", "WARNING")
                            
                        except Exception as e:
                            failed += 1
                            error_msg = str(e)
                            self._add_log(f"  ✗ Failed to import customer {card_code}: {error_msg}", "WARNING")
                    
                    # Update skip for next batch
                    skip += batch_size
                    
                    # Check if we've reached the limit
                    if self.customer_limit > 0 and skip >= self.customer_limit:
                        has_more = False
                        self._add_log(f"Reached customer limit of {self.customer_limit}")
                    
                    # Check if there are more records
                    if batch_size < self.batch_size:
                        has_more = False
                    
                    # Commit batch to avoid memory issues
                    self.env.cr.commit()
                    
                except Exception as e:
                    self._add_log(f"Error fetching batch at offset {skip}: {str(e)}", "ERROR")
                    has_more = False
            
            self._add_log(f"Customer import completed: {total_count} succeeded, {failed} failed")
            return total_count
            
        except Exception as e:
            self._add_log(f"CRITICAL: Error importing customers: {str(e)}", "ERROR")
            _logger.error(f"Error importing customers: {str(e)}")
            raise
    
    def _import_products(self):
        """Import products from SAP with pagination"""
        try:
            self._add_log("Connecting to SAP to fetch products...")
            product_model = self.env['sap.product.sync']
            connection = self.backend_id.get_connection()
            
            # Determine limit
            limit_msg = f"Limit: {self.product_limit}" if self.product_limit > 0 else "All records"
            self._add_log(f"Requesting products from SAP ({limit_msg})...")
            
            # Initialize pagination
            skip = 0
            total_count = 0
            failed = 0
            has_more = True
            
            while has_more:
                try:
                    # Build query parameters
                    params = {
                        '$top': self.batch_size,
                        '$skip': skip,
                        '$orderby': 'ItemCode'
                    }
                    
                    # Fetch batch
                    products_data = connection.get('Items', params)
                    batch = products_data.get('value', [])
                    
                    if not batch:
                        has_more = False
                        break
                    
                    batch_size = len(batch)
                    self._add_log(f"Processing batch: {skip + 1} to {skip + batch_size}")
                    
                    # Process each product in batch
                    for idx, product_data in enumerate(batch, 1):
                        item_code = None
                        try:
                            item_code = product_data.get('ItemCode')
                            item_name = product_data.get('ItemName', 'Unknown')
                            global_idx = skip + idx
                            self._add_log(f"  [{global_idx}] Importing product: {item_code} - {item_name}")
                            
                            result = product_model.import_record(self.backend_id, item_code)
                            if result:
                                total_count += 1
                                self._add_log(f"  ✓ Success: {item_name}", "INFO")
                            else:
                                failed += 1
                                self._add_log(f"  ✗ Failed: Not found in SAP", "WARNING")
                            
                        except Exception as e:
                            failed += 1
                            error_msg = str(e)
                            self._add_log(f"  ✗ Failed to import product {item_code}: {error_msg}", "WARNING")
                    
                    # Update skip for next batch
                    skip += batch_size
                    
                    # Check if we've reached the limit
                    if self.product_limit > 0 and skip >= self.product_limit:
                        has_more = False
                        self._add_log(f"Reached product limit of {self.product_limit}")
                    
                    # Check if there are more records
                    if batch_size < self.batch_size:
                        has_more = False
                    
                    # Commit batch to avoid memory issues
                    self.env.cr.commit()
                    
                except Exception as e:
                    self._add_log(f"Error fetching batch at offset {skip}: {str(e)}", "ERROR")
                    has_more = False
            
            self._add_log(f"Product import completed: {total_count} succeeded, {failed} failed")
            return total_count
            
        except Exception as e:
            self._add_log(f"CRITICAL: Error importing products: {str(e)}", "ERROR")
            _logger.error(f"Error importing products: {str(e)}")
            raise
    
    def _import_pricelists(self):
        """Import pricelists from SAP"""
        try:
            pricelist_model = self.env['sap.pricelist.sync']
            connection = self.backend_id.get_connection()
            
            # Get all pricelists from SAP
            pricelists_data = connection.get('PriceLists', {})
            
            count = 0
            failed = 0
            pricelists = pricelists_data.get('value', [])
            
            self._add_log(f"Found {len(pricelists)} pricelists in SAP")
            
            for idx, pricelist_data in enumerate(pricelists, 1):
                try:
                    pricelist_no = pricelist_data.get('PriceListNo')
                    pricelist_name = pricelist_data.get('PriceListName', 'Unknown')
                    self._add_log(f"  [{idx}/{len(pricelists)}] Importing pricelist: {pricelist_no} - {pricelist_name}")
                    
                    if hasattr(pricelist_model, 'import_record'):
                        pricelist_model.import_record(self.backend_id, pricelist_no)
                        count += 1
                except Exception as e:
                    failed += 1
                    self._add_log(f"  ✗ Failed to import pricelist {pricelist_no}: {str(e)}", "WARNING")
            
            self._add_log(f"Pricelist import completed: {count} succeeded, {failed} failed")
            return count
            
        except Exception as e:
            _logger.error(f"Error importing pricelists: {str(e)}")
            raise
    
    def _import_sales_orders(self):
        """Import sales orders from SAP with pagination"""
        try:
            sale_model = self.env['sap.sale.sync']
            connection = self.backend_id.get_connection()
            
            # Initialize pagination
            skip = 0
            total_count = 0
            failed = 0
            has_more = True
            
            self._add_log("Fetching sales orders from SAP (All records)...")
            
            while has_more:
                try:
                    # Build query parameters
                    params = {
                        '$top': self.batch_size,
                        '$skip': skip,
                        '$orderby': 'DocEntry'
                    }
                    
                    # Fetch batch
                    orders_data = connection.get('Orders', params)
                    batch = orders_data.get('value', [])
                    
                    if not batch:
                        has_more = False
                        break
                    
                    batch_size = len(batch)
                    self._add_log(f"Processing batch: {skip + 1} to {skip + batch_size}")
                    
                    # Process each order in batch
                    for idx, order_data in enumerate(batch, 1):
                        try:
                            doc_entry = order_data.get('DocEntry')
                            doc_num = order_data.get('DocNum', 'Unknown')
                            global_idx = skip + idx
                            self._add_log(f"  [{global_idx}] Importing sales order: {doc_entry} (DocNum: {doc_num})")
                            
                            if hasattr(sale_model, 'import_record'):
                                sale_model.import_record(self.backend_id, doc_entry)
                                total_count += 1
                            
                        except Exception as e:
                            failed += 1
                            self._add_log(f"  ✗ Failed to import order {doc_entry}: {str(e)}", "WARNING")
                    
                    # Update skip for next batch
                    skip += batch_size
                    
                    # Check if there are more records
                    if batch_size < self.batch_size:
                        has_more = False
                    
                    # Commit batch to avoid memory issues
                    self.env.cr.commit()
                    
                except Exception as e:
                    self._add_log(f"Error fetching batch at offset {skip}: {str(e)}", "ERROR")
                    has_more = False
            
            self._add_log(f"Sales order import completed: {total_count} succeeded, {failed} failed")
            return total_count
            
        except Exception as e:
            _logger.error(f"Error importing sales orders: {str(e)}")
            raise
    
    def _import_quotations(self):
        """Import quotations from SAP with pagination"""
        try:
            quotation_model = self.env['sap.quotation.sync']
            connection = self.backend_id.get_connection()
            
            # Initialize pagination
            skip = 0
            total_count = 0
            failed = 0
            has_more = True
            
            self._add_log("Fetching quotations from SAP (All records)...")
            
            while has_more:
                try:
                    # Build query parameters
                    params = {
                        '$top': self.batch_size,
                        '$skip': skip,
                        '$orderby': 'DocEntry'
                    }
                    
                    # Fetch batch
                    quotations_data = connection.get('Quotations', params)
                    batch = quotations_data.get('value', [])
                    
                    if not batch:
                        has_more = False
                        break
                    
                    batch_size = len(batch)
                    self._add_log(f"Processing batch: {skip + 1} to {skip + batch_size}")
                    
                    # Process each quotation in batch
                    for idx, quotation_data in enumerate(batch, 1):
                        try:
                            doc_entry = quotation_data.get('DocEntry')
                            doc_num = quotation_data.get('DocNum', 'Unknown')
                            global_idx = skip + idx
                            self._add_log(f"  [{global_idx}] Importing quotation: {doc_entry} (DocNum: {doc_num})")
                            
                            if hasattr(quotation_model, 'import_record'):
                                quotation_model.import_record(self.backend_id, doc_entry)
                                total_count += 1
                            
                        except Exception as e:
                            failed += 1
                            self._add_log(f"  ✗ Failed to import quotation {doc_entry}: {str(e)}", "WARNING")
                    
                    # Update skip for next batch
                    skip += batch_size
                    
                    # Check if there are more records
                    if batch_size < self.batch_size:
                        has_more = False
                    
                    # Commit batch to avoid memory issues
                    self.env.cr.commit()
                    
                except Exception as e:
                    self._add_log(f"Error fetching batch at offset {skip}: {str(e)}", "ERROR")
                    has_more = False
            
            self._add_log(f"Quotation import completed: {total_count} succeeded, {failed} failed")
            return total_count
            
        except Exception as e:
            _logger.error(f"Error importing quotations: {str(e)}")
            raise
    
    def _import_invoices(self):
        """Import invoices from SAP with pagination"""
        try:
            invoice_model = self.env['sap.invoice.sync']
            connection = self.backend_id.get_connection()
            
            # Initialize pagination
            skip = 0
            total_count = 0
            failed = 0
            has_more = True
            
            self._add_log("Fetching invoices from SAP (All records)...")
            
            while has_more:
                try:
                    # Build query parameters
                    params = {
                        '$top': self.batch_size,
                        '$skip': skip,
                        '$orderby': 'DocEntry'
                    }
                    
                    # Fetch batch
                    invoices_data = connection.get('Invoices', params)
                    batch = invoices_data.get('value', [])
                    
                    if not batch:
                        has_more = False
                        break
                    
                    batch_size = len(batch)
                    self._add_log(f"Processing batch: {skip + 1} to {skip + batch_size}")
                    
                    # Process each invoice in batch
                    for idx, invoice_data in enumerate(batch, 1):
                        try:
                            doc_entry = invoice_data.get('DocEntry')
                            doc_num = invoice_data.get('DocNum', 'Unknown')
                            global_idx = skip + idx
                            self._add_log(f"  [{global_idx}] Importing invoice: {doc_entry} (DocNum: {doc_num})")
                            
                            if hasattr(invoice_model, 'import_record'):
                                invoice_model.import_record(self.backend_id, doc_entry)
                                total_count += 1
                            
                        except Exception as e:
                            failed += 1
                            self._add_log(f"  ✗ Failed to import invoice {doc_entry}: {str(e)}", "WARNING")
                    
                    # Update skip for next batch
                    skip += batch_size
                    
                    # Check if there are more records
                    if batch_size < self.batch_size:
                        has_more = False
                    
                    # Commit batch to avoid memory issues
                    self.env.cr.commit()
                    
                except Exception as e:
                    self._add_log(f"Error fetching batch at offset {skip}: {str(e)}", "ERROR")
                    has_more = False
            
            self._add_log(f"Invoice import completed: {total_count} succeeded, {failed} failed")
            return total_count
            
        except Exception as e:
            _logger.error(f"Error importing invoices: {str(e)}")
            raise
    
    def action_import_all(self):
        """Quick action to import everything"""
        self.write({
            'import_customers': True,
            'import_products': True,
            'import_uoms': True,
            'import_warehouses': True,
            'import_pricelists': True,
            'import_sales_orders': True,
            'import_quotations': True,
            'import_invoices': True,
        })
        return self.action_import_selected()
