# 📋 خطة تطوير شاملة - NBS Archive System

## 🎯 الهدف

تطوير نظام NBS Archive ليصبح نظام أرشفة متكامل وعالمي المستوى مع:
- إمكانيات تعديل/حذف متقدمة
- رفع ملفات متعددة (Bulk Upload)
- نظام صلاحيات متطور
- سلة المحذوفات (Trash/Recycle Bin)
- تحسينات في الأداء والأمان

---

## 📊 تحليل الوضع الحالي

### ✅ **ما يعمل حالياً:**

```
✅ رفع مستند واحد
✅ عرض المستندات
✅ البحث الأساسي
✅ إضافة مرفقات
✅ Versioning (إصدارات)
✅ Edit Requests (طلبات تعديل)
✅ Workflow (سير عمل الموافقات)
✅ Audit Log (سجل التدقيق)
✅ JWT Authentication
✅ صلاحيات أساسية (3 مستويات)
```

### ❌ **النقوصات المكتشفة:**

```
❌ لا يمكن تعديل المرفقات
❌ لا يمكن حذف المرفقات
❌ لا يمكن حذف المستند نهائياً
❌ لا يوجد Soft Delete
❌ لا يوجد سلة محذوفات
❌ لا يوجد Bulk Upload
❌ لا يوجد رفع ملفات متعددة لنفس المستند
❌ لا يوجد نظام مجلدات متطور
❌ الصلاحيات محدودة جداً
❌ لا يوجد Role-Based Access Control متقدم
❌ لا يوجد Document Locking
❌ لا يوجد Download History
❌ لا يوجد Activity Log لكل مستند
❌ لا يوجد Favorites/Bookmarks
❌ لا يوجد Recent Documents
❌ لا يوجد File Preview
```

---

## 🎯 Phase 1: الميزات الحرجة (Week 1-2)

### 1.0 إدارة الأقسام وأنواع المستندات ✅✅

**API Endpoints للأقسام:**

```python
# Get Departments
POST /api/departments

# Get Single Department
POST /api/departments/{department_id}

# Create Department
POST /api/departments/create
Request:
{
    "name": "المشتريات",
    "code": "PUR",
    "description": "قسم المشتريات",
    "manager_ids": [5, 6],
    "sequence": 10
}

# Update Department
POST /api/departments/{department_id}/update
Request:
{
    "name": "المشتريات المركزي",
    "manager_ids": [5, 6, 7]
}

# Delete (Archive) Department
DELETE /api/departments/{department_id}
```

**API Endpoints لأنواع المستندات:**

```python
# Get Document Types
POST /api/document-types

# Get Single Document Type
POST /api/document-types/{doc_type_id}

# Create Document Type
POST /api/document-types/create
Request:
{
    "name": "فاتورة شراء",
    "code": "PINV",
    "department_id": 1,
    "description": "فواتير الشراء",
    "sequence": 10
}

# Update Document Type
POST /api/document-types/{doc_type_id}/update
Request:
{
    "name": "فاتورة شراء محلي",
    "description": "فواتير الشراء من الموردين المحليين"
}

# Delete (Archive) Document Type
DELETE /api/document-types/{doc_type_id}
```

**الميزات:**
- ✅ CRUD كامل للأقسام وأنواع المستندات
- ✅ حماية من الحذف إذا كان يحتوي مستندات
- ✅ Audit logging لكل عملية
- ✅ التحقق من تكرار الرموز (codes)
- ✅ صلاحيات محددة (Admin/Manager)

---

### 1.1 تعديل/حذف المرفقات ✅

**API Endpoints:**

```python
# Update Attachment
PUT /api/documents/{document_id}/attachments/{attachment_id}
Request:
{
    "name": "اسم جديد",
    "description": "وصف جديد",
    "file_data": "base64...",  # optional - replace file
    "file_name": "new_file.pdf"  # optional
}

# Delete Attachment (Soft Delete)
DELETE /api/documents/{document_id}/attachments/{attachment_id}
Response:
{
    "success": true,
    "message": "تم نقل المرفق إلى سلة المحذوفات"
}

# Permanent Delete Attachment
DELETE /api/documents/{document_id}/attachments/{attachment_id}/permanent
Response:
{
    "success": true,
    "message": "تم حذف المرفق نهائياً"
}
```

