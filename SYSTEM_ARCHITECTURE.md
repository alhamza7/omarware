# Lugal NBS ERP - System Architecture
## البنية المعمارية الكاملة لنظام Lugal NBS

---

## 📊 Overview - نظرة عامة

```
Lugal NBS ERP System
├── Odoo 17.0 Core (Python/PostgreSQL)
├── Custom Modules (12 modules)
├── SAP Integration Layer
├── External Integrations (WhatsApp, OpenSearch)
└── Web Interface (JavaScript/OWL)
```

**Version:** 17.0  
**Database:** PostgreSQL 14+  
**Backend:** Python 3.12  
**Frontend:** JavaScript (OWL Framework)  
**Server:** Ubuntu Linux 22.04+

---

## 🏗️ System Layers - طبقات النظام

```
┌─────────────────────────────────────────────────────────┐
│                     Presentation Layer                   │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────┐   │
│  │  Web UI   │  │ POS UI    │  │  Mobile App      │   │
│  │ (Browser) │  │(Perfume)  │  │  (Odoo Mobile)   │   │
│  └───────────┘  └───────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  ┌────────────────────────────────────────────────┐    │
│  │              Odoo Framework (Core)              │    │
│  │  • ORM (Models)                                 │    │
│  │  • Business Logic                               │    │
│  │  • Workflow Engine                              │    │
│  │  • Report Engine                                │    │
│  │  • Security & Access Control                    │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   Integration Layer                      │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ SAP B1 API  │  │ WhatsApp │  │ OpenSearch API   │  │
│  │  (REST)     │  │(UltraMsg)│  │  (Archive)       │  │
│  └─────────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│  ┌────────────────┐  ┌─────────────────────────────┐   │
│  │  PostgreSQL    │  │  File Storage (FileStore)   │   │
│  │  (Database)    │  │  /var/lib/odoo/filestore    │   │
│  └────────────────┘  └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Modules Structure - بنية الوحدات

### Core Odoo Modules (Built-in)
```
addons/
├── base/                    # Core module (users, companies, currencies)
├── web/                     # Web interface framework
├── mail/                    # Messaging & communication
├── account/                 # Accounting & invoicing
├── sale/                    # Sales management
├── purchase/                # Purchase management
├── stock/                   # Inventory & warehouse
├── product/                 # Product management
├── point_of_sale/          # POS framework
└── uom/                     # Units of measure
```

### Custom Modules (Lugal NBS)
```
addons/
├── sap_integration/               # SAP Business One Integration
│   ├── models/
│   │   ├── sap_backend.py        # SAP connection config
│   │   ├── sap_product.py        # Product sync
│   │   ├── sap_partner.py        # Customer sync
│   │   ├── sap_sale_order.py     # Order export
│   │   └── sap_stock.py          # Stock sync
│   ├── components/
│   │   ├── adapter.py            # SAP API wrapper
│   │   ├── binder.py             # Odoo↔SAP binding
│   │   ├── exporter.py           # Export to SAP
│   │   ├── importer.py           # Import from SAP
│   │   ├── listener.py           # Event listener
│   │   └── mapper.py             # Data transformation
│   └── security/
│       └── ir.model.access.csv
│
├── pos_perfume_custom/            # Custom POS for Perfume Shop
│   ├── models/
│   │   ├── pos_perfume_order.py  # Order management
│   │   ├── product_product.py    # Extended product
│   │   └── res_config_settings.py # Settings
│   ├── static/src/
│   │   ├── app/
│   │   │   ├── pos_perfume_screen.js  # Main interface
│   │   │   ├── customer_search.js     # Customer widget
│   │   │   ├── product_search_uom.js  # Product search
│   │   │   └── location_selector.js   # Warehouse selector
│   │   ├── xml/
│   │   │   └── pos_perfume_screen.xml
│   │   └── scss/
│   │       └── perfume_pos.scss
│   ├── controllers/
│   │   ├── pos_perfume_controller.py
│   │   └── pos_perfume_whatsapp_image.py
│   ├── reports/
│   │   └── pos_perfume_order_report.xml
│   └── data/
│       └── default_exchange_rate.xml  # Exchange rate config
│
├── nbs_archive/                   # Document Archive System ★ v1.1.0
│   ├── models/
│   │   ├── nbs_department.py          # Departments
│   │   ├── nbs_document_type.py       # Document types
│   │   ├── nbs_document.py            # Documents (with soft delete)
│   │   ├── nbs_document_relation.py   # Relations & Attachments (with soft delete)
│   │   ├── nbs_document_version.py    # Version control
│   │   ├── nbs_document_tag.py        # Tags
│   │   ├── nbs_folder.py              # Folder hierarchy
│   │   ├── nbs_bulk_upload.py         # Bulk upload jobs ★ NEW
│   │   ├── nbs_workflow.py            # Workflow management
│   │   ├── nbs_edit_request.py        # Edit requests
│   │   ├── nbs_signature_request.py   # Digital signatures
│   │   ├── nbs_audit_log.py           # Audit trail
│   │   ├── nbs_notification.py        # Notifications
│   │   ├── opensearch_service.py      # OpenSearch integration
│   │   └── res_users.py               # User extensions
│   ├── controllers/
│   │   ├── auth_controller.py              # JWT authentication
│   │   ├── document_controller.py          # Document CRUD + Soft Delete ★
│   │   ├── attachments_controller.py       # Attachment CRUD + Edit/Delete ★
│   │   ├── bulk_upload_controller.py       # Bulk upload APIs ★ NEW
│   │   ├── department_management_controller.py  # Dept/Type CRUD ★
│   │   ├── search_controller.py            # Advanced search
│   │   ├── workflow_controller.py          # Workflow management
│   │   ├── admin_controller.py             # Admin operations
│   │   ├── permissions_controller.py       # Permissions
│   │   ├── signature_controller.py         # Signatures
│   │   ├── relations_controller.py         # Document relations
│   │   ├── edit_request_controller.py      # Edit requests
│   │   ├── notification_controller.py      # Notifications
│   │   ├── document_hierarchy_controller.py # Folder hierarchy
│   │   ├── websocket_controller.py         # Real-time updates
│   │   └── ocr_controller.py               # OCR processing
│   ├── data/
│   │   ├── nbs_department_data.xml
│   │   ├── nbs_document_type_data.xml
│   │   └── nbs_security_groups.xml
│   ├── security/
│   │   ├── nbs_security.xml
│   │   ├── nbs_record_rules.xml
│   │   └── ir.model.access.csv
│   └── static/
│       └── description/
│           ├── icon.png
│           └── index.html
│
├── product_label_designer/        # Barcode Label Designer
│   ├── models/
│   │   └── customer_label.py
│   ├── wizard/
│   │   └── print_customer_label_wizard.py
│   └── reports/
│       └── customer_label_report.xml
│
├── invoice_designer/              # Custom Invoice Designer
│   ├── models/
│   │   ├── sale_order.py
│   │   └── invoice_template.py
│   └── reports/
│       └── invoice_report.xml
│
├── lugal_fragrantica/             # Fragrantica Integration
│   ├── models/
│   │   ├── fragrantica_scraper.py
│   │   └── res_config_settings.py
│   └── data/
│       └── ir_cron_data.xml
│
└── ultramsg_integration/          # WhatsApp Integration
    ├── models/
    │   ├── ultramsg_config.py
    │   └── ultramsg_message.py
    └── controllers/
        └── ultramsg_webhook.py
