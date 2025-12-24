# NBS Archive System - Odoo Module Implementation Plan

## Executive Summary

This document provides a comprehensive architectural plan for building the Noor Al Nibras (NBS) Enterprise Archiving System as an **Odoo Custom Module** instead of a standalone application.

**Key Decision**: Converting the original FastAPI/React architecture to Odoo changes many aspects but maintains all core business requirements.

---

## 1. Architecture Overview

### 1.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Odoo Instance (v17+)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │        Custom Module: nbs_archive                  │     │
│  │                                                     │     │
│  │  ├── Models (Odoo ORM)                             │     │
│  │  │   ├── nbs.department                            │     │
│  │  │   ├── nbs.document.type                         │     │
│  │  │   ├── nbs.document                              │     │
│  │  │   ├── nbs.document.version                      │     │
│  │  │   ├── nbs.edit.request                          │     │
│  │  │   ├── nbs.audit.log                             │     │
│  │  │   └── nbs.notification                          │     │
│  │                                                     │     │
│  │  ├── Views (QWeb/XML)                              │     │
│  │  │   ├── Tree views                                │     │
│  │  │   ├── Form views                                │     │
│  │  │   ├── Kanban views                              │     │
│  │  │   └── Custom dashboard views                    │     │
│  │                                                     │     │
│  │  ├── Controllers (HTTP Routes)                     │     │
│  │  │   ├── Document upload                           │     │
│  │  │   ├── Search API                                │     │
│  │  │   ├── Download endpoints                        │     │
│  │  │   └── WebSocket proxy                           │     │
│  │                                                     │     │
│  │  ├── JavaScript/OWL Components                     │     │
│  │  │   ├── Document viewer widget                    │     │
│  │  │   ├── Search widget with highlight              │     │
│  │  │   ├── Barcode scanner                           │     │
│  │  │   ├── Voice search                              │     │
│  │  │   └── Notification center                       │     │
│  │                                                     │     │
│  │  ├── Security (ir.model.access.csv, rules)        │     │
│  │  ├── Data (seed: departments, doc types)          │     │
│  │  └── Wizards (edit requests, approvals)           │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────┐        ┌─────────────┐      ┌──────────────┐
    │PostgreSQL│        │ OpenSearch  │      │    Redis     │
    │(Odoo DB) │        │  (Search)   │      │(Queue/Cache) │
    └──────────┘        └─────────────┘      └──────────────┘
```

### 1.2 Technology Stack Adaptation

| Requirement | Original Spec | Odoo Adaptation |
|-------------|---------------|-----------------|
| **Backend** | FastAPI | Odoo Python (same Python, different framework) |
| **ORM** | SQLAlchemy 2.x + Alembic | Odoo ORM (built-in, similar to SQLAlchemy) |
| **Frontend** | React + Vite + TypeScript | Odoo Web (Owl framework + JavaScript + QWeb) |
| **Auth** | Custom JWT | Odoo's built-in auth + custom access rules |
| **Database** | PostgreSQL | PostgreSQL (✓ Same) |
| **Search** | OpenSearch | OpenSearch (external service, same) |
| **OCR** | Celery + Redis | Odoo Queue Job module + Redis |
| **WebSocket** | Custom | Odoo Bus / longpolling + Redis |
| **API** | REST API | Odoo RPC (XML-RPC/JSON-RPC) + Custom REST |

---

## 2. Database Models (Odoo ORM)

### 2.1 Core Models

#### nbs.department
```python
class NBSDepartment(models.Model):
    _name = 'nbs.department'
    _description = 'NBS Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(required=True, translate=True)  # Bilingual
    code = fields.Char(required=True, size=10, index=True)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    manager_ids = fields.Many2many('res.users', 'nbs_dept_manager_rel')
    user_ids = fields.Many2many('res.users', 'nbs_dept_user_rel')
    document_type_ids = fields.One2many('nbs.document.type', 'department_id')
    color = fields.Integer('Color Index')
```

#### nbs.document.type
```python
class NBSDocumentType(models.Model):
    _name = 'nbs.document.type'
    _description = 'Document Type Template'
    
    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    department_id = fields.Many2one('nbs.department', required=True)
    
    # Dynamic fields configuration (stored as JSON)
    custom_field_config = fields.Text('Custom Fields JSON')
    # Example: [
    #   {"name": "bl_number", "type": "char", "label": "BL Number", "required": true},
    #   {"name": "container_number", "type": "char", "label": "Container #", "required": false}
    # ]
    
    mandatory_fields = fields.Text('Mandatory Fields List')  # JSON array
    active = fields.Boolean(default=True)