**Models Changes:**

```python
# nbs.document.attachment
class NBSDocumentAttachment(models.Model):
    # Add new fields
    is_deleted = fields.Boolean(default=False)
    deleted_at = fields.Datetime()
    deleted_by = fields.Many2one('res.users')
    restore_deadline = fields.Datetime()  # Auto-delete after 30 days
    
    # Methods
    def soft_delete(self):
        """Move to trash"""
        
    def restore(self):
        """Restore from trash"""
        
    def permanent_delete(self):
        """Delete permanently"""
```

---

### 1.2 Bulk Upload للملفات ✅✅

**API Endpoint:**

```python
POST /api/documents/bulk-upload
Request:
{
    "files": [
        {
            "name": "Document 1",
            "file_data": "base64...",
            "file_name": "doc1.pdf",
            "department_id": 1,
            "document_type_id": 2,
            "confidentiality_level": "internal",
            "tags": ["tag1", "tag2"]
        },
        {
            "name": "Document 2",
            "file_data": "base64...",
            "file_name": "doc2.pdf",
            ...
        }
    ],
    "folder_id": 123,  # optional - group in folder
    "auto_ocr": true   # optional - run OCR immediately
}

Response:
{
    "success": true,
    "data": {
        "total": 10,
        "succeeded": 8,
        "failed": 2,
        "documents": [
            {"id": 1, "name": "Document 1", "status": "success"},
            {"id": null, "name": "Document 2", "status": "failed", "error": "..."}
        ],
        "job_id": "bulk_upload_123456"  # for tracking
    }
}

# Track Progress
GET /api/documents/bulk-upload/{job_id}/progress
Response:
{
    "job_id": "bulk_upload_123456",
    "status": "processing",
    "total": 10,
    "processed": 5,
    "succeeded": 4,
    "failed": 1,
    "progress_percentage": 50
}
```

**Implementation:**

```python
# New Model: nbs.bulk.upload.job
class NBSBulkUploadJob(models.Model):
    _name = 'nbs.bulk.upload.job'
    
    job_id = fields.Char(required=True, index=True)
    user_id = fields.Many2one('res.users')
    total_files = fields.Integer()
    processed_files = fields.Integer()
    succeeded_files = fields.Integer()
    failed_files = fields.Integer()
    status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])
    created_document_ids = fields.Many2many('nbs.document')
    error_log = fields.Text()
    
# Controller
@http.route('/api/documents/bulk-upload', type='jsonrpc', auth='none')
def bulk_upload(self, files, folder_id=None, auto_ocr=False, **kwargs):
    """Handle bulk upload with background job"""
    job = create_bulk_job(files)
    # Process in background
    job.process_async()
    return job.get_status()
```

---

### 1.3 رفع ملفات متعددة لنفس المستند ✅

**API Endpoint:**

```python
POST /api/documents/{document_id}/add-multiple-attachments
Request:
{
    "attachments": [
        {
            "name": "Attachment 1",
            "file_data": "base64...",
            "file_name": "attach1.pdf",
            "description": "وصف",
            "attachment_type": "supporting"
        },
        {
            "name": "Attachment 2",
            ...
        }
    ]
}

Response:
{
    "success": true,
    "data": {
        "added": 5,
        "failed": 0,
        "attachments": [...]
    }
}
```

---

### 1.4 Soft Delete للمستندات ✅✅

**API Endpoints:**

```python
# Soft Delete Document
DELETE /api/documents/{document_id}
Response:
{
    "success": true,
    "message": "تم نقل المستند إلى سلة المحذوفات",
    "restore_deadline": "2024-03-07"  # 30 days
}

# Restore Document
POST /api/documents/{document_id}/restore
Response:
{
    "success": true,
    "message": "تم استعادة المستند بنجاح"
}

# Permanent Delete
DELETE /api/documents/{document_id}/permanent
Request:
{
    "confirmation": "DELETE_PERMANENT",
    "reason": "سبب الحذف النهائي"
}
Response:
{
    "success": true,
    "message": "تم حذف المستند نهائياً"
}

# Get Trash
GET /api/trash/documents
Response:
{
    "success": true,
    "data": [
        {
            "id": 123,
            "name": "مستند محذوف",
            "deleted_at": "2024-02-07",
            "deleted_by": "أحمد",
            "restore_deadline": "2024-03-07",
            "days_remaining": 28
        }
    ]
}

# Empty Trash
DELETE /api/trash/empty
Request:
{
    "older_than_days": 30,  # optional
    "confirmation": "EMPTY_TRASH"
}
```