```

---

## 🔄 Data Flow - تدفق البيانات

### 1. SAP → Odoo (Product Sync)
```
┌──────────────┐
│  SAP B1      │
│  (Products)  │
└──────┬───────┘
       │ REST API
       ↓
┌──────────────────────┐
│ SAP Integration      │
│ ├── Adapter          │ Fetch products
│ ├── Mapper          │ Transform data
│ └── Importer        │ Create/Update
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ Odoo Database        │
│ ├── product.product  │
│ ├── product.template │
│ └── sap.product      │ (binding)
└──────────────────────┘
```

### 2. Odoo → SAP (Order Export)
```
┌──────────────────────┐
│ POS Perfume Order    │
│ (User creates order) │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ Sale Order           │
│ (Converted to SO)    │
└──────┬───────────────┘
       │ Event: order_confirmed
       ↓
┌──────────────────────┐
│ SAP Integration      │
│ ├── Listener         │ Detect event
│ ├── Exporter         │ Prepare data
│ └── Adapter          │ Send to SAP
└──────┬───────────────┘
       │ REST API
       ↓
┌──────────────┐
│  SAP B1      │
│ (Sale Order) │
└──────────────┘
```

### 3. POS Perfume Workflow
```
┌─────────────┐
│   User      │
│ (Cashier)   │
└──────┬──────┘
       │ Opens POS Perfume
       ↓
┌─────────────────────────────┐
│ Load Products from DB       │
│ ├── product.product         │
│ ├── stock.warehouse         │
│ └── res.partner (customers) │
└──────┬──────────────────────┘
       │ Search & Select
       ↓
┌─────────────────────────────┐
│ Create Order                │
│ ├── pos.perfume.order       │
│ └── pos.perfume.order.line  │
└──────┬──────────────────────┘
       │ Confirm Order
       ↓
