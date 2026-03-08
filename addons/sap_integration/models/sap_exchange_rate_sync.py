# -*- coding: utf-8 -*-
"""
SAP Exchange Rate Sync

Pulls the IQD/USD exchange rate from SAP Business One (via DocRate on recent
IQD-denominated documents) and writes it to:
  1. ir.config_parameter  key='pos_perfume.default_exchange_rate_usd_iqd'
     → used by POS Perfume orders and the /pos_perfume/get_exchange_rate endpoint
  2. res.currency.rate    for the IQD currency (Odoo standard accounting)
     → used by usd_currency._convert() and standard invoicing

A scheduled action runs this every 30 minutes so the rate stays current
without any manual intervention.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

# Fallback rate used only when SAP cannot be reached (current SAP rate ~1560)
_FALLBACK_RATE = 1560.0

# Minimum and maximum sane rate values — reject obviously wrong data from SAP
_MIN_RATE = 100.0
_MAX_RATE = 10000.0


class SapExchangeRateSync(models.Model):
    """Stores the last fetched SAP IQD/USD rate and provides sync utilities."""
    _name = 'sap.exchange.rate.sync'
    _description = 'SAP IQD/USD Exchange Rate Synchronization'
    _order = 'id desc'

    name = fields.Char(string='Name', default='IQD/USD Sync', readonly=True)
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='cascade',
        index=True,
    )
    active = fields.Boolean(default=True)

    # Last fetched state
    last_rate = fields.Float(
        string='Last Fetched Rate (IQD/USD)',
        readonly=True,
        digits=(12, 2),
    )
    last_sync_at = fields.Datetime(string='Last Sync At', readonly=True)
    last_sync_status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('no_change', 'No Change'),
    ], string='Status', readonly=True)
    last_sync_log = fields.Text(string='Log', readonly=True)
    total_runs = fields.Integer(string='Total Runs', readonly=True, default=0)
    total_errors = fields.Integer(string='Total Errors', readonly=True, default=0)

    _sql_constraints = [
        ('unique_backend', 'unique(backend_id)',
         'Only one exchange rate sync config per SAP backend is allowed.'),
    ]

    # ------------------------------------------------------------------
    # Cron entry point
    # ------------------------------------------------------------------

    @api.model
    def cron_sync_exchange_rate(self):
        """Called by the 30-minute scheduled action."""
        configs = self.search([('active', '=', True)])
        if not configs:
            _logger.debug('SAP Exchange Rate Sync: no active configs.')
            return
        for config in configs:
            try:
                config._run_sync()
            except Exception as exc:
                _logger.error(
                    'SAP Exchange Rate Sync: unhandled error for %s: %s',
                    config.backend_id.name, exc, exc_info=True,
                )

    @api.model
    def set_rate_1560_new_only(self):
        """
        Set exchange rate to 1560 for new usage only (no record required).
        Use from shell: env['sap.exchange.rate.sync'].set_rate_1560_new_only()
        Does not change old invoices or historical currency rates.
        """
        rate = 1560.0
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_perfume.default_exchange_rate_usd_iqd', str(rate)
        )
        iqd = self.env['res.currency'].search([('name', '=', 'IQD')], limit=1)
        if not iqd:
            _logger.warning('set_rate_1560_new_only: IQD currency not found.')
            return
        today = fields.Date.today()
        odoo_rate = round(1.0 / rate, 10)
        for company in self.env['res.company'].search([]):
            existing = self.env['res.currency.rate'].search([
                ('currency_id', '=', iqd.id),
                ('name', '=', today),
                ('company_id', '=', company.id),
            ], limit=1)
            if existing:
                existing.sudo().write({'rate': odoo_rate})
            else:
                self.env['res.currency.rate'].sudo().create({
                    'currency_id': iqd.id,
                    'rate': odoo_rate,
                    'name': today,
                    'company_id': company.id,
                })
        _logger.info('Exchange rate set to 1560 for new usage only (all companies).')

    # ------------------------------------------------------------------
    # Manual trigger
    # ------------------------------------------------------------------

    def action_sync_now(self):
        """Manual sync button."""
        self.ensure_one()
        self._run_sync()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SAP Exchange Rate',
                'message': f'Sync done — status: {self.last_sync_status} | Rate: {self.last_rate}',
                'type': 'success' if self.last_sync_status != 'failed' else 'warning',
                'sticky': False,
            },
        }

    def action_set_rate_1560_new_only(self):
        """
        Set exchange rate to 1560 for NEW usage only.
        Updates: config parameter (POS/default) and TODAY's currency rate for IQD.
        Does NOT change past invoices or historical res.currency.rate records.
        """
        self.ensure_one()
        rate = 1560.0
        IrParam = self.env['ir.config_parameter'].sudo()
        IrParam.set_param('pos_perfume.default_exchange_rate_usd_iqd', str(rate))
        IqdCurrency = self.env['res.currency'].search([('name', '=', 'IQD')], limit=1)
        if not IqdCurrency:
            raise UserError('عملة IQD غير موجودة في النظام.')
        today = fields.Date.today()
        odoo_rate = round(1.0 / rate, 10)
        existing = self.env['res.currency.rate'].search([
            ('currency_id', '=', IqdCurrency.id),
            ('name', '=', today),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if existing:
            existing.sudo().write({'rate': odoo_rate})
        else:
            self.env['res.currency.rate'].sudo().create({
                'currency_id': IqdCurrency.id,
                'rate': odoo_rate,
                'name': today,
                'company_id': self.env.company.id,
            })
        self.write({
            'last_rate': rate,
            'last_sync_status': 'success',
            'last_sync_at': fields.Datetime.now(),
            'last_sync_log': f'تعيين يدوي: سعر الصرف 1560 للاستخدام الجديد فقط (لا يغيّر الفواتير القديمة).',
        })
        self.env.cr.commit()
        _logger.info('Exchange rate set to 1560 for new usage only (today and config).')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'سعر الصرف',
                'message': 'تم تعيين سعر الصرف 1560 للجديد فقط (POS، الفواتير الجديدة، المحاسبة). الفواتير القديمة لم تتغير.',
                'type': 'success',
                'sticky': True,
            },
        }

    # ------------------------------------------------------------------
    # Core sync logic
    # ------------------------------------------------------------------

    def _run_sync(self):
        """Fetch rate from SAP and update both ir.config_parameter and res.currency.rate."""
        self.ensure_one()
        log = []

        try:
            connection = self.backend_id.get_connection()
            rate = connection.get_iqd_exchange_rate()

            if not rate:
                log.append('SAP returned no IQD rate — using fallback.')
                rate = _FALLBACK_RATE

            if not (_MIN_RATE <= rate <= _MAX_RATE):
                raise UserError(
                    f'SAP returned suspicious IQD rate {rate} — '
                    f'expected between {_MIN_RATE} and {_MAX_RATE}. Skipping.'
                )

            log.append(f'Rate from SAP: {rate}')

            previous = self.last_rate
            if previous and abs(previous - rate) < 0.01:
                log.append('Rate unchanged — skipping write.')
                self.write({
                    'last_sync_status': 'no_change',
                    'last_sync_at': fields.Datetime.now(),
                    'last_sync_log': '\n'.join(log),
                    'total_runs': self.total_runs + 1,
                })
                self.env.cr.commit()
                return

            self._write_config_parameter(rate)
            log.append(f'ir.config_parameter updated: {rate}')

            self._write_currency_rate(rate)
            log.append(f'res.currency.rate updated: {round(1.0 / rate, 10)}')

            self.write({
                'last_rate': rate,
                'last_sync_status': 'success',
                'last_sync_at': fields.Datetime.now(),
                'last_sync_log': '\n'.join(log),
                'total_runs': self.total_runs + 1,
            })
            _logger.info('SAP Exchange Rate Sync: new rate %.2f (was %.2f)', rate, previous or 0)

        except Exception as exc:
            log.append(f'ERROR: {exc}')
            self.write({
                'last_sync_status': 'failed',
                'last_sync_log': '\n'.join(log),
                'total_runs': self.total_runs + 1,
                'total_errors': self.total_errors + 1,
            })
            _logger.error('SAP Exchange Rate Sync failed: %s', exc, exc_info=True)
        finally:
            self.env.cr.commit()

    def _write_config_parameter(self, rate):
        """Update pos_perfume.default_exchange_rate_usd_iqd in ir.config_parameter."""
        IrParam = self.env['ir.config_parameter'].sudo()
        IrParam.set_param('pos_perfume.default_exchange_rate_usd_iqd', str(rate))

    def _write_currency_rate(self, rate):
        """
        Create or update today's res.currency.rate record for IQD.
        Odoo stores rates as inverse: rate = 1 / human_rate
        (e.g. 1 / 1530 ≈ 0.000654).
        """
        IqdCurrency = self.env['res.currency'].search(
            [('name', '=', 'IQD')], limit=1
        )
        if not IqdCurrency:
            _logger.warning('SAP Exchange Rate Sync: IQD currency not found in Odoo.')
            return

        today = fields.Date.today()
        odoo_rate = round(1.0 / rate, 10)

        existing = self.env['res.currency.rate'].search([
            ('currency_id', '=', IqdCurrency.id),
            ('name', '=', today),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        if existing:
            existing.sudo().write({'rate': odoo_rate})
        else:
            self.env['res.currency.rate'].sudo().create({
                'currency_id': IqdCurrency.id,
                'rate': odoo_rate,
                'name': today,
                'company_id': self.env.company.id,
            })