**Models Changes:**

```python
# nbs.document
class NBSDocument(models.Model):
    # Add trash fields
    is_deleted = fields.Boolean(default=False, index=True)
    deleted_at = fields.Datetime()
    deleted_by = fields.Many2one('res.users')
    deletion_reason = fields.Text()
    restore_deadline = fields.Datetime()
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('trash', 'In Trash'),  # NEW
        ('deleted', 'Permanently Deleted')  # NEW
    ])
```

---

## 🔐 Phase 2: نظام صلاحيات متطور (Week 3-4)

### 2.1 Role-Based Access Control (RBAC) ✅✅

**New Security Groups:**

```python
# Existing (3 levels):
- NBS Archive User
- NBS Archive Manager  
- NBS Archive Administrator

# NEW (7 levels total):
- NBS Archive Viewer (Read-only)
- NBS Archive User (Read + Create)
- NBS Archive Editor (Read + Create + Edit own)
- NBS Archive Reviewer (Approve/Reject edits)
- NBS Archive Manager (Full access to department)
- NBS Archive Auditor (Read all + Audit logs)
- NBS Archive Administrator (Full system access)
```

**Permission Matrix:**

```
Action                  | Viewer | User | Editor | Reviewer | Manager | Auditor | Admin
------------------------|--------|------|--------|----------|---------|---------|-------
View Documents          |   ✅   |  ✅  |   ✅   |    ✅    |   ✅    |   ✅   |  ✅
Create Documents        |   ❌   |  ✅  |   ✅   |    ✅    |   ✅    |   ❌   |  ✅
Edit Own Documents      |   ❌   |  ❌  |   ✅   |    ✅    |   ✅    |   ❌   |  ✅
Edit Others' Docs       |   ❌   |  ❌  |   ❌   |    ❌    |   ✅    |   ❌   |  ✅
Delete Documents        |   ❌   |  ❌  |   ❌   |    ❌    |   ✅    |   ❌   |  ✅
Approve Edits           |   ❌   |  ❌  |   ❌   |    ✅    |   ✅    |   ❌   |  ✅
View Audit Logs         |   ❌   |  ❌  |   ❌   |    ❌    |   ✅    |   ✅   |  ✅
Manage Users            |   ❌   |  ❌  |   ❌   |    ❌    |   ❌    |   ❌   |  ✅
Restore from Trash      |   ❌   |  ❌  |   ❌   |    ❌    |   ✅    |   ❌   |  ✅
Permanent Delete        |   ❌   |  ❌  |   ❌   |    ❌    |   ❌    |   ❌   |  ✅
```

---

### 2.2 Document-Level Permissions ✅

**New Model:**

```python
class NBSDocumentPermission(models.Model):
    _name = 'nbs.document.permission'
    _description = 'Document-level permissions'
    
    document_id = fields.Many2one('nbs.document', required=True)
    user_id = fields.Many2one('res.users')
    group_id = fields.Many2one('res.groups')
    
    # Permissions
    can_read = fields.Boolean(default=True)
    can_write = fields.Boolean(default=False)
    can_delete = fields.Boolean(default=False)
    can_share = fields.Boolean(default=False)
    can_download = fields.Boolean(default=True)
    can_print = fields.Boolean(default=False)
    
    # Expiry
    expires_at = fields.Datetime()
    is_active = fields.Boolean(default=True)
    
    # Audit
    granted_by = fields.Many2one('res.users')
    granted_at = fields.Datetime(default=fields.Datetime.now)
```

**API Endpoints:**

```python
# Grant Permission
POST /api/documents/{document_id}/permissions
Request:
{
    "user_id": 5,
    "permissions": {
        "can_read": true,
        "can_write": true,
        "can_delete": false,
        "can_download": true
    },
    "expires_at": "2024-12-31"
}

# Revoke Permission
DELETE /api/documents/{document_id}/permissions/{permission_id}

# List Permissions
GET /api/documents/{document_id}/permissions
```