┌─────────────────────────────┐
│ Generate Reports            │
│ ├── PDF Invoice             │
│ ├── WhatsApp Message        │
│ └── Export to SAP (optional)│
└─────────────────────────────┘
```

### 4. NBS Archive Workflow ★ (Document Lifecycle)
```
┌─────────────────────┐
│   User (Employee)   │
│  via API/Frontend   │
└──────┬──────────────┘
       │ Upload Document
       ↓
┌──────────────────────────────────┐
│ Create Document (draft)          │
│ ├── nbs_document                 │
│ ├── nbs_document_attachment      │
│ └── Audit Log: document_created  │
└──────┬───────────────────────────┘
       │ Activate
       ↓
┌──────────────────────────────────┐
│ Active Document                  │
│ ├── Edit/Update Allowed          │
│ ├── Add Multiple Attachments ★   │
│ ├── Edit Attachments ★           │
│ └── Version Control               │
└──────┬───────────────────────────┘
       │ Soft Delete
       ↓
┌──────────────────────────────────┐
│ Trash (30 days)                  │
│ ├── is_deleted = true ★          │
│ ├── restore_deadline set ★       │
│ ├── Can be Restored ★            │
│ └── Audit: document_soft_deleted │
└──────┬───────────────────────────┘
       │
       ├──→ Restore ──────┐
       │                  │
       ↓                  ↓
┌──────────────────┐  Back to Active
│ Permanent Delete │
│ (Admin Only) ★   │
└──────────────────┘
```

### 5. Bulk Upload Workflow ★ (Week 1 Feature)
```
┌─────────────────────────┐
│   User (API Client)     │
│ Needs to upload 100 docs│
└──────┬──────────────────┘
       │ POST /api/documents/bulk-upload/start
       ↓
┌──────────────────────────────────────┐
│ Create Bulk Upload Job               │
│ ├── nbs_bulk_upload_job             │
│ ├── job_id: UUID                     │
│ ├── status: pending                  │
│ └── department_id, document_type_id  │
└──────┬───────────────────────────────┘
       │ Returns job_id
       ↓
┌──────────────────────────────────────┐
│ Upload Files (100 files)             │
│ POST /bulk-upload/<job_id>/upload   │
│ ├── files: [file1, file2, ...]      │
│ └── Base64 encoded data              │
└──────┬───────────────────────────────┘
       │ Process files one by one
       ↓
┌──────────────────────────────────────┐
│ Processing Loop                      │
│ For each file:                       │
│ ├── Create nbs_document              │
│ ├── Create nbs_document_attachment   │
│ ├── Update progress (commit)         │
│ ├── processed_files++                │
│ └── Log errors if any                │
└──────┬───────────────────────────────┘
       │ Real-time Progress Tracking
       ↓
┌──────────────────────────────────────┐
│ GET /bulk-upload/<job_id>/progress  │
│ Returns:                             │
│ ├── status: processing               │
│ ├── progress_percentage: 45%         │
│ ├── successful_files: 43/100         │
│ ├── failed_files: 2                  │
│ └── error_log: "File 12: Invalid..." │
└──────┬───────────────────────────────┘
       │ All files processed
       ↓
┌──────────────────────────────────────┐
│ Job Complete                         │
│ ├── status: completed/partial        │
│ ├── total_files: 100                 │
│ ├── successful_files: 98             │
│ ├── failed_files: 2                  │
│ └── created_document_ids: [1,2,...]  │
└──────────────────────────────────────┘
```

---

## 🗄️ Database Schema - هيكل قاعدة البيانات

### Core Tables
```sql
-- Users & Access
├── res_users              # Users
├── res_groups             # User groups
├── res_partner            # Customers/Suppliers
└── res_company            # Companies

-- Products
├── product_product        # Product variants
├── product_template       # Product templates
├── product_category       # Categories
└── uom_uom                # Units of measure

-- Sales
├── sale_order             # Sale orders
├── sale_order_line        # Order lines
└── account_move           # Invoices

-- Inventory
├── stock_warehouse        # Warehouses
├── stock_location         # Stock locations
├── stock_quant            # Stock quantities
└── stock_move             # Stock movements

-- Currencies
├── res_currency           # Currencies (USD, IQD)
└── res_currency_rate      # Exchange rates
```

### Custom Tables (SAP Integration)
```sql
-- SAP Configuration
├── sap_backend                    # SAP connection config
├── sap_backend_auto_sync         # Auto-sync settings

-- SAP Bindings (Odoo ↔ SAP mapping)
├── sap_product_product           # Product bindings
├── sap_res_partner               # Customer bindings
├── sap_sale_order                # Order bindings
└── sap_stock_warehouse           # Warehouse bindings