```

#### nbs.document
```python
class NBSDocument(models.Model):
    _name = 'nbs.document'
    _description = 'NBS Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # CORE FIELDS (always present)
    name = fields.Char('Title', required=True, tracking=True)
    department_id = fields.Many2one('nbs.department', required=True, readonly=True)
    document_type_id = fields.Many2one('nbs.document.type', required=True, readonly=True)
    
    # User info
    uploader_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    upload_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    
    # Tags
    tag_ids = fields.Many2many('nbs.document.tag', string='Tags')
    
    # Related numbers (stored as individual fields + searchable)
    po_number = fields.Char('PO Number', index=True)
    bl_number = fields.Char('BL Number', index=True)
    container_number = fields.Char('Container Number', index=True)
    invoice_number = fields.Char('Invoice Number', index=True)
    envoy_number = fields.Char('Envoy Number', index=True)
    
    # Status
    state = fields.Selection([
        ('active', 'Active'),
        ('archived', 'Archived')
    ], default='active', required=True, tracking=True)
    
    # Confidentiality
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('strict', 'Strict')
    ], default='internal', required=True, tracking=True)
    
    # Versioning
    current_version_id = fields.Many2one('nbs.document.version', readonly=True)
    version_ids = fields.One2many('nbs.document.version', 'document_id')
    version_count = fields.Integer(compute='_compute_version_count')
    
    # Barcode
    barcode = fields.Char('Barcode', readonly=True, index=True, copy=False)
    
    # Lock status
    is_locked = fields.Boolean('Locked', default=True, readonly=True)
    unlock_token = fields.Char('One-time Unlock Token', readonly=True)
    unlock_expiry = fields.Datetime('Unlock Expiry', readonly=True)
    
    # Dynamic fields (type-specific, stored as JSON)
    custom_fields_data = fields.Text('Custom Fields Data JSON')
    
    # Edit requests
    edit_request_ids = fields.One2many('nbs.edit.request', 'document_id')
    pending_edit_request_count = fields.Integer(compute='_compute_pending_requests')
    
    # OCR status
    ocr_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    
    # Search indexing
    indexed_in_search = fields.Boolean('Indexed', default=False)
    
    @api.model
    def create(self, vals):
        # Generate barcode
        vals['barcode'] = self._generate_barcode()
        doc = super().create(vals)
        # Trigger OCR job
        doc._schedule_ocr()
        return doc
    
    def _generate_barcode(self):
        return f"NBS{self.env['ir.sequence'].next_by_code('nbs.document.barcode')}"
    
    def _schedule_ocr(self):
        # Queue job for OCR
        self.env['queue.job'].sudo().create({
            'name': f'OCR: {self.name}',
            'model_name': 'nbs.document',
            'method_name': '_process_ocr',
            'args': str([self.id])
        })
```

#### nbs.document.version
```python
class NBSDocumentVersion(models.Model):
    _name = 'nbs.document.version'
    _description = 'Document Version'
    _order = 'version_number desc'
    
    document_id = fields.Many2one('nbs.document', required=True, ondelete='restrict')
    version_number = fields.Integer(required=True, readonly=True)
    
    # File storage
    file_data = fields.Binary('File', attachment=True)
    file_name = fields.Char('Filename')
    file_size = fields.Integer('Size (bytes)')
    file_type = fields.Char('MIME Type')
    file_path = fields.Char('Server Path', readonly=True)
    
    # Extracted text (for search)
    extracted_text = fields.Text('Extracted Text')
    extracted_text_per_page = fields.Text('Per-Page Text JSON')
    # JSON: [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}]
    
    # OCR
    ocr_completed = fields.Boolean('OCR Done', default=False)
    ocr_language = fields.Char('OCR Languages', default='ara+eng')
    
    # Metadata
    uploader_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    upload_date = fields.Datetime(default=fields.Datetime.now)
    notes = fields.Text('Version Notes')
    
    # CRITICAL: NO DELETE
    _sql_constraints = [
        ('no_delete', 'CHECK(1=1)', 'Versions cannot be deleted!')
    ]
```

#### nbs.edit.request
```python
class NBSEditRequest(models.Model):
    _name = 'nbs.edit.request'
    _description = 'Edit Request'
    _inherit = ['mail.thread']
    _order = 'create_date desc'
    
    document_id = fields.Many2one('nbs.document', required=True)
    requester_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    request_date = fields.Datetime(default=fields.Datetime.now)
    
    reason = fields.Text('Reason', required=True)
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ], default='pending', tracking=True)
    
    approver_id = fields.Many2one('res.users')
    approval_date = fields.Datetime()
    approval_notes = fields.Text()
    
    unlock_token = fields.Char('Unlock Token', readonly=True)
    
    def action_approve(self):
        self.ensure_one()
        token = secrets.token_urlsafe(32)
        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'unlock_token': token
        })
        self.document_id.write({
            'unlock_token': token,
            'unlock_expiry': fields.Datetime.now() + timedelta(hours=24)
        })
        # Send notification
        self._send_notification('approved')