---

### 2.3 Department Hierarchy & Inheritance ✅

**Model Updates:**

```python
class NBSDepartment(models.Model):
    parent_id = fields.Many2one('nbs.department', 'Parent Department')
    child_ids = fields.One2many('nbs.department', 'parent_id')
    inherit_permissions = fields.Boolean(default=True)
    
    def get_all_child_departments(self):
        """Get all child departments recursively"""
        
    def get_users_with_access(self):
        """Get all users who have access (including inherited)"""
```

---

### 2.4 Confidentiality Levels Control ✅

**Enhanced Confidentiality:**

```python
# Current: public, internal, confidential, strict
# NEW: Add dynamic levels

class NBSConfidentialityLevel(models.Model):
    _name = 'nbs.confidentiality.level'
    
    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    level = fields.Integer()  # 0=lowest, 100=highest
    description = fields.Text()
    color = fields.Char()
    icon = fields.Char()
    
    # Who can access
    allowed_group_ids = fields.Many2many('res.groups')
    allowed_user_ids = fields.Many2many('res.users')
    
    # Restrictions
    restrict_download = fields.Boolean()
    restrict_print = fields.Boolean()
    restrict_share = fields.Boolean()
    watermark_required = fields.Boolean()
    
    # Audit
    log_all_access = fields.Boolean()
```

---

## 📁 Phase 3: نظام المجلدات المتطور (Week 5-6)

### 3.1 Folder System Enhancement ✅✅

**API Endpoints:**

```python
# Create Folder
POST /api/folders
Request:
{
    "name": "مجلد المشتريات 2024",
    "parent_id": null,  # or parent folder id
    "department_id": 1,
    "description": "وصف",
    "color": "#FF5733",
    "icon": "folder-open",
    "is_shared": false
}

# Move Documents to Folder
POST /api/folders/{folder_id}/add-documents
Request:
{
    "document_ids": [1, 2, 3, 4, 5]
}

# Move Multiple Documents
POST /api/documents/bulk-move
Request:
{
    "document_ids": [1, 2, 3],
    "target_folder_id": 10
}

# Folder Tree
GET /api/folders/tree
Response:
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "Root Folder",
            "children": [
                {
                    "id": 2,
                    "name": "Sub Folder",
                    "document_count": 15,
                    "children": []
                }
            ]
        }
    ]
}

# Search in Folder
POST /api/folders/{folder_id}/search
Request:
{
    "query": "invoice",
    "recursive": true  # search in subfolders
}
```

---

### 3.2 Smart Folders (Auto-categorization) ✅

**API Endpoint:**

```python
POST /api/folders/smart
Request:
{
    "name": "Invoices 2024",
    "rules": [
        {
            "field": "document_type_id",
            "operator": "=",
            "value": 5
        },
        {
            "field": "upload_date",
            "operator": ">=",
            "value": "2024-01-01"
        },
        {
            "field": "name",
            "operator": "contains",
            "value": "invoice"
        }
    ],
    "auto_add": true  # automatically add matching documents
}

# Smart folders automatically update based on rules
```

---

## 🚀 Phase 4: تحسينات الأداء والتجربة (Week 7-8)

### 4.1 Document Locking ✅

```python
# Lock Document
POST /api/documents/{document_id}/lock
Response:
{
    "success": true,
    "locked_by": "أحمد محمد",
    "locked_until": "2024-02-07 18:00:00"
}

# Unlock Document
POST /api/documents/{document_id}/unlock

# Check Lock Status
GET /api/documents/{document_id}/lock-status
```

---

### 4.2 Favorites & Bookmarks ✅

```python
# Add to Favorites
POST /api/documents/{document_id}/favorite

# Remove from Favorites
DELETE /api/documents/{document_id}/favorite

# Get Favorites
GET /api/favorites
Response:
{
    "success": true,
    "data": [
        {
            "id": 123,
            "name": "مستند مهم",
            "favorited_at": "2024-02-01"
        }
    ]
}
```

---

### 4.3 Recent Documents ✅