-- SAP Data Cache
├── sap_product_extended          # Extended product info
└── sap_stock_info                # Stock information
```

### Custom Tables (NBS Archive System) ★ v1.1.0
```sql
-- Core Archive Tables
├── nbs_department                     # Departments/divisions
├── nbs_document_type                  # Document types/categories
├── nbs_folder                         # Folder hierarchy
├── nbs_document                       # Main documents table
│   ├── state: draft/active/archived/trash  # Document lifecycle
│   ├── is_deleted: Boolean            # Soft delete flag ★
│   ├── deleted_at: DateTime           # Deletion timestamp ★
│   ├── restore_deadline: DateTime     # 30-day restore window ★
│   └── state_before_trash: Char       # Original state ★

-- Document Relations
├── nbs_document_relation              # Document relationships
├── nbs_document_attachment            # File attachments
│   ├── file_data: Binary              # Actual file (in filestore)
│   ├── is_deleted: Boolean            # Soft delete flag ★
│   ├── deleted_at: DateTime           # Deletion timestamp ★
│   └── restore_deadline: DateTime     # 30-day restore window ★
├── nbs_document_version               # Version history
└── nbs_document_tag                   # Tags/labels

-- Workflow & Permissions
├── nbs_workflow                       # Workflow definitions
├── nbs_edit_request                   # Document edit requests
├── nbs_signature_request              # Digital signature requests
└── res_groups (extended)              # Access groups
    ├── group_nbs_user                 # Basic user
    ├── group_nbs_manager              # Manager
    └── group_nbs_admin                # Administrator

-- Bulk Operations ★ NEW (Week 1 Implementation)
├── nbs_bulk_upload_job                # Bulk upload tracking
│   ├── job_id: UUID                   # Unique job identifier
│   ├── status: pending/processing/completed/failed/partial
│   ├── total_files: Integer           # Total files to upload
│   ├── processed_files: Integer       # Files processed
│   ├── successful_files: Integer      # Successfully uploaded
│   ├── failed_files: Integer          # Failed uploads
│   ├── progress_percentage: Float     # Computed progress
│   └── error_log: Text                # Error details
└── bulk_upload_document_rel           # Job ↔ Document mapping

-- Audit & Notifications
├── nbs_audit_log                      # Complete audit trail
│   ├── action: attachment_updated, attachment_deleted, ★
│   │          document_soft_deleted, document_restored, ★
│   │          multiple_attachments_upload, etc. ★
│   ├── user_id: Many2one              # Who performed action
│   ├── document_id: Many2one          # Related document
│   ├── metadata: Text                 # Additional details
│   └── ip_address: Char               # User IP
└── nbs_notification                   # User notifications
```

### Custom Tables (POS Perfume)
```sql
-- POS Orders
├── pos_perfume_order             # Orders
├── pos_perfume_order_line        # Order lines
└── pos_perfume_session           # POS sessions

-- Configuration
└── ir_config_parameter
    └── pos_perfume.default_exchange_rate_usd_iqd
```

### Custom Tables (Archive System)
```sql
-- Archive Management
├── nbs_department                # Departments
├── nbs_document_type             # Document types
├── nbs_document                  # Documents
├── nbs_document_version          # Document versions
└── nbs_audit_log                 # Audit trail
```

---

## 🌐 API Endpoints - نقاط الوصول للـ API

### NBS Archive REST APIs ★ v1.1.0

#### Document Management
```http
# List documents (with filters)
POST /api/documents
Body: { department_id, document_type_id, status, search, page, per_page }

# Get document by ID
POST /api/documents/<id>

# Create document
POST /api/documents/create
Body: { name, department_id, document_type_id, description, ... }

# Update document
POST /api/documents/<id>/update

# ★ Soft Delete - Move to trash (30 days)
POST /api/documents/<id>/trash
Body: { reason: "optional deletion reason" }

# ★ Restore from trash
POST /api/documents/<id>/restore

# ★ Permanent delete (Admin only, requires confirmation)
DELETE /api/documents/<id>/permanent?confirmation=DELETE_PERMANENT

# ★ List trash
POST /api/documents/trash
```

#### Attachment Management ★ (Week 1)
```http
# List attachments
POST /api/documents/<document_id>/attachments

# Add single attachment
POST /api/documents/<document_id>/add-attachment
Body: { name, file_name, file_data, description }

# ★ Add multiple attachments at once (NEW)
POST /api/documents/<document_id>/attachments/multiple
Body: { 
    attachments: [
        { name, file_name, file_data, description },
        { name, file_name, file_data, description },
        ...
    ]
}