```

#### nbs.audit.log
```python
class NBSAuditLog(models.Model):
    _name = 'nbs.audit.log'
    _description = 'Audit Log'
    _order = 'timestamp desc'
    _rec_name = 'action'
    
    timestamp = fields.Datetime(default=fields.Datetime.now, readonly=True, index=True)
    user_id = fields.Many2one('res.users', readonly=True, required=True)
    action = fields.Selection([
        ('upload', 'Upload'),
        ('view', 'View'),
        ('download', 'Download'),
        ('edit_request', 'Edit Request'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('new_version', 'New Version'),
        ('archive', 'Archive'),
        ('unarchive', 'Unarchive'),
        ('search', 'Search')
    ], required=True, index=True)
    
    document_id = fields.Many2one('nbs.document', ondelete='restrict')
    department_id = fields.Many2one('nbs.department')
    
    ip_address = fields.Char('IP Address')
    user_agent = fields.Text('User Agent')
    
    details = fields.Text('Additional Details JSON')
    metadata_snapshot = fields.Text('Metadata Snapshot')
```

#### nbs.notification
```python
class NBSNotification(models.Model):
    _name = 'nbs.notification'
    _description = 'Notification'
    _order = 'create_date desc'
    
    user_id = fields.Many2one('res.users', required=True, index=True)
    title = fields.Char(required=True, translate=True)
    message = fields.Text(translate=True)
    
    notification_type = fields.Selection([
        ('upload', 'New Upload'),
        ('edit_request', 'Edit Request'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('new_version', 'New Version'),
        ('mention', 'Mention')
    ])
    
    document_id = fields.Many2one('nbs.document')
    edit_request_id = fields.Many2one('nbs.edit.request')
    
    is_read = fields.Boolean('Read', default=False)
    read_date = fields.Datetime()
    
    create_date = fields.Datetime(default=fields.Datetime.now)
```

---

## 3. Security & Access Control

### 3.1 Odoo Groups (ir.model.access)

```xml
<!-- security/nbs_security.xml -->
<odoo>
    <data>
        <!-- Base Groups -->
        <record id="group_nbs_user" model="res.groups">
            <field name="name">NBS User</field>
            <field name="category_id" ref="base.module_category_operations"/>
        </record>
        
        <record id="group_nbs_manager" model="res.groups">
            <field name="name">NBS Manager</field>
            <field name="implied_ids" eval="[(4, ref('group_nbs_user'))]"/>
        </record>
        
        <record id="group_nbs_admin" model="res.groups">
            <field name="name">NBS Admin</field>
            <field name="implied_ids" eval="[(4, ref('group_nbs_manager'))]"/>
        </record>
    </data>
</odoo>
```

### 3.2 Record Rules (Department Isolation)

```xml
<!-- security/nbs_record_rules.xml -->
<odoo>
    <data noupdate="1">
        <!-- Users can only see documents from their departments -->
        <record id="nbs_document_user_rule" model="ir.rule">
            <field name="name">User: Own Department Documents</field>
            <field name="model_id" ref="model_nbs_document"/>
            <field name="groups" eval="[(4, ref('group_nbs_user'))]"/>
            <field name="domain_force">
                [
                    ('department_id.user_ids', 'in', [user.id]),
                    '|',
                        ('confidentiality_level', 'in', ['public', 'internal']),
                        ('uploader_id', '=', user.id)
                ]
            </field>
        </record>
        
        <!-- Managers see confidential docs in their department -->
        <record id="nbs_document_manager_rule" model="ir.rule">
            <field name="name">Manager: Department Confidential</field>
            <field name="model_id" ref="model_nbs_document"/>
            <field name="groups" eval="[(4, ref('group_nbs_manager'))]"/>
            <field name="domain_force">
                [
                    ('department_id.manager_ids', 'in', [user.id]),
                    ('confidentiality_level', '!=', 'strict')
                ]
            </field>
        </record>
        
        <!-- Admins see everything except they must respect strict -->
        <record id="nbs_document_admin_rule" model="ir.rule">
            <field name="name">Admin: All Documents</field>
            <field name="model_id" ref="model_nbs_document"/>
            <field name="groups" eval="[(4, ref('group_nbs_admin'))]"/>
            <field name="domain_force">[(1, '=', 1)]</field>
        </record>
    </data>
</odoo>
```

### 3.3 Field-Level Security

```python
# In model definition:
@api.depends_context('uid')
def _compute_can_edit_tags(self):
    for rec in self:
        # Only managers can edit tags
        rec.can_edit_tags = self.env.user.has_group('nbs_archive.group_nbs_manager')

tag_ids = fields.Many2many('nbs.document.tag', readonly=True, 
                           states={'draft': [('readonly', False)]})
```

---

## 4. Document Upload & Storage

### 4.1 Storage Strategy

**Hybrid approach** (Odoo attachment system + file structure):

1. **Primary**: Odoo's `ir.attachment` model (stores in filestore)
2. **Organized**: Custom symlinks/copies in structured folders
3. **Path pattern**: `/opt/odoo/data/filestore/{db}/nbs/{dept_code}/{doc_type}/{doc_id}/v{version}/`

### 4.2 Upload Controller

```python
# controllers/document_controller.py
from odoo import http
from odoo.http import request, Response
import os, base64

class NBSDocumentController(http.Controller):
    
    @http.route('/nbs/upload', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_document(self, **post):
        file = post.get('file')
        doc_data = {
            'name': post.get('title'),
            'department_id': int(post.get('department_id')),
            'document_type_id': int(post.get('document_type_id')),
            'confidentiality_level': post.get('confidentiality_level', 'internal'),
            'custom_fields_data': post.get('custom_fields'),  # JSON
        }
        
        # Create document
        document = request.env['nbs.document'].sudo().create(doc_data)
        
        # Create first version
        version = request.env['nbs.document.version'].sudo().create({
            'document_id': document.id,
            'version_number': 1,
            'file_data': base64.b64encode(file.read()),
            'file_name': file.filename,
            'file_size': file.content_length,
            'file_type': file.content_type
        })
        
        # Update document
        document.write({'current_version_id': version.id})
        
        # Organize file physically
        document._organize_file_storage(version)
        
        # Log
        request.env['nbs.audit.log'].sudo().create({
            'user_id': request.env.user.id,
            'action': 'upload',
            'document_id': document.id,
            'department_id': document.department_id.id,
            'ip_address': request.httprequest.remote_addr
        })
        
        return Response(json.dumps({'document_id': document.id}), 
                       content_type='application/json')
```

---

## 5. OCR Pipeline

### 5.1 Architecture

Use **Odoo Queue Job** module (`queue_job`) instead of Celery:

```python
# models/nbs_document.py (continued)

def _schedule_ocr(self):
    """Schedule background OCR job"""
    self.with_delay(priority=5)._process_ocr()

def _process_ocr(self):
    """Background job: OCR processing"""
    self.ocr_status = 'processing'
    
    version = self.current_version_id
    if not version:
        return
    
    # Get file path
    file_path = version.file_path or self._get_attachment_path(version)
    
    # Convert to images if PDF
    if version.file_type == 'application/pdf':
        images = self._pdf_to_images(file_path)
    else:
        images = [file_path]
    
    # Run Tesseract OCR
    all_text = []
    per_page_text = []
    
    for idx, img in enumerate(images):
        try:
            text = pytesseract.image_to_string(
                img,
                lang='ara+eng',
                config='--oem 3 --psm 6'
            )
            all_text.append(text)
            per_page_text.append({'page': idx + 1, 'text': text})
        except Exception as e:
            _logger.error(f"OCR failed for page {idx}: {e}")
    
    # Update version
    version.write({
        'extracted_text': '\n\n'.join(all_text),
        'extracted_text_per_page': json.dumps(per_page_text, ensure_ascii=False),
        'ocr_completed': True
    })
    
    self.ocr_status = 'completed'
    
    # Index in OpenSearch
    self.with_delay()._index_in_opensearch()

def _pdf_to_images(self, pdf_path):
    """Convert PDF to images using pdf2image"""
    from pdf2image import convert_from_path
    return convert_from_path(pdf_path, dpi=300)
```

### 5.2 Queue Job Setup

```python
# __manifest__.py
'depends': ['base', 'web', 'mail', 'queue_job'],
```

---

## 6. OpenSearch Integration

### 6.1 Index Configuration

```python
# models/opensearch_service.py
from opensearchpy import OpenSearch

class OpenSearchService:
    
    def __init__(self):
        self.client = OpenSearch(
            hosts=[{'host': 'opensearch', 'port': 9200}],
            http_auth=('admin', 'admin'),
            use_ssl=False
        )
        self.index_name = 'nbs_documents'
    
    def create_index(self):
        """Create index with Arabic+English analyzers"""
        mapping = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "arabic_english": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "arabic_normalization", "asciifolding"]
                        }
                    }
                },
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            },
            "mappings": {
                "properties": {
                    "document_id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "analyzer": "arabic_english",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "arabic_english"
                    },
                    "pages": {
                        "type": "nested",
                        "properties": {
                            "page_number": {"type": "integer"},
                            "text": {"type": "text", "analyzer": "arabic_english"}
                        }
                    },
                    "department": {"type": "keyword"},
                    "document_type": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "barcode": {"type": "keyword"},
                    "po_number": {"type": "keyword"},
                    "bl_number": {"type": "keyword"},
                    "confidentiality_level": {"type": "keyword"},
                    "upload_date": {"type": "date"}
                }
            }
        }
        
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name, body=mapping)
    
    def index_document(self, doc_id, data):
        """Index a document"""
        self.client.index(
            index=self.index_name,
            id=doc_id,
            body=data,
            refresh=True
        )
    
    def search(self, query, filters=None, fuzzy=True):
        """Search with highlight"""
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "content", "pages.text"],
                                "fuzziness": "AUTO" if fuzzy else 0
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "highlight": {
                "fields": {
                    "content": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]},
                    "pages.text": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"]}
                },
                "number_of_fragments": 3,
                "fragment_size": 150
            },
            "size": 50
        }
        
        # Add filters
        if filters:
            if filters.get('department'):
                body['query']['bool']['filter'].append(
                    {"term": {"department": filters['department']}}
                )
            if filters.get('date_from'):
                body['query']['bool']['filter'].append(
                    {"range": {"upload_date": {"gte": filters['date_from']}}}
                )
        
        result = self.client.search(index=self.index_name, body=body)
        return result