```python
# Get Recent Documents
GET /api/documents/recent
Response:
{
    "success": true,
    "data": [
        {
            "id": 123,
            "name": "مستند",
            "last_accessed": "2024-02-07 10:30:00",
            "access_count": 5
        }
    ]
}

# Track document view
POST /api/documents/{document_id}/track-view
```

---

### 4.4 Download History ✅

```python
# Get Download History
GET /api/documents/{document_id}/download-history
Response:
{
    "success": true,
    "data": [
        {
            "user": "أحمد",
            "downloaded_at": "2024-02-07 09:00:00",
            "ip_address": "192.168.1.10",
            "device": "Chrome on Windows"
        }
    ]
}
```

---

### 4.5 Activity Log ✅

```python
# Get Document Activity
GET /api/documents/{document_id}/activity
Response:
{
    "success": true,
    "data": [
        {
            "action": "created",
            "user": "أحمد",
            "timestamp": "2024-02-01 10:00:00",
            "details": "تم إنشاء المستند"
        },
        {
            "action": "edited",
            "user": "محمد",
            "timestamp": "2024-02-02 14:30:00",
            "details": "تم تعديل الاسم من X إلى Y"
        },
        {
            "action": "downloaded",
            "user": "سارة",
            "timestamp": "2024-02-03 09:15:00"
        }
    ]
}
```

---

## 🔍 Phase 5: بحث وتقارير متقدمة (Week 9-10)

### 5.1 Advanced Search ✅✅

```python
POST /api/search/advanced
Request:
{
    "query": "invoice",
    "filters": {
        "department_ids": [1, 2],
        "document_type_ids": [3, 4],
        "date_from": "2024-01-01",
        "date_to": "2024-02-07",
        "confidentiality_levels": ["internal", "public"],
        "uploaded_by": [5, 6],
        "tags": ["urgent", "finance"],
        "has_attachments": true,
        "min_size": 1024,  # bytes
        "max_size": 10485760,  # 10MB
        "file_types": ["pdf", "docx"]
    },
    "sort_by": "upload_date",
    "sort_order": "desc",
    "page": 1,
    "per_page": 20
}
```

---

### 5.2 Search Filters & Facets ✅

```python
GET /api/search/facets?query=invoice
Response:
{
    "success": true,
    "facets": {
        "document_types": [
            {"name": "Invoice", "count": 150},
            {"name": "Receipt", "count": 80}
        ],
        "departments": [
            {"name": "Finance", "count": 200},
            {"name": "HR", "count": 30}
        ],
        "years": [
            {"year": 2024, "count": 180},
            {"year": 2023, "count": 100}
        ],
        "file_types": [
            {"type": "pdf", "count": 180},
            {"type": "docx", "count": 50}
        ]
    }
}
```

---

### 5.3 Saved Searches ✅

```python
# Save Search
POST /api/search/save
Request:
{
    "name": "Invoices 2024",
    "query": {...},  # search params
    "notify_on_new": true
}

# Get Saved Searches
GET /api/search/saved

# Execute Saved Search
GET /api/search/saved/{search_id}/execute
```

---

### 5.4 Reports & Analytics ✅✅

```python
# Document Statistics
GET /api/reports/statistics
Response:
{
    "total_documents": 1500,
    "by_department": [...],
    "by_type": [...],
    "by_month": [...],
    "total_size": "15GB",
    "growth_rate": "+12%"
}

# User Activity Report
GET /api/reports/user-activity
Response:
{
    "most_active_users": [
        {"name": "أحمد", "uploads": 50, "edits": 30}
    ],
    "least_active": [...]
}

# Audit Report
GET /api/reports/audit
Request:
{
    "date_from": "2024-01-01",
    "date_to": "2024-02-07",
    "action_types": ["create", "edit", "delete"],
    "user_ids": [1, 2]
}

# Export Report
GET /api/reports/{report_id}/export?format=pdf
GET /api/reports/{report_id}/export?format=excel
GET /api/reports/{report_id}/export?format=csv
```

---

## 🎨 Phase 6: UI/UX Enhancements (Week 11-12)

### 6.1 File Preview ✅

