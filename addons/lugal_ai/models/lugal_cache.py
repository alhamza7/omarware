# -*- coding: utf-8 -*-

from odoo import models, fields, api
import hashlib
import json
import logging

_logger = logging.getLogger(__name__)


class LugalCache(models.Model):
    _name = 'lugal.cache'
    _description = 'Lugal AI Response Cache'
    _rec_name = 'cache_key'
    _order = 'last_accessed desc'

    cache_key = fields.Char(string='Cache Key', required=True, index=True,
                             help='Hash of question + role + context')
    
    # Question & Context
    question = fields.Text(string='Question', required=True)
    user_role = fields.Selection([
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('customer', 'Customer'),
    ], string='User Role', required=True, index=True)
    
    category = fields.Selection([
        ('product', 'Product Query'),
        ('sales', 'Sales Query'),
        ('customer', 'Customer Query'),
        ('employee', 'Employee Query'),
        ('analytical', 'Analytical Query'),
        ('operational', 'Operational Query'),
        ('out_of_scope', 'Out of Scope'),
    ], string='Category', index=True)
    
    # Cached Response
    answer = fields.Text(string='Cached Answer', required=True)
    
    # Context Fingerprint (for cache validation)
    context_fingerprint = fields.Char(string='Context Fingerprint',
                                       help='Hash of data structure (not values) to validate cache freshness')
    
    # Statistics
    hit_count = fields.Integer(string='Cache Hits', default=0, readonly=True)
    last_accessed = fields.Datetime(string='Last Accessed', default=fields.Datetime.now)
    created_date = fields.Datetime(string='Created', default=fields.Datetime.now, readonly=True)
    
    # Expiry
    expires_at = fields.Datetime(string='Expires At', required=True, index=True)
    is_expired = fields.Boolean(string='Is Expired', compute='_compute_is_expired', search='_search_is_expired')
    
    # Token Usage
    saved_input_tokens = fields.Integer(string='Saved Input Tokens',
                                         help='Tokens saved by using cache instead of API')
    saved_output_tokens = fields.Integer(string='Saved Output Tokens')
    
    @api.depends('expires_at')
    def _compute_is_expired(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_expired = record.expires_at < now if record.expires_at else True
    
    def _search_is_expired(self, operator, value):
        now = fields.Datetime.now()
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('expires_at', '<', now)]
        else:
            return [('expires_at', '>=', now)]
    
    @api.model
    def generate_cache_key(self, question, role, context_data=None):
        """Generate unique cache key from question, role, and context"""
        # Normalize question
        question_normalized = question.lower().strip()
        
        # Create fingerprint of context structure (not values)
        context_fingerprint = ""
        if context_data:
            try:
                context_dict = json.loads(context_data) if isinstance(context_data, str) else context_data
                # Only hash the structure (keys), not values (as values may change)
                structure = self._get_structure(context_dict)
                context_fingerprint = hashlib.md5(json.dumps(structure, sort_keys=True).encode()).hexdigest()
            except:
                pass
        
        # Combine all components
        key_string = f"{question_normalized}|{role}|{context_fingerprint}"
        cache_key = hashlib.sha256(key_string.encode()).hexdigest()
        
        return cache_key, context_fingerprint
    
    @api.model
    def _get_structure(self, obj):
        """Extract structure (keys/types) from object, ignoring values"""
        if isinstance(obj, dict):
            return {k: self._get_structure(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return ['list'] if not obj else [self._get_structure(obj[0])]
        else:
            return type(obj).__name__
    
    @api.model
    def get_cached_response(self, question, role, context_data=None):
        """Get cached response if available and not expired"""
        cache_key, context_fingerprint = self.generate_cache_key(question, role, context_data)
        
        # Search for valid cache entry
        cache_entry = self.search([
            ('cache_key', '=', cache_key),
            ('user_role', '=', role),
            ('expires_at', '>=', fields.Datetime.now()),
        ], limit=1)
        
        if cache_entry:
            # Validate context hasn't changed structure
            if cache_entry.context_fingerprint != context_fingerprint:
                _logger.info(f"Cache invalidated due to context structure change: {cache_key}")
                cache_entry.unlink()
                return None
            
            # Update hit statistics
            cache_entry.sudo().write({
                'hit_count': cache_entry.hit_count + 1,
                'last_accessed': fields.Datetime.now(),
            })
            
            _logger.info(f"Cache HIT for key: {cache_key} (hits: {cache_entry.hit_count + 1})")
            return cache_entry.answer
        
        _logger.info(f"Cache MISS for key: {cache_key}")
        return None
    
    @api.model
    def set_cached_response(self, question, role, answer, category=None, context_data=None, 
                             input_tokens=0, output_tokens=0, cache_duration_hours=24):
        """Store response in cache"""
        cache_key, context_fingerprint = self.generate_cache_key(question, role, context_data)
        
        # Calculate expiry
        expires_at = fields.Datetime.now() + fields.timedelta(hours=cache_duration_hours)
        
        # Check if cache entry already exists
        existing = self.search([('cache_key', '=', cache_key)], limit=1)
        
        if existing:
            # Update existing
            existing.write({
                'answer': answer,
                'category': category,
                'context_fingerprint': context_fingerprint,
                'expires_at': expires_at,
                'last_accessed': fields.Datetime.now(),
            })
            _logger.info(f"Cache UPDATED for key: {cache_key}")
        else:
            # Create new
            self.create({
                'cache_key': cache_key,
                'question': question,
                'user_role': role,
                'category': category,
                'answer': answer,
                'context_fingerprint': context_fingerprint,
                'expires_at': expires_at,
                'saved_input_tokens': input_tokens,
                'saved_output_tokens': output_tokens,
            })
            _logger.info(f"Cache STORED for key: {cache_key}")
        
        return cache_key
    
    @api.model
    def cleanup_expired_cache(self):
        """Remove expired cache entries (to be called by scheduled action)"""
        expired = self.search([('expires_at', '<', fields.Datetime.now())])
        count = len(expired)
        expired.unlink()
        _logger.info(f"Cleaned up {count} expired cache entries")
        return count
    
    @api.model
    def get_cache_stats(self):
        """Get cache performance statistics"""
        all_cache = self.search([])
        active_cache = all_cache.filtered(lambda c: not c.is_expired)
        
        total_hits = sum(all_cache.mapped('hit_count'))
        total_saved_tokens = sum(all_cache.mapped('saved_input_tokens')) + sum(all_cache.mapped('saved_output_tokens'))
        
        return {
            'total_entries': len(all_cache),
            'active_entries': len(active_cache),
            'expired_entries': len(all_cache) - len(active_cache),
            'total_hits': total_hits,
            'total_saved_tokens': total_saved_tokens,
            'avg_hits_per_entry': total_hits / len(all_cache) if all_cache else 0,
            'hit_rate': (total_hits / (len(all_cache) + total_hits)) * 100 if all_cache else 0,
        }