```

### 6.2 Search Controller

```python
# controllers/search_controller.py

class NBSSearchController(http.Controller):
    
    @http.route('/nbs/search', type='json', auth='user')
    def search(self, query, filters=None, **kw):
        search_service = request.env['nbs.opensearch.service']
        results = search_service.search(query, filters)
        
        # Filter by department access
        user_dept_ids = request.env.user.nbs_department_ids.ids
        
        filtered_results = []
        for hit in results['hits']['hits']:
            doc_id = hit['_source']['document_id']
            document = request.env['nbs.document'].browse(doc_id)
            
            # Check access
            if document.department_id.id in user_dept_ids:
                filtered_results.append({
                    'id': doc_id,
                    'title': hit['_source']['title'],
                    'highlights': hit.get('highlight', {}),
                    'score': hit['_score']
                })
        
        # Log search
        request.env['nbs.audit.log'].create({
            'user_id': request.env.user.id,
            'action': 'search',
            'details': json.dumps({'query': query, 'results': len(filtered_results)})
        })
        
        return filtered_results
```

---

## 7. Versioning & Edit Request Flow

### 7.1 Edit Request Wizard

```python
# wizards/edit_request_wizard.py
class EditRequestWizard(models.TransientModel):
    _name = 'nbs.edit.request.wizard'
    
    document_id = fields.Many2one('nbs.document', required=True)
    reason = fields.Text('Reason for Edit', required=True)
    
    def action_submit_request(self):
        request = self.env['nbs.edit.request'].create({
            'document_id': self.document_id.id,
            'requester_id': self.env.user.id,
            'reason': self.reason
        })
        
        # Notify managers
        managers = self.document_id.department_id.manager_ids
        for manager in managers:
            self.env['nbs.notification'].create({
                'user_id': manager.id,
                'title': _('Edit Request: %s') % self.document_id.name,
                'message': _('%s requested to edit document') % self.env.user.name,
                'notification_type': 'edit_request',
                'edit_request_id': request.id
            })
        
        return {'type': 'ir.actions.act_window_close'}
```

### 7.2 New Version Upload (with token)

```python
# controllers/document_controller.py (continued)

@http.route('/nbs/upload_version', type='http', auth='user', methods=['POST'])
def upload_new_version(self, document_id, unlock_token, file, notes='', **kw):
    document = request.env['nbs.document'].browse(int(document_id))
    
    # Verify unlock token
    if document.unlock_token != unlock_token:
        return Response(json.dumps({'error': 'Invalid token'}), status=403)
    
    if document.unlock_expiry < fields.Datetime.now():
        return Response(json.dumps({'error': 'Token expired'}), status=403)
    
    # Create new version
    new_version_number = document.version_count + 1
    version = request.env['nbs.document.version'].create({
        'document_id': document.id,
        'version_number': new_version_number,
        'file_data': base64.b64encode(file.read()),
        'file_name': file.filename,
        'notes': notes
    })
    
    # Update document
    document.write({
        'current_version_id': version.id,
        'unlock_token': False,
        'unlock_expiry': False
    })
    
    # Mark edit request as completed
    edit_request = request.env['nbs.edit.request'].search([
        ('document_id', '=', document.id),
        ('unlock_token', '=', unlock_token)
    ], limit=1)
    if edit_request:
        edit_request.state = 'completed'
    
    # Schedule OCR for new version
    document._schedule_ocr()
    
    # Notify requester
    # ... notification logic
    
    return Response(json.dumps({'version_id': version.id}))
```

---

## 8. WebSocket Notifications (Odoo Bus)

### 8.1 Using Odoo's Bus System

Odoo has a built-in notification system via `bus.bus`:

```python
# models/nbs_notification.py