# ★ Update/Edit attachment (NEW)
POST /api/documents/<document_id>/attachments/<attachment_id>/update
Body: { name, description, file_data, file_name }

# ★ Soft delete attachment (NEW)
DELETE /api/documents/<document_id>/attachments/<attachment_id>

# ★ Restore attachment (NEW)
POST /api/documents/<document_id>/attachments/<attachment_id>/restore

# ★ Permanent delete (Admin only, NEW)
DELETE /api/documents/<document_id>/attachments/<attachment_id>/permanent

# Download attachment
GET /api/documents/<document_id>/attachments/<attachment_id>/download
```

#### Bulk Upload ★ (Week 1 - NEW Feature)
```http
# Step 1: Start bulk upload job
POST /api/documents/bulk-upload/start
Body: { department_id, document_type_id, folder_id, confidentiality_level }
Returns: { job_id, id }

# Step 2: Upload files
POST /api/documents/bulk-upload/<job_id>/upload
Body: { 
    files: [
        { file_name, file_data, name, description },
        ...
    ]
}

# Step 3: Track progress (Real-time)
POST /api/documents/bulk-upload/<job_id>/progress
Returns: { 
    status, 
    progress_percentage, 
    processed_files, 
    successful_files,
    failed_files,
    error_log 
}

# Cancel job
POST /api/documents/bulk-upload/<job_id>/cancel

# List jobs
POST /api/documents/bulk-upload/jobs
Body: { status, limit, offset }
```

#### Department & Document Type Management ★ (NEW)
```http
# Departments
POST /api/departments/create
POST /api/departments
POST /api/departments/<id>
POST /api/departments/<id>/update
DELETE /api/departments/<id>

# Document Types
POST /api/document-types/create
POST /api/document-types
POST /api/document-types/<id>
POST /api/document-types/<id>/update
DELETE /api/document-types/<id>
```

### Authentication
```http
# JWT Login
POST /api/auth/login
Body: { username, password }
Returns: { token, user_id }

# All requests require JWT token in header
Authorization: Bearer <token>
```

---

## 🔌 External Integrations - التكاملات الخارجية

### 1. SAP Business One Integration
```yaml
Type: REST API Integration
Protocol: HTTPS
Authentication: Service Layer Token
Endpoints:
  - /Items                    # Products
  - /BusinessPartners         # Customers
  - /Orders                   # Sale Orders
  - /Warehouses              # Stock locations
  - /StockTransfers          # Stock movements

Sync Methods:
  - Real-time: On event (order confirm)
  - Scheduled: Cron jobs (products, stock)
  - Manual: Full sync button

Configuration:
  Location: Settings → SAP Integration → Backends
  Fields:
    - Host: SAP server URL
    - Port: 50000 (default)
    - Database: Company DB name
    - Username: SAP user
    - Password: SAP password
```

### 2. WhatsApp Integration (UltraMsg)
```yaml
Type: REST API
Provider: UltraMsg.com
Authentication: API Token

Features:
  - Send invoice via WhatsApp
  - Send order confirmation
  - Attach PDF invoices
  - Send images with orders

Configuration:
  Location: Settings → UltraMsg Integration
  Fields:
    - Instance ID
    - API Token
    - Default Phone Number

Usage:
  - From POS Perfume: "Send WhatsApp" button
  - From Sale Order: "Send via WhatsApp" action
```

### 3. OpenSearch Integration (Archive)
```yaml
Type: Full-text Search Engine
Use Case: Document archive search
Features:
  - Arabic + English OCR
  - Full-text search
  - Advanced filters
  - Audit logging

Configuration:
  Location: NBS Archive settings
  Dependencies:
    - opensearch-py (Python library)
    - PyJWT (Authentication)

Status: Configured but optional
```

---

## 💱 Currency & Exchange Rate System

### Currency Configuration
```yaml
Base Currency: IQD (Iraqi Dinar)
Foreign Currency: USD (US Dollar)

Exchange Rate Storage:
  - Table: res_currency_rate
  - Field: rate (inverse: 1/actual_rate)
  - Example: 1 USD = 1510 IQD
    → Stored as: rate = 0.00066225

POS Perfume Specific:
  - Separate config: ir_config_parameter
  - Key: pos_perfume.default_exchange_rate_usd_iqd
  - Value: 1510.0 (direct value)
  
Update Methods:
  1. Manual: Settings → Currencies → USD → Rates
  2. Script: update_exchange_rate.py 1510
  3. SQL: UPDATE ir_config_parameter SET value='1510.0'