```python
# Generate Preview
POST /api/documents/{document_id}/generate-preview
Response:
{
    "success": true,
    "preview_url": "/api/documents/123/preview",
    "thumbnail_url": "/api/documents/123/thumbnail"
}

# Get Preview
GET /api/documents/{document_id}/preview
# Returns image/html preview

# Get Thumbnail
GET /api/documents/{document_id}/thumbnail
# Returns thumbnail image
```

---

### 6.2 Quick Actions ✅

```python
# Duplicate Document
POST /api/documents/{document_id}/duplicate
Response:
{
    "success": true,
    "new_document_id": 456
}

# Share Document (Generate Link)
POST /api/documents/{document_id}/share
Request:
{
    "expires_in_days": 7,
    "allow_download": true,
    "password_protected": true,
    "password": "secret123"
}
Response:
{
    "success": true,
    "share_link": "https://domain.com/shared/abc123",
    "expires_at": "2024-02-14"
}

# Email Document
POST /api/documents/{document_id}/email
Request:
{
    "to": ["user@example.com"],
    "subject": "مستند مهم",
    "message": "نص الرسالة"
}
```

---

### 6.3 Batch Operations ✅✅

```python
# Bulk Delete
POST /api/documents/bulk-delete
Request:
{
    "document_ids": [1, 2, 3, 4, 5],
    "reason": "سبب الحذف"
}

# Bulk Update
POST /api/documents/bulk-update
Request:
{
    "document_ids": [1, 2, 3],
    "updates": {
        "document_type_id": 5,
        "tags": ["updated", "bulk"],
        "confidentiality_level": "internal"
    }
}

# Bulk Download (ZIP)
POST /api/documents/bulk-download
Request:
{
    "document_ids": [1, 2, 3, 4, 5]
}
Response:
{
    "success": true,
    "download_url": "/api/downloads/bulk_123456.zip",
    "expires_at": "2024-02-07 18:00:00"
}

# Bulk Move to Folder
POST /api/documents/bulk-move
Request:
{
    "document_ids": [1, 2, 3],
    "folder_id": 10
}

# Bulk Tag
POST /api/documents/bulk-tag
Request:
{
    "document_ids": [1, 2, 3],
    "tags": ["urgent", "review"]
}
```

---

## 🔒 Phase 7: الأمان والحماية (Week 13-14)

### 7.1 Document Encryption ✅

```python
# Enable encryption for document
POST /api/documents/{document_id}/encrypt
Request:
{
    "encryption_key": "user_provided_key"
}

# Decrypt and view
GET /api/documents/{document_id}/decrypt
Headers:
{
    "X-Encryption-Key": "user_key"
}
```

---

### 7.2 Watermarking ✅

```python
# Add watermark
POST /api/documents/{document_id}/watermark
Request:
{
    "text": "CONFIDENTIAL - أحمد محمد - 2024-02-07",
    "position": "diagonal",  # center, top, bottom, diagonal
    "opacity": 0.3
}
```

---

### 7.3 Access Control Lists (ACL) ✅

```python
# Get ACL
GET /api/documents/{document_id}/acl
Response:
{
    "success": true,
    "acl": [
        {
            "user": "أحمد",
            "permissions": ["read", "write"],
            "granted_at": "2024-02-01"
        }
    ]
}

# Update ACL
PUT /api/documents/{document_id}/acl
Request:
{
    "acl": [
        {"user_id": 5, "permissions": ["read"]},
        {"group_id": 3, "permissions": ["read", "write"]}
    ]
}
```

---

### 7.4 Two-Factor Authentication for Sensitive Actions ✅

```python
# Require 2FA for permanent delete
DELETE /api/documents/{document_id}/permanent
Request:
{
    "confirmation": "DELETE_PERMANENT",
    "otp_code": "123456"
}
```

---

## 📱 Phase 8: التكامل والأتمتة (Week 15-16)

### 8.1 Webhooks ✅

```python
# Register webhook
POST /api/webhooks
Request:
{
    "url": "https://your-app.com/webhook",
    "events": ["document.created", "document.deleted"],
    "secret": "webhook_secret"
}

# Events:
- document.created
- document.updated
- document.deleted
- document.downloaded
- document.shared
- edit_request.created
- edit_request.approved
```

---

### 8.2 Auto-tagging & AI Classification ✅