class NBSNotification(models.Model):
    _name = 'nbs.notification'
    # ... (as defined above)
    
    @api.model
    def create(self, vals):
        notif = super().create(vals)
        # Send via Odoo bus
        self.env['bus.bus']._sendone(
            f'res.partner/{notif.user_id.partner_id.id}',
            'nbs_notification',
            {
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.notification_type
            }
        )
        return notif
```

### 8.2 Frontend Listener (JavaScript)

```javascript
// static/src/js/notification_service.js
odoo.define('nbs_archive.notification_service', function (require) {
    "use strict";
    
    const { registry } = require("@web/core/registry");
    const { useService } = require("@web/core/utils/hooks");
    
    class NotificationService {
        setup() {
            this.bus = useService("bus_service");
            this.bus.addEventListener("notification", this._onNotification.bind(this));
            this.bus.start();
        }
        
        _onNotification(notifications) {
            for (let notif of notifications) {
                if (notif.type === 'nbs_notification') {
                    this._showNotification(notif.payload);
                }
            }
        }
        
        _showNotification(data) {
            // Show toast/banner
            this.env.services.notification.add(data.title, {
                type: 'info',
                sticky: false
            });
        }
    }
    
    registry.category("services").add("nbs_notification", NotificationService);
});
```

---

## 9. Frontend UI (Odoo Views + Custom Widgets)

### 9.1 Menu Structure

```xml
<!-- views/nbs_menu.xml -->
<odoo>
    <data>
        <!-- Main Menu -->
        <menuitem id="menu_nbs_root" name="NBS Archive" sequence="10"/>
        
        <!-- Dashboard -->
        <menuitem id="menu_nbs_dashboard" name="Dashboard" 
                  parent="menu_nbs_root" sequence="1"
                  action="action_nbs_dashboard"/>
        
        <!-- Documents -->
        <menuitem id="menu_nbs_documents" name="Documents" 
                  parent="menu_nbs_root" sequence="2"/>
        
        <menuitem id="menu_nbs_documents_all" name="All Documents" 
                  parent="menu_nbs_documents" sequence="1"
                  action="action_nbs_document_all"/>
        
        <menuitem id="menu_nbs_documents_my_uploads" name="My Uploads" 
                  parent="menu_nbs_documents" sequence="2"
                  action="action_nbs_document_my_uploads"/>
        
        <!-- Search -->
        <menuitem id="menu_nbs_search" name="Search" 
                  parent="menu_nbs_root" sequence="3"
                  action="action_nbs_search"/>
        
        <!-- Edit Requests (Manager only) -->
        <menuitem id="menu_nbs_edit_requests" name="Edit Requests" 
                  parent="menu_nbs_root" sequence="4"
                  action="action_nbs_edit_requests"
                  groups="group_nbs_manager"/>
        
        <!-- Configuration (Admin only) -->
        <menuitem id="menu_nbs_config" name="Configuration" 
                  parent="menu_nbs_root" sequence="100"
                  groups="group_nbs_admin"/>
        
        <menuitem id="menu_nbs_departments" name="Departments" 
                  parent="menu_nbs_config" sequence="1"
                  action="action_nbs_department"/>
        
        <menuitem id="menu_nbs_document_types" name="Document Types" 
                  parent="menu_nbs_config" sequence="2"
                  action="action_nbs_document_type"/>
    </data>
</odoo>
```

### 9.2 Document Form View with Custom Widgets

```xml
<!-- views/nbs_document_views.xml -->
<odoo>
    <record id="view_nbs_document_form" model="ir.ui.view">
        <field name="name">nbs.document.form</field>
        <field name="model">nbs.document</field>
        <field name="arch" type="xml">
            <form string="Document">
                <header>
                    <button name="action_archive" type="object" string="Archive" 
                            class="btn-warning" groups="group_nbs_manager"
                            attrs="{'invisible': [('state', '=', 'archived')]}"/>
                    <button name="action_request_edit" type="object" string="Request Edit" 
                            class="btn-primary"
                            attrs="{'invisible': [('state', '=', 'archived')]}"/>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="action_view_versions" type="object" 
                                class="oe_stat_button" icon="fa-history">
                            <field name="version_count" widget="statinfo" string="Versions"/>
                        </button>
                        <button name="action_view_audit_logs" type="object" 
                                class="oe_stat_button" icon="fa-list">
                            <div class="o_stat_info">
                                <span class="o_stat_text">Audit Logs</span>
                            </div>
                        </button>
                    </div>
                    
                    <widget name="web_ribbon" title="Archived" bg_color="bg-danger" 
                            attrs="{'invisible': [('state', '!=', 'archived')]}"/>
                    
                    <div class="oe_title">
                        <label for="name" class="oe_edit_only"/>
                        <h1><field name="name" readonly="1"/></h1>
                    </div>
                    
                    <group>
                        <group>
                            <field name="department_id" readonly="1"/>
                            <field name="document_type_id" readonly="1"/>
                            <field name="barcode" widget="barcode"/>
                            <field name="confidentiality_level" readonly="1"/>
                        </group>
                        <group>
                            <field name="uploader_id" readonly="1"/>
                            <field name="upload_date" readonly="1"/>
                            <field name="current_version_id" readonly="1"/>
                            <field name="ocr_status" widget="badge"/>
                        </group>
                    </group>
                    
                    <notebook>
                        <page string="Document Viewer">
                            <field name="current_version_id" invisible="1"/>
                            <!-- Custom widget for PDF/image viewer -->
                            <widget name="nbs_document_viewer" 
                                    document_id="id" 
                                    version_id="current_version_id"/>
                        </page>
                        
                        <page string="Metadata">
                            <group>
                                <field name="tag_ids" widget="many2many_tags" 
                                       readonly="1" groups="group_nbs_manager"/>
                                <field name="po_number" readonly="1"/>
                                <field name="bl_number" readonly="1"/>
                                <field name="container_number" readonly="1"/>
                                <field name="invoice_number" readonly="1"/>
                            </group>
                            <!-- Dynamic fields from custom_fields_data -->
                            <widget name="nbs_custom_fields" 
                                    document_type_id="document_type_id"
                                    custom_data="custom_fields_data"/>
                        </page>
                        
                        <page string="Versions">
                            <field name="version_ids" nolabel="1">
                                <tree>
                                    <field name="version_number"/>
                                    <field name="file_name"/>
                                    <field name="uploader_id"/>
                                    <field name="upload_date"/>
                                    <field name="ocr_completed"/>
                                    <button name="action_download" type="object" 
                                            string="Download" icon="fa-download"/>
                                </tree>
                            </field>
                        </page>
                        
                        <page string="Edit Requests" groups="group_nbs_manager">
                            <field name="edit_request_ids" nolabel="1"/>
                        </page>
                    </notebook>
                </sheet>
                <div class="oe_chatter">
                    <field name="message_follower_ids"/>
                    <field name="message_ids"/>
                </div>
            </form>
        </field>
    </record>
