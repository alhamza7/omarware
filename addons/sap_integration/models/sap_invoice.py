# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapInvoiceSync(models.Model):
    _name = 'sap.invoice.sync'
    _description = 'SAP Invoice Synchronizer'
    _order = 'last_sync desc'
    
    backend_id = fields.Many2one('sap.backend', 'Backend', required=True)
    connector_id = fields.Many2one('sap.connector', 'Connector')
    odoo_invoice_id = fields.Many2one('account.move', 'Odoo Invoice')
    sap_invoice_id = fields.Char('SAP Invoice ID', required=True)
    sap_doc_entry = fields.Integer('SAP Doc Entry')
    
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
    
    @api.model
    def create(self, vals):
        """Override create to set default values"""
        if not vals.get('backend_id') and vals.get('connector_id'):
            vals['backend_id'] = self.env['sap.connector'].browse(vals['connector_id']).backend_id.id
        return super(SapInvoiceSync, self).create(vals)
    
    def sync_from_sap(self):
        """Sync invoice from SAP to Odoo"""
        try:
            connection = self.backend_id.get_connection()
            
            # Get invoice data from SAP
            invoices = connection.get_invoices(
                filter_query=f"DocEntry eq {self.sap_doc_entry}"
            )
            
            if not invoices.get('value'):
                raise UserError(f"Invoice {self.sap_doc_entry} not found in SAP")
            
            invoice_data = invoices['value'][0]
            self.sap_data = str(invoice_data)
            
            # Process invoice data
            invoice = self._process_invoice_data(invoice_data)
            
            self.odoo_invoice_id = invoice.id
            self.sync_status = 'success'
            self.last_sync = fields.Datetime.now()
            self.error_message = False
            self.retry_count = 0
            
            _logger.info(f"Successfully synced invoice {self.sap_invoice_id}")
            
        except Exception as e:
            self.sync_status = 'error'
            self.error_message = str(e)
            self.retry_count += 1
            _logger.error(f"Error syncing invoice {self.sap_invoice_id}: {str(e)}")
            raise
    
    def _process_invoice_data(self, invoice_data):
        """Process invoice data from SAP and create/update Odoo invoice"""
        try:
            # Map SAP data to Odoo format
            invoice_vals = self._map_sap_to_odoo(invoice_data)
            
            # Check if invoice already exists
            invoice = self.env['account.move'].search([
                ('ref', '=', invoice_data['DocNum'])
            ], limit=1)
            
            if invoice:
                # Update existing invoice
                invoice.write(invoice_vals)
                _logger.info(f"Updated existing invoice: {invoice.name}")
            else:
                # Create new invoice
                invoice = self.env['account.move'].create(invoice_vals)
                _logger.info(f"Created new invoice: {invoice.name}")
            
            return invoice
            
        except Exception as e:
            _logger.error(f"Error processing invoice data: {str(e)}")
            raise
    
    def _map_sap_to_odoo(self, sap_data):
        """Map SAP invoice data to Odoo invoice format"""
        # Get customer
        customer = self.env['res.partner'].search([
            ('ref', '=', sap_data.get('CardCode', ''))
        ], limit=1)
        
        if not customer:
            # Create customer if not exists
            customer = self.env['res.partner'].create({
                'name': sap_data.get('CardName', ''),
                'ref': sap_data.get('CardCode', ''),
                'is_company': True,
                'customer_rank': 1,
            })
        
        # Prepare invoice lines
        invoice_lines = []
        for line in sap_data.get('DocumentLines', []):
            # Get product
            product = self.env['product.product'].search([
                ('default_code', '=', line.get('ItemCode', ''))
            ], limit=1)
            
            if product:
                invoice_lines.append((0, 0, {
                    'product_id': product.id,
                    'name': line.get('ItemDescription', ''),
                    'quantity': line.get('Quantity', 0),
                    'price_unit': line.get('UnitPrice', 0),
                    'discount': line.get('DiscountPercent', 0),
                }))
        
        return {
            'name': f"INV/{sap_data.get('DocNum', '')}",
            'ref': sap_data.get('DocNum', ''),
            'partner_id': customer.id,
            'invoice_date': sap_data.get('DocDate', fields.Date.today()),
            'move_type': 'out_invoice',
            'invoice_line_ids': invoice_lines,
            'narration': f"SAP Invoice: {sap_data.get('DocNum', '')}",
        }
    
    def retry_sync(self):
        """Retry failed synchronization"""
        if self.retry_count >= self.max_retries:
            raise UserError(f"Maximum retry attempts ({self.max_retries}) exceeded")
        
        if self.sync_direction in ['sap_to_odoo', 'bidirectional']:
            self.sync_from_sap()
        elif self.sync_direction == 'odoo_to_sap':
            self.sync_to_sap()
    
    def sync_to_sap(self):
        """
        Sync (update) invoice from Odoo to SAP.
        Sends current invoice header and DocumentLines to SAP via PATCH so that
        additions/deletions/changes in Odoo are applied in SAP.
        """
        self.ensure_one()
        if not self.sap_doc_entry:
            raise UserError("لا يوجد DocEntry للفاتورة في SAP — لا يمكن التحديث. أنشئ الفاتورة في SAP أولاً.")
        invoice = self.odoo_invoice_id
        if not invoice:
            invoice = self.env["account.move"].search(
                [("ref", "=", self.sap_invoice_id), ("move_type", "=", "out_invoice")],
                limit=1,
            )
        if not invoice:
            raise UserError(
                "لم يتم العثور على فاتورة Odoo مرتبطة بهذا السجل. ربط الفاتورة (Odoo Invoice) أو التأكد من ref."
            )
        try:
            mapper = self.env["sap.data.mapper"]
            payload = mapper.map_odoo_invoice_to_sap(invoice)
            # PATCH expects DocumentLines and optionally header fields; send full lines so SAP replaces them
            update_payload = {
                "DocumentLines": payload.get("DocumentLines", []),
            }
            if payload.get("DocDate"):
                update_payload["DocDate"] = payload["DocDate"]
            if payload.get("DocDueDate"):
                update_payload["DocDueDate"] = payload["DocDueDate"]
            if payload.get("CardCode"):
                update_payload["CardCode"] = payload["CardCode"]
            self.backend_id.update_invoice_in_sap(self.sap_doc_entry, update_payload)
            self.write({
                "sync_status": "success",
                "last_sync": fields.Datetime.now(),
                "error_message": False,
                "retry_count": 0,
            })
            self.env.cr.commit()
            _logger.info("Successfully synced invoice to SAP: %s (DocEntry %s)", self.sap_invoice_id, self.sap_doc_entry)
        except Exception as e:
            self.write({
                "sync_status": "error",
                "error_message": str(e),
                "retry_count": self.retry_count + 1,
            })
            self.env.cr.commit()
            _logger.error("Error syncing invoice to SAP: %s", e, exc_info=True)
            raise UserError("فشل تحديث الفاتورة في SAP: %s" % e)
    
    @api.model
    def sync_all_invoices(self, backend_id):
        """Sync all invoices from SAP"""
        try:
            backend = self.env['sap.backend'].browse(backend_id)
            connection = backend.get_connection()
            
            # Get all invoices from SAP
            invoices = connection.get_invoices(top=1000)  # Adjust as needed
            
            synced_count = 0
            for invoice_data in invoices.get('value', []):
                # Check if sync record already exists
                sync_record = self.search([
                    ('backend_id', '=', backend_id),
                    ('sap_doc_entry', '=', invoice_data['DocEntry'])
                ])
                
                if not sync_record:
                    # Create new sync record
                    sync_record = self.create({
                        'backend_id': backend_id,
                        'sap_invoice_id': invoice_data['DocNum'],
                        'sap_doc_entry': invoice_data['DocEntry'],
                        'sync_direction': 'sap_to_odoo',
                    })
                
                # Sync the invoice
                sync_record.sync_from_sap()
                synced_count += 1
            
            _logger.info(f"Synced {synced_count} invoices from SAP")
            return synced_count
            
        except Exception as e:
            _logger.error(f"Error syncing all invoices: {str(e)}")
            raise