```

### Exchange Rate Application
```
┌─────────────────────────────────────────────────────┐
│ Module          │ Rate Source         │ Applied     │
├─────────────────┼─────────────────────┼─────────────┤
│ Sale Order      │ res_currency_rate   │ On date     │
│ Invoice         │ res_currency_rate   │ On date     │
│ POS (Standard)  │ res_currency_rate   │ On session  │
│ POS Perfume     │ ir_config_parameter │ Real-time   │
└─────────────────────────────────────────────────────┘
```

---

## 🔐 Security Architecture

### Access Control Layers
```
1. Module Level
   ├── ir.model.access.csv    # Model permissions
   └── security.xml           # Groups & rules

2. Record Level
   ├── Record Rules           # Row-level security
   └── Multi-company rules    # Company isolation

3. Field Level
   ├── groups attribute       # Field visibility
   └── readonly conditions    # Edit restrictions

4. API Level
   ├── @api.constrains        # Validation
   └── @api.ondelete         # Deletion rules
```

### User Groups (Key)
```
Base Groups:
├── Internal User              # Basic Odoo access
├── Portal User                # Limited external access
└── Public User                # No login required

Sales Groups:
├── Sales User                 # Read sales
├── Sales Team Leader          # Manage team
└── Sales Manager              # Full sales access

Inventory Groups:
├── Inventory User             # Stock operations
└── Inventory Manager          # Full inventory control

Custom Groups:
├── POS Perfume User           # POS access
├── POS Perfume Manager        # POS management
├── SAP Integration User       # SAP sync
├── SAP Integration Manager    # SAP configuration
├── NBS Archive User           # Archive read
├── NBS Archive Manager        # Archive manage
└── NBS Archive Admin          # Full archive control
```

---

## 🚀 Deployment Architecture

### Production Setup
```
┌─────────────────────────────────────────────────┐
│              Load Balancer (Nginx)              │
│              Port 80 → 8069                     │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│           Odoo Application Server               │
│  ┌──────────────────────────────────────┐      │
│  │  Odoo Instance (Python)              │      │
│  │  Port: 8069                          │      │
│  │  Workers: 4-8 (multiprocessing)      │      │
│  │  Config: odoo.conf                   │      │
│  └──────────────────────────────────────┘      │
└────────────────────┬────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│            PostgreSQL Database                  │
│  Port: 5432                                     │
│  Database: nbs_lugalai                          │
│  User: odoo                                     │
└─────────────────────────────────────────────────┘
```

### File Structure (Server)
```
/home/lugalai/Lugal-ai/
├── odoo-bin                    # Main executable
├── odoo.conf                   # Configuration
├── addons/                     # Custom modules
├── venv/                       # Python virtual environment
├── requirements.txt            # Python dependencies
└── odoo.log                    # Application logs

/var/lib/odoo/
└── filestore/
    └── nbs_lugalai/           # Uploaded files
        ├── 00/ → ff/          # File storage (by hash)
        └── nbs_archive/       # Archive documents
```

### Configuration (odoo.conf)
```ini
[options]
addons_path = /home/lugalai/Lugal-ai/addons
data_dir = /var/lib/odoo
db_host = localhost
db_port = 5432
db_user = odoo
db_password = ********
db_name = nbs_lugalai
xmlrpc_port = 8069
workers = 4
max_cron_threads = 2
limit_time_cpu = 600
limit_time_real = 1200
```

---

## 📊 Performance Optimization

### Database
```sql
-- Indexes for performance
CREATE INDEX idx_product_default_code ON product_product(default_code);
CREATE INDEX idx_sap_product_external ON sap_product_product(external_id);
CREATE INDEX idx_sale_order_date ON sale_order(date_order);
CREATE INDEX idx_stock_quant_location ON stock_quant(location_id, product_id);
```

### Caching
```yaml
Session Cache:
  - Type: Redis (optional) or Memory
  - TTL: 3600 seconds
  
Asset Cache:
  - Static files: /web/static/
  - Bundled JS/CSS
  - Browser cache: 7 days

ORM Cache:
  - Record cache per transaction
  - Invalidated on write
  - Field-level caching
```

### Cron Jobs (Scheduled Tasks)
```python
# SAP Product Sync
Schedule: Every 30 minutes
Model: sap.backend
Method: cron_sync_products()

# SAP Stock Sync  
Schedule: Every 15 minutes
Model: sap.backend
Method: cron_sync_stock()

# Fragrantica Scraper
Schedule: Daily at 2:00 AM
Model: fragrantica.scraper
Method: cron_auto_scrape()

