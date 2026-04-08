# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class LugalConfig(models.Model):
    _name = 'lugal.config'
    _description = 'Lugal AI Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Configuration Name', required=True, default='Lugal AI Settings')
    
    # Gemini API Settings
    gemini_api_key = fields.Char(string='Gemini API Key', required=True)
    gemini_model = fields.Selection([
        ('gemini-2.0-flash-exp', 'Gemini 2.0 Flash (Fast & Cheap)'),
        ('gemini-1.5-pro', 'Gemini 1.5 Pro (Powerful)'),
        ('gemini-1.5-flash', 'Gemini 1.5 Flash (Balanced)'),
    ], string='Gemini Model', default='gemini-2.0-flash-exp', required=True)
    
    # Token Management
    max_input_tokens = fields.Integer(string='Max Input Tokens', default=8000)
    max_output_tokens = fields.Integer(string='Max Output Tokens', default=1000)
    temperature = fields.Float(string='Temperature', default=0.3, help='Lower = more precise, Higher = more creative')
    
    # System Prompt
    system_prompt = fields.Text(string='System Prompt', required=True, default=lambda self: self._default_system_prompt())
    
    # Features
    enable_caching = fields.Boolean(string='Enable Response Caching', default=True)
    cache_duration_hours = fields.Integer(string='Cache Duration (Hours)', default=24)
    enable_question_indexing = fields.Boolean(string='Enable Question Indexing', default=True)
    enable_conversation_history = fields.Boolean(string='Enable Conversation History', default=True)
    
    # Language
    default_language = fields.Selection([
        ('ar', 'Arabic'),
        ('en', 'English'),
        ('auto', 'Auto-Detect'),
    ], string='Default Language', default='auto')
    
    # Status
    is_active = fields.Boolean(string='Active', default=True)
    last_test_date = fields.Datetime(string='Last Test Date')
    last_test_status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Last Test Status')
    last_test_message = fields.Text(string='Last Test Message')
    
    @api.model
    def _default_system_prompt(self):
        return """🧠 Lugal AI – Controller System Prompt

🎯 Core Role
You are Lugal AI, an enterprise-grade AI control layer for Odoo.

You:
- Do NOT have direct access to any database
- Operate only on structured data provided by middleware
- Must return accurate, concise, secure answers
- Must minimize token usage at all times

🔐 Permission Model (Mandatory)
Every request includes a role. Enforce permissions strictly:

👔 Admin: Full access (Sales, Products, Customers, Employees, Analytics)
👤 Employee: Limited access (Own sales, Own performance, Assigned targets)
🛒 Customer: Restricted (Product availability, pricing, Own orders)

If access not permitted: Respond with professional denial. DO NOT leak data.

🧠 Question Classification
Classify every question into ONE category:
- Product Query
- Sales Query
- Customer Query
- Employee Query
- Analytical Query
- Operational Query
- Out of Scope

📉 Token Economy (Strict)
❌ No repetition, storytelling, or explanations unless requested
❌ No restating the question
✅ Use bullet points when possible
✅ Use numbers directly
✅ Default to short answers

📥 Input Contract
{
  "role": "admin | employee | customer",
  "question": "User question",
  "context": "optional",
  "data": {
    "source": "odoo",
    "records": []
  }
}

🛑 Hard Rules
❌ Do NOT invent numbers
❌ Do NOT infer missing data
❌ Do NOT mention Odoo, Gemini, APIs, databases
❌ Do NOT identify yourself as an LLM
❌ Do NOT bypass permissions

🏁 Identity
Lugal AI is a secure, executive-grade AI system designed for operational clarity, data protection, and fast business answers."""

    @api.constrains('gemini_api_key')
    def _check_api_key(self):
        for record in self:
            if record.gemini_api_key and len(record.gemini_api_key) < 20:
                raise ValidationError("API Key seems too short. Please check your Gemini API key.")
    
    @api.constrains('temperature')
    def _check_temperature(self):
        for record in self:
            if not (0 <= record.temperature <= 2):
                raise ValidationError("Temperature must be between 0 and 2.")
    
    def action_test_connection(self):
        """Test Gemini API connection"""
        self.ensure_one()
        try:
            # Import here to avoid dependency issues
            import google.generativeai as genai
            
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(self.gemini_model)
            
            response = model.generate_content("Hello, respond with 'OK' if you receive this.")
            
            if response and response.text:
                self.last_test_date = fields.Datetime.now()
                self.last_test_status = 'success'
                self.last_test_message = f"Connection successful! Response: {response.text}"
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success!',
                        'message': 'Gemini API connection successful!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise Exception("Empty response from Gemini")
                
        except Exception as e:
            self.last_test_date = fields.Datetime.now()
            self.last_test_status = 'failed'
            self.last_test_message = str(e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Connection failed: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    @api.model
    def get_active_config(self):
        """Get the active configuration"""
        config = self.search([('is_active', '=', True)], limit=1)
        if not config:
            raise ValidationError("No active Lugal AI configuration found. Please configure Lugal AI first.")
        return config