```python
# Enable auto-tagging
POST /api/documents/{document_id}/auto-tag
Response:
{
    "success": true,
    "suggested_tags": ["invoice", "finance", "2024"],
    "confidence": 0.95
}

# Auto-classify document type
POST /api/documents/{document_id}/auto-classify
Response:
{
    "success": true,
    "suggested_type": "Invoice",
    "confidence": 0.92
}
```

---

### 8.3 Scheduled Tasks ✅

```python
# Schedule auto-archive
POST /api/documents/{document_id}/schedule-archive
Request:
{
    "archive_after_days": 90
}

# Schedule auto-delete
POST /api/documents/{document_id}/schedule-delete
Request:
{
    "delete_after_days": 365,
    "notify_before_days": 30
}

# Bulk cleanup
POST /api/maintenance/cleanup
Request:
{
    "delete_trash_older_than": 30,
    "archive_inactive_older_than": 180
}
```

---

## 📊 Implementation Priority Matrix

```
Priority | Feature                        | Impact | Effort | Status
---------|--------------------------------|--------|--------|--------
P0       | Edit/Delete Attachments        | High   | Low    | ⏳ Week 1
P0       | Soft Delete & Trash            | High   | Medium | ⏳ Week 1
P0       | Bulk Upload                    | High   | Medium | ⏳ Week 2
P1       | Advanced Permissions           | High   | High   | ⏳ Week 3-4
P1       | Folder System                  | Medium | Medium | ⏳ Week 5-6
P2       | Document Locking               | Medium | Low    | ⏳ Week 7
P2       | Favorites & Recent             | Medium | Low    | ⏳ Week 7
P2       | Download History               | Medium | Low    | ⏳ Week 8
P2       | Activity Log                   | Medium | Medium | ⏳ Week 8
P3       | Advanced Search                | High   | Medium | ⏳ Week 9
P3       | Reports & Analytics            | Medium | Medium | ⏳ Week 10
P3       | File Preview                   | Low    | High   | ⏳ Week 11
P3       | Batch Operations               | Medium | Medium | ⏳ Week 12
P4       | Encryption                     | Low    | High   | ⏳ Week 13
P4       | Watermarking                   | Low    | Medium | ⏳ Week 13
P4       | ACL                            | Medium | Medium | ⏳ Week 14
P5       | Webhooks                       | Low    | Medium | ⏳ Week 15
P5       | Auto-tagging                   | Low    | High   | ⏳ Week 16
```

---

## 🎯 Quick Wins (أول أسبوع)

```
✅ Edit Attachment API (2 hours)
✅ Delete Attachment API (2 hours)
✅ Soft Delete Document (4 hours)
✅ Restore from Trash (2 hours)
✅ Bulk Upload (8 hours)

Total: ~18 hours = Week 1 Done!
```

---

## 📈 Success Metrics

```
Before:
- Basic CRUD only
- 3 permission levels
- No trash system
- Single file upload
- Limited search

After (16 weeks):
- Full CRUD + Trash + Restore
- 7 permission levels + ACL
- Bulk upload/download
- Advanced search + filters
- Reports & analytics
- File preview
- Document locking
- Activity tracking
- Webhooks & automation

Improvement: 500%+ in features
```

---

## 🚀 Getting Started

### Week 1 - Quick Implementation:

```bash
# 1. Create new branch
git checkout development
git pull origin development
git checkout -b feature/nbs-archive-enhancements

# 2. Install dependencies (if needed)
./install_nbs_dependencies.sh

# 3. Start implementing Phase 1
# - Edit attachments
# - Delete attachments  
# - Soft delete
# - Bulk upload

# 4. Test APIs
# 5. Commit & push
# 6. Move to Phase 2
```

---

## 📝 Notes

- كل Phase مستقل ويمكن تنفيذه بشكل منفصل
- الأولوية للـ P0 و P1 (أول 6 أسابيع)
- P2-P5 يمكن تأجيلها حسب الحاجة
- التوثيق مهم لكل feature
- اختبار شامل بعد كل Phase

---

**تاريخ الخطة:** 2026-02-07  
**المدة المقدرة:** 16 أسبوع  
**الحالة:** جاهز للتنفيذ ✅