</odoo>
```

### 9.3 Custom JavaScript Widget: Document Viewer

```javascript
// static/src/components/document_viewer/document_viewer.js
/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class DocumentViewer extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            pdfUrl: null,
            currentPage: 1,
            totalPages: 0,
            zoom: 1.0
        });
        
        onWillStart(async () => {
            await this.loadDocument();
        });
    }
    
    async loadDocument() {
        const result = await this.rpc("/nbs/document/view", {
            document_id: this.props.document_id,
            version_id: this.props.version_id
        });
        this.state.pdfUrl = result.url;
        this.state.totalPages = result.pages;
    }
    
    nextPage() {
        if (this.state.currentPage < this.state.totalPages) {
            this.state.currentPage++;
        }
    }
    
    prevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
        }
    }
    
    zoomIn() {
        this.state.zoom = Math.min(this.state.zoom + 0.1, 3.0);
    }
    
    zoomOut() {
        this.state.zoom = Math.max(this.state.zoom - 0.1, 0.5);
    }
}

DocumentViewer.template = "nbs_archive.DocumentViewer";
DocumentViewer.props = {
    document_id: Number,
    version_id: Number
};

registry.category("fields").add("nbs_document_viewer", DocumentViewer);
```

### 9.4 Search Interface with Barcode/Voice

```xml
<!-- views/nbs_search_view.xml -->
<record id="view_nbs_search" model="ir.ui.view">
    <field name="name">nbs.search.view</field>
    <field name="model">nbs.document</field>
    <field name="arch" type="xml">
        <form string="Search Documents">
            <sheet>
                <group>
                    <field name="search_query" placeholder="Search documents..."
                           widget="nbs_search_box"/>
                    
                    <div class="o_row">
                        <button name="action_voice_search" type="object" 
                                string="Voice Search" icon="fa-microphone"
                                class="btn-primary"/>
                        <button name="action_barcode_scan" type="object" 
                                string="Scan Barcode" icon="fa-qrcode"
                                class="btn-info"/>
                    </div>
                </group>
                
                <group string="Filters">
                    <field name="department_filter"/>
                    <field name="document_type_filter"/>
                    <field name="date_from_filter"/>
                    <field name="date_to_filter"/>
                </group>
                
                <separator string="Results"/>
                <field name="search_results" nolabel="1">
                    <tree>
                        <field name="name"/>
                        <field name="highlights" widget="html"/>
                        <field name="department_id"/>
                        <field name="score"/>
                        <button name="action_open_document" type="object" 
                                string="Open" icon="fa-external-link"/>
                    </tree>
                </field>
            </sheet>
        </form>
    </field>
</record>
```

### 9.5 Voice Search Widget

```javascript
// static/src/components/voice_search/voice_search.js
/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class VoiceSearch extends Component {
    setup() {
        this.state = useState({
            isListening: false,
            transcript: ""
        });
        
        // Check browser support
        this.recognition = null;
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.lang = this.props.language || 'ar-SA'; // Arabic default
            this.recognition.interimResults = false;
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.state.transcript = transcript;
                this.props.onTranscript(transcript);
            };
            
            this.recognition.onend = () => {
                this.state.isListening = false;
            };
        }
    }
    
    startListening() {
        if (this.recognition) {
            this.state.isListening = true;
            this.recognition.start();
        } else {
            alert("Voice recognition not supported in this browser");
        }
    }
    
    stopListening() {
        if (this.recognition) {
            this.recognition.stop();
        }
    }
}

VoiceSearch.template = "nbs_archive.VoiceSearch";
registry.category("fields").add("nbs_voice_search", VoiceSearch);
```

---

## 10. Bilingual Support (Arabic RTL + English)

### 10.1 Translation Files

```xml
<!-- i18n/ar.po -->
# Arabic translation for nbs_archive
msgid ""
msgstr ""
"Language: ar\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"

#. module: nbs_archive
#: model:ir.model.fields,field_description:nbs_archive.field_nbs_document__name
msgid "Title"
msgstr "العنوان"

#: model:ir.model.fields,field_description:nbs_archive.field_nbs_document__department_id
msgid "Department"
msgstr "القسم"

#: model:ir.ui.menu,name:nbs_archive.menu_nbs_root
msgid "NBS Archive"
msgstr "أرشيف نور النبراس"

#: model:ir.actions.act_window,name:nbs_archive.action_nbs_search
msgid "Search"
msgstr "بحث"

# ... more translations
```

### 10.2 RTL CSS

```css
/* static/src/css/nbs_rtl.css */
.o_nbs_archive[dir="rtl"] {
    direction: rtl;
    text-align: right;
}

.o_nbs_archive[dir="rtl"] .o_form_sheet {
    direction: rtl;
}

.o_nbs_archive[dir="rtl"] .o_input,
.o_nbs_archive[dir="rtl"] .o_field_widget {
    text-align: right;
}