# Archive Cleanup
Schedule: Weekly (Sunday 3:00 AM)
Model: nbs.document
Method: cron_cleanup_old_versions()
```

---

## 🛠️ Development Tools & Scripts

### Management Scripts
```bash
# Exchange Rate Management
update_exchange_rate.py [rate]          # Update system rate
activate_currency_menu.py               # Enable currency menu
update_pos_perfume_rate.py             # Update POS Perfume rate
change_current_rate_to_1510.py         # Direct rate update
update_pos_perfume_db_direct.sh        # SQL update for POS

# System Maintenance
clear_cache_from_db.py                 # Clear all caches
fix_pos_exchange_rate.py               # Fix POS rate issues
check_pos_perfume_rate.sh              # Verify POS rate

# SAP Integration
sync_sap_products_now.sh               # Manual SAP sync
check_sap_connection.py                # Test SAP connection

# Module Management
quick_update_lugal_nbs.sh              # Quick module update
setup_lugal_nbs.sh                     # Initial setup

# Database Operations
fix_filestore_permissions.sh           # Fix file permissions
fix_uom_complete.sh                    # Fix UoM errors
```

### Testing & Debugging
```python
# Odoo Shell (Interactive)
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai

# Example commands in shell:
env['res.partner'].search([])          # List partners
env['product.product'].browse(123)     # Get product by ID
env['sale.order'].search_count([])     # Count orders

# Check logs
tail -f odoo.log                       # Real-time logs
grep -i error odoo.log                 # Find errors
```

---

## 📈 Monitoring & Metrics

### Key Performance Indicators
```yaml
System Health:
  - CPU Usage: < 70%
  - Memory Usage: < 80%
  - Database Size: Monitor growth
  - Response Time: < 2 seconds

Business Metrics:
  - Daily Orders: POS Perfume
  - SAP Sync Success Rate: > 95%
  - Stock Accuracy: > 98%
  - Document Archive Size: GB/month

Error Tracking:
  - SAP Connection Failures
  - Database Deadlocks
  - Missing Product Bindings
  - Exchange Rate Mismatches
```

### Log Locations
```
Application Logs:
  /home/lugalai/Lugal-ai/odoo.log

PostgreSQL Logs:
  /var/log/postgresql/postgresql-14-main.log

Nginx Logs:
  /var/log/nginx/access.log
  /var/log/nginx/error.log

System Logs:
  /var/log/syslog
```

---

## 🔄 Backup & Recovery

### Backup Strategy
```yaml
Database Backup:
  Frequency: Daily at 2:00 AM
  Method: pg_dump
  Location: /backup/postgres/
  Retention: 30 days
  Command: |
    pg_dump nbs_lugalai > backup_$(date +%Y%m%d).sql

Filestore Backup:
  Frequency: Daily at 3:00 AM
  Method: rsync
  Location: /backup/filestore/
  Retention: 30 days
  Command: |
    rsync -av /var/lib/odoo/filestore/ /backup/filestore/

Module Backup:
  Frequency: Before updates
  Method: Git commit
  Location: GitHub repository
```

### Recovery Procedures
```bash
# Database Restore
psql -U odoo -d nbs_lugalai < backup_20260129.sql

# Filestore Restore
rsync -av /backup/filestore/ /var/lib/odoo/filestore/

# Module Rollback
git checkout <commit-hash>
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u all --stop-after-init
```

---

## 📝 API Endpoints

### REST API (Odoo)
```
Base URL: http://192.168.116.211:8069

Authentication:
  POST /web/session/authenticate
  Body: {
    "jsonrpc": "2.0",
    "params": {
      "db": "nbs_lugalai",
      "login": "admin",
      "password": "password"
    }
  }

CRUD Operations:
  POST /web/dataset/call_kw/[model]/search_read
  POST /web/dataset/call_kw/[model]/create
  POST /web/dataset/call_kw/[model]/write
  POST /web/dataset/call_kw/[model]/unlink

Custom Endpoints:
  POST /pos_perfume/create_order
  POST /pos_perfume/send_whatsapp
  GET  /pos_perfume/get_products
```

### SAP B1 API (External)
```
Base URL: https://sap-server:50000/b1s/v1

Authentication:
  POST /Login
  Body: {
    "CompanyDB": "SBODemoUS",
    "UserName": "manager",
    "Password": "password"
  }

Endpoints Used:
  GET  /Items                  # Products
  GET  /BusinessPartners       # Customers
  POST /Orders                 # Create order
  GET  /Warehouses            # Stock locations
```

---

## 🌐 Network Architecture

```
Internet
    ↓
