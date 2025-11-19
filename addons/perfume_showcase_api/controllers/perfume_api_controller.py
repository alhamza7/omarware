# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class PerfumeAPIController(http.Controller):
    """REST API Controller for Perfume Showcase Website"""

    @http.route('/api/perfume/brands', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_brands(self, **kwargs):
        """Get all brands with their perfumes"""
        try:
            brands = request.env['perfume.brand'].sudo().search([('active', '=', True)])
            
            result = []
            for brand in brands:
                perfumes_data = []
                for perfume in brand.perfumes.filtered(lambda p: p.active):
                    perfumes_data.append(perfume.get_api_data())
                
                result.append({
                    'id': brand.code,
                    'name': brand.name,
                    'country': brand.country,
                    'perfumes': perfumes_data
                })
            
            return request.make_response(
                json.dumps(result, ensure_ascii=False),
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error in get_brands: {e}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e)}, ensure_ascii=False),
                status=500,
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )

    @http.route('/api/perfume/brands/<string:brand_code>', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_brand(self, brand_code, **kwargs):
        """Get a specific brand with its perfumes"""
        try:
            brand = request.env['perfume.brand'].sudo().search([
                ('code', '=', brand_code),
                ('active', '=', True)
            ], limit=1)
            
            if not brand:
                return request.make_response(
                    json.dumps({'error': 'Brand not found'}, ensure_ascii=False),
                    status=404,
                    headers=[
                        ('Content-Type', 'application/json'),
                        ('Access-Control-Allow-Origin', '*'),
                    ]
                )
            
            perfumes_data = []
            for perfume in brand.perfumes.filtered(lambda p: p.active):
                perfumes_data.append(perfume.get_api_data())
            
            result = {
                'id': brand.code,
                'name': brand.name,
                'country': brand.country,
                'perfumes': perfumes_data
            }
            
            return request.make_response(
                json.dumps(result, ensure_ascii=False),
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error in get_brand: {e}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e)}, ensure_ascii=False),
                status=500,
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )

    @http.route('/api/perfume/perfumes', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_perfumes(self, brand_id=None, **kwargs):
        """Get all perfumes, optionally filtered by brand"""
        try:
            domain = [('active', '=', True)]
            if brand_id:
                brand = request.env['perfume.brand'].sudo().search([
                    ('code', '=', brand_id)
                ], limit=1)
                if brand:
                    domain.append(('brand_id', '=', brand.id))
            
            perfumes = request.env['perfume.perfume'].sudo().search(domain)
            
            result = []
            for perfume in perfumes:
                result.append(perfume.get_api_data())
            
            return request.make_response(
                json.dumps(result, ensure_ascii=False),
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error in get_perfumes: {e}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e)}, ensure_ascii=False),
                status=500,
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )

    @http.route('/api/perfume/perfumes/<string:perfume_code>', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_perfume(self, perfume_code, **kwargs):
        """Get a specific perfume by code"""
        try:
            perfume = request.env['perfume.perfume'].sudo().search([
                ('code', '=', perfume_code),
                ('active', '=', True)
            ], limit=1)
            
            if not perfume:
                return request.make_response(
                    json.dumps({'error': 'Perfume not found'}, ensure_ascii=False),
                    status=404,
                    headers=[
                        ('Content-Type', 'application/json'),
                        ('Access-Control-Allow-Origin', '*'),
                    ]
                )
            
            result = perfume.get_api_data()
            
            return request.make_response(
                json.dumps(result, ensure_ascii=False),
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error in get_perfume: {e}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e)}, ensure_ascii=False),
                status=500,
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )

    @http.route('/api/perfume/options', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_options(self, **kwargs):
        """Get all available options (seasons, occasions, notes)"""
        try:
            seasons = request.env['perfume.season'].sudo().search([('active', '=', True)])
            occasions = request.env['perfume.occasion'].sudo().search([('active', '=', True)])
            notes = request.env['perfume.note'].sudo().search([('active', '=', True)])
            
            result = {
                'seasons': seasons.mapped('name'),
                'occasions': occasions.mapped('name'),
                'notes': {
                    'top': notes.filtered(lambda n: n.category == 'top').mapped('name'),
                    'middle': notes.filtered(lambda n: n.category == 'middle').mapped('name'),
                    'base': notes.filtered(lambda n: n.category == 'base').mapped('name'),
                }
            }
            
            return request.make_response(
                json.dumps(result, ensure_ascii=False),
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error in get_options: {e}", exc_info=True)
            return request.make_response(
                json.dumps({'error': str(e)}, ensure_ascii=False),
                status=500,
                headers=[
                    ('Content-Type', 'application/json'),
                ]
            )

    @http.route('/api/perfume/options', type='http', auth='public', methods=['OPTIONS'], csrf=False, cors='*')
    def options_cors(self, **kwargs):
        """Handle CORS preflight requests"""
        return request.make_response(
            '',
            headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
                ('Access-Control-Max-Age', '3600'),
            ]
        )