/* Fix Odoo's default LTR styling for Arabic */
body[dir="rtl"] .o_content {
    margin-right: 0;
    margin-left: auto;
}
```

### 10.3 Language Toggle

```python
# models/res_users.py (inherit)
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    preferred_nbs_language = fields.Selection([
        ('en_US', 'English'),
        ('ar_SA', 'Arabic')
    ], default='ar_SA')
    
    def action_toggle_nbs_language(self):
        self.ensure_one()
        new_lang = 'ar_SA' if self.preferred_nbs_language == 'en_US' else 'en_US'
        self.write({'preferred_nbs_language': new_lang})
        self.env.context = dict(self.env.context, lang=new_lang)
        return {'type': 'ir.actions.client', 'tag': 'reload'}
```

---

## 11. Backup & Restore Scripts

### 11.1 Backup Script

```bash
#!/bin/bash
# scripts/backup_nbs.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/odoo/backups/nbs_archive"
DB_NAME="odoo_new"
FILESTORE="/opt/odoo/data/filestore/$DB_NAME"

mkdir -p $BACKUP_DIR

echo "Starting NBS Archive backup: $DATE"

# 1. Backup PostgreSQL
echo "Backing up database..."
pg_dump -U odoo_user -h localhost $DB_NAME | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# 2. Backup filestore
echo "Backing up files..."
tar -czf "$BACKUP_DIR/filestore_$DATE.tar.gz" -C "$(dirname $FILESTORE)" "$(basename $FILESTORE)"

# 3. Backup OpenSearch indices (optional)
echo "Backing up OpenSearch index..."
curl -X POST "http://localhost:9200/_snapshot/nbs_backup/snapshot_$DATE?wait_for_completion=true"

# 4. Create manifest
echo "Creating manifest..."
cat > "$BACKUP_DIR/manifest_$DATE.json" <<EOF
{
  "date": "$DATE",
  "database": "db_$DATE.sql.gz",
  "filestore": "filestore_$DATE.tar.gz",
  "opensearch_snapshot": "snapshot_$DATE"
}
EOF

echo "Backup completed: $BACKUP_DIR"

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.json" -mtime +30 -delete
```

### 11.2 Restore Script

```bash
#!/bin/bash
# scripts/restore_nbs.sh

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20241217_143000"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_DIR="/opt/odoo/backups/nbs_archive"
DB_NAME="odoo_new"
FILESTORE="/opt/odoo/data/filestore/$DB_NAME"

echo "Restoring NBS Archive from backup: $BACKUP_DATE"

# 1. Stop Odoo
echo "Stopping Odoo..."
systemctl stop odoo

# 2. Restore database
echo "Restoring database..."
dropdb -U odoo_user $DB_NAME
createdb -U odoo_user $DB_NAME
gunzip -c "$BACKUP_DIR/db_$BACKUP_DATE.sql.gz" | psql -U odoo_user $DB_NAME

# 3. Restore filestore
echo "Restoring files..."
rm -rf $FILESTORE
tar -xzf "$BACKUP_DIR/filestore_$BACKUP_DATE.tar.gz" -C "$(dirname $FILESTORE)"

# 4. Restore OpenSearch (optional)
echo "Restoring OpenSearch..."
curl -X POST "http://localhost:9200/_snapshot/nbs_backup/snapshot_$BACKUP_DATE/_restore"

# 5. Start Odoo
echo "Starting Odoo..."
systemctl start odoo

echo "Restore completed!"
```

---

## 12. Docker Compose Setup

### 12.1 docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: odoo_user
      POSTGRES_PASSWORD: root
      POSTGRES_DB: odoo_new
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - nbs_network

  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - DISABLE_SECURITY_PLUGIN=true
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    ports:
      - "9200:9200"
      - "9600:9600"
    networks:
      - nbs_network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - nbs_network

  odoo:
    image: odoo:17.0
    depends_on:
      - postgres
      - redis
      - opensearch
    ports:
      - "8069:8069"
    volumes:
      - ./addons/nbs_archive:/mnt/extra-addons/nbs_archive
      - odoo_web_data:/var/lib/odoo
      - ./odoo.conf:/etc/odoo/odoo.conf
    environment:
      - HOST=postgres
      - USER=odoo_user
      - PASSWORD=root
    command: odoo --config=/etc/odoo/odoo.conf --dev=all
    networks:
      - nbs_network

volumes:
  postgres_data:
  opensearch_data:
  redis_data:
  odoo_web_data:

networks:
  nbs_network:
    driver: bridge
```

### 12.2 odoo.conf (for module)

```ini
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
db_host = postgres
db_port = 5432
db_user = odoo_user
db_password = root
admin_passwd = admin
dbfilter = ^odoo_new$

; Queue job configuration
server_wide_modules = base,web,queue_job
workers = 2
max_cron_threads = 1

; Redis for queue_job
redis_host = redis
redis_port = 6379
```

---

## 13. Module Structure