┌─────────────────────────────┐
│   Firewall / Router         │
│   Port Forwarding:          │
│   80 → 192.168.116.211:80   │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│   Internal Network          │
│   192.168.116.0/24          │
│                             │
│   ┌──────────────────────┐  │
│   │  Odoo Server         │  │
│   │  192.168.116.211     │  │
│   │  Port: 8069          │  │
│   └──────────────────────┘  │
│                             │
│   ┌──────────────────────┐  │
│   │  SAP Server          │  │
│   │  192.168.116.xxx     │  │
│   │  Port: 50000         │  │
│   └──────────────────────┘  │
│                             │
│   ┌──────────────────────┐  │
│   │  Client Workstations │  │
│   │  192.168.116.xxx     │  │
│   └──────────────────────┘  │
└─────────────────────────────┘
```

---

## 🎯 Future Enhancements

### Planned Features
```yaml
Phase 1 (Q1 2026):
  - [ ] Advanced reporting dashboard
  - [ ] Multi-warehouse optimization
  - [ ] Mobile app improvements
  - [ ] Enhanced SAP sync logs

Phase 2 (Q2 2026):
  - [ ] AI-powered product recommendations
  - [ ] Automated reordering
  - [ ] Customer loyalty program
  - [ ] Advanced analytics

Phase 3 (Q3 2026):
  - [ ] E-commerce integration
  - [ ] Payment gateway integration
  - [ ] Advanced inventory forecasting
  - [ ] Multi-language support
```

---

## 📞 Support & Maintenance

### System Administrator Contacts
```
Technical Support: IT Team
Database Admin: DBA Team
SAP Integration: SAP Team
Network Admin: Network Team
```

### Regular Maintenance Tasks
```yaml
Daily:
  - Check system logs for errors
  - Verify SAP sync status
  - Monitor disk space
  - Review failed cron jobs

Weekly:
  - Database vacuum and analyze
  - Clear old sessions
  - Review access logs
  - Update exchange rates

Monthly:
  - Module updates (if available)
  - Security patches
  - Performance review
  - Backup verification
```

---

## 📚 Documentation Index

### User Guides
- `README.md` - Main documentation
- `QUICK_START_GUIDE.md` - Getting started
- `FIX_*_AR.md` - Arabic troubleshooting guides

### Technical Documentation
- `SYSTEM_ARCHITECTURE.md` - This file
- Module-specific README files in each addon
- API documentation in controllers

### Operational Guides
- Exchange rate update guides
- SAP integration guides
- Backup and recovery procedures
- Troubleshooting guides

---

## 📊 Technology Stack Summary

```yaml
Backend:
  - Framework: Odoo 17.0
  - Language: Python 3.12
  - Database: PostgreSQL 14+
  - ORM: Odoo ORM
  - Web Server: Werkzeug (development) / Gunicorn (production)

Frontend:
  - Framework: OWL (Odoo Web Library)
  - JavaScript: ES6+
  - CSS: SCSS/SASS
  - UI: Bootstrap 5

Integrations:
  - SAP B1: REST API
  - WhatsApp: UltraMsg API
  - Search: OpenSearch
  - Payment: (Future)

Infrastructure:
  - OS: Ubuntu 22.04 LTS
  - Web Server: Nginx
  - Reverse Proxy: Nginx
  - SSL: Let's Encrypt (optional)
  - Backup: pg_dump + rsync

Development:
  - Version Control: Git
  - Repository: GitHub
  - IDE: Cursor / VS Code
  - Testing: Odoo Test Framework
```

---

**Last Updated:** February 7, 2026  
**Version:** 1.1 (NBS Archive v1.1.0 - Week 1 Implementation Complete ★)  
**Maintained By:** Lugal-AI Development Team

---

## 📋 Recent Updates

### v1.1.0 - NBS Archive Week 1 Implementation (Feb 7, 2026) ★

**New Features:**
- ✅ Soft Delete system for Documents & Attachments (30-day trash)
- ✅ Edit/Update Attachments (name, description, file replacement)
- ✅ Bulk Upload with real-time progress tracking
- ✅ Multiple Attachments upload (single API call)
- ✅ Department & Document Type CRUD APIs
- ✅ Enhanced Audit Logging (8 new action types)
- ✅ Trash management (List, Restore, Permanent Delete)

**New Models:**
- `nbs_bulk_upload_job` - Track bulk upload operations

**New API Endpoints:** 14 endpoints
- 4 Soft Delete APIs (trash, restore, permanent delete, list trash)
- 4 Attachment management APIs (update, delete, restore, permanent delete)
- 5 Bulk upload APIs (start, upload, progress, cancel, list)
- 1 Multiple attachments upload API

**Documentation:**
- `NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md` - Full documentation
- `NBS_ARCHIVE_QUICK_TEST_GUIDE.md` - Testing guide
- `NBS_DEPARTMENT_DOCTYPE_MANAGEMENT.md` - Management guide

---

For detailed information about specific modules or features, refer to the README files in each module directory.