```
nbs_archive/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── nbs_department.py
│   ├── nbs_document.py
│   ├── nbs_document_type.py
│   ├── nbs_document_version.py
│   ├── nbs_edit_request.py
│   ├── nbs_audit_log.py
│   ├── nbs_notification.py
│   ├── opensearch_service.py
│   └── res_users.py (inherit)
├── controllers/
│   ├── __init__.py
│   ├── document_controller.py
│   ├── search_controller.py
│   └── barcode_controller.py
├── wizards/
│   ├── __init__.py
│   ├── edit_request_wizard.py
│   └── upload_wizard.py
├── views/
│   ├── nbs_menu.xml
│   ├── nbs_document_views.xml
│   ├── nbs_department_views.xml
│   ├── nbs_document_type_views.xml
│   ├── nbs_edit_request_views.xml
│   ├── nbs_audit_log_views.xml
│   ├── nbs_notification_views.xml
│   ├── nbs_dashboard.xml
│   └── nbs_search_view.xml
├── security/
│   ├── nbs_security.xml
│   ├── ir.model.access.csv
│   └── nbs_record_rules.xml
├── data/
│   ├── nbs_department_data.xml
│   ├── nbs_document_type_data.xml
│   └── ir_sequence_data.xml
├── static/
│   ├── src/
│   │   ├── components/
│   │   │   ├── document_viewer/
│   │   │   │   ├── document_viewer.js
│   │   │   │   └── document_viewer.xml
│   │   │   ├── voice_search/
│   │   │   │   ├── voice_search.js
│   │   │   │   └── voice_search.xml
│   │   │   ├── barcode_scanner/
│   │   │   │   ├── barcode_scanner.js
│   │   │   │   └── barcode_scanner.xml
│   │   │   └── notification_center/
│   │   │       ├── notification_center.js
│   │   │       └── notification_center.xml
│   │   ├── css/
│   │   │   ├── nbs_archive.css
│   │   │   └── nbs_rtl.css
│   │   └── js/
│   │       ├── notification_service.js
│   │       └── websocket_client.js
│   └── description/
│       ├── icon.png
│       └── index.html
├── i18n/
│   ├── ar.po
│   └── en_US.po
├── tests/
│   ├── __init__.py
│   ├── test_document_upload.py
│   ├── test_versioning.py
│   ├── test_search.py
│   └── test_permissions.py
├── scripts/
│   ├── backup_nbs.sh
│   ├── restore_nbs.sh
│   └── setup_opensearch.py
├── README.md
├── README_AR.md
└── requirements.txt
```

---

## 14. Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
1. ✅ Module scaffolding
2. ✅ Database models
3. ✅ Basic views (tree/form)
4. ✅ Security groups & rules
5. ✅ Seed data (departments, doc types)

### Phase 2: Document Management (Week 3-4)
1. ✅ Upload wizard & controller
2. ✅ File storage organization
3. ✅ Document locking
4. ✅ Basic viewers
5. ✅ Barcode generation

### Phase 3: OCR & Search (Week 5-6)
1. ✅ Queue job integration
2. ✅ Tesseract OCR pipeline
3. ✅ OpenSearch setup
4. ✅ Indexing service
5. ✅ Search API with highlight
6. ✅ Search UI

### Phase 4: Versioning & Approvals (Week 7-8)
1. ✅ Edit request wizard
2. ✅ Approval workflow
3. ✅ One-time unlock token
4. ✅ Version upload
5. ✅ Version history viewer

### Phase 5: Notifications & Audit (Week 9)
1. ✅ Notification model
2. ✅ Bus integration
3. ✅ Frontend listener
4. ✅ Audit logging middleware
5. ✅ Audit log viewer

### Phase 6: Advanced Features (Week 10-11)
1. ✅ Barcode scanner widget
2. ✅ Voice search widget
3. ✅ Advanced document viewer (PDF.js)
4. ✅ Dashboard with charts
5. ✅ Custom fields rendering

### Phase 7: Bilingual & UX (Week 12)
1. ✅ Arabic translations
2. ✅ RTL styling
3. ✅ Language toggle
4. ✅ UI polish
5. ✅ Mobile responsiveness

### Phase 8: Testing & Deployment (Week 13-14)
1. ✅ Unit tests
2. ✅ Integration tests
3. ✅ Performance optimization
4. ✅ Docker setup
5. ✅ Documentation
6. ✅ Backup/restore scripts

---

## 15. Key Differences from Standalone App

| Aspect | Standalone (Original) | Odoo Module (Adapted) |
|--------|----------------------|----------------------|
| **Backend** | FastAPI (new API) | Odoo Python (leverage existing) |
| **Frontend** | React + Vite | Odoo Web (Owl + QWeb) |
| **Auth** | Custom JWT | Odoo's built-in + custom rules |
| **ORM** | SQLAlchemy | Odoo ORM (simpler, integrated) |
| **Migrations** | Alembic | Odoo auto-migration |
| **Admin UI** | Build from scratch | Odoo admin built-in |
| **User Management** | Custom | Odoo `res.users` |
| **API** | RESTful (pure) | RPC + custom REST endpoints |
| **Deployment** | Separate containers | Single Odoo instance + services |
| **Development** | Separate repos | Single module |

---

## 16. Critical Constraints Compliance

✅ **NO DELETE RULE**: 
- No `unlink()` methods exposed to users
- SQL constraint on versions
- Application-level guards in controllers
- Archive/disable instead of delete

✅ **Department Isolation**:
- Odoo record rules enforce per-department access
- Confidentiality levels via computed access

✅ **Locking & Versioning**:
- Document locked by default
- Edit requires approval workflow
- One-time token mechanism

✅ **OCR & Search**:
- Background OCR via queue_job
- OpenSearch external service
- Highlight + fuzzy search
- Arabic + English support

✅ **Bilingual**:
- Translation files (ar.po, en_US.po)
- RTL CSS
- User language preference

✅ **Audit Everything**:
- Audit log model
- Middleware logging
- View/download/edit tracking

✅ **API-ready**:
- Odoo RPC inherently API-ready
- Custom REST endpoints for mobile/external
- WhatsApp integration prepared (stubs)

---

## 17. Next Steps

**User Decision Required**: 
Should we proceed with:
- **Option A**: Build as Odoo module (this plan)
- **Option B**: Build standalone FastAPI/React (original spec)

If **Option A** (Odoo module), I will start generating code files.

If **Option B**, I will follow the original architecture plan.

**Please confirm which approach you prefer before I begin implementation.**

---

## 18. Estimated Effort

- **Odoo Module Approach**: ~10-14 weeks (leveraging Odoo framework)
- **Standalone Approach**: ~16-20 weeks (building everything from scratch)

**Recommendation**: Odoo module is faster, more maintainable, and provides better integration with existing ERP features if NBS uses Odoo.

---

**END OF PLAN**










