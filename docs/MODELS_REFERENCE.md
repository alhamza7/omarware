# 📊 NBS Archive Models Reference v2.0.0

## جميع Models (25+)

---

## 1. Core Models

### 1.1 nbs.document
**الوثيقة الرئيسية**

```python
Fields:
- name: str
- document_number: str (auto-generated)
- department_id: Many2one
- document_type_id: Many2one
- folder_id: Many2one (NEW)
- state: Selection [draft, active, archived, trash]
- confidentiality_level: Selection
- uploader_id: Many2one
- is_deleted: Boolean
- deleted_at: Datetime
- deleted_by: Many2one
- deletion_reason: Text
- restore_deadline: Datetime
- state_before_trash: Char

Methods:
- soft_delete(reason)
- restore_from_trash()
- permanent_delete()
```

### 1.2 nbs.document.attachment
**المرفقات**

```python
Fields:
- document_id: Many2one
- name: Char
- file_data: Binary
- file_size: Float
- mime_type: Char
- is_deleted: Boolean
- deleted_at: Datetime
- deleted_by: Many2one
- deletion_reason: Text
- restore_deadline: Datetime

Methods:
- soft_delete(reason)
- restore()
- permanent_delete()
```

### 1.3 nbs.department
**الأقسام**

```python
Fields:
- name: Char
- code: Char (unique)
- description: Text
- manager_ids: Many2many
- sequence: Integer
- active: Boolean
```

### 1.4 nbs.document.type
**أنواع المستندات**

```python
Fields:
- name: Char
- code: Char (unique)
- description: Text
- sequence: Integer
- active: Boolean
```

---

## 2. Organization Models (Week 2)

### 2.1 nbs.document.folder ⭐ NEW
**الملفات الهرمية**

```python
Fields:
- name: Char
- parent_id: Many2one (self)
- parent_path: Char (auto)
- level: Integer (compute)
- full_path: Char (compute)
- child_ids: One2many (self)
- document_count: Integer (compute)
- subfolder_count: Integer (compute)
- department_id: Many2one
- description: Text
- color: Integer
- active: Boolean
- user_ids: Many2many (access control)

Methods:
- _get_all_children()
- check_access(user)
- move_to_folder(new_parent)

Features:
- _parent_store = True
- Hierarchical structure
- Access control
```

### 2.2 nbs.saved.search ⭐ NEW
**البحث المحفوظ**

```python
Fields:
- name: Char
- user_id: Many2one
- search_criteria: Text (JSON)
- is_public: Boolean
- use_count: Integer
- last_used: Datetime

Methods:
- _build_domain()
- execute_search()
```

### 2.3 nbs.document.template ⭐ NEW
**قوالب المستندات**

```python
Fields:
- name: Char
- department_id: Many2one
- document_type_id: Many2one
- folder_id: Many2one
- default_name_pattern: Char
- description: Text
- confidentiality_level: Selection
- default_tags: Char

Methods:
- create_document_from_template()
```

### 2.4 nbs.batch.operation ⭐ NEW
**العمليات الجماعية**

```python
Fields:
- name: Char
- operation_type: Selection [archive, unarchive, trash, restore, change_folder, change_department, add_tags, remove_tags]
- document_ids: Many2many
- created_by: Many2one
- executed_at: Datetime
- status: Selection [pending, success, failed]
- result_log: Text

Methods:
- execute_batch_operation()
```

---

## 3. Security Models (Week 3-4)

### 3.1 nbs.permission.rule ⭐ NEW
**قواعد الصلاحيات المتقدمة**

```python
Fields:
- name: Char
- group_id: Many2one
- department_id: Many2one
- folder_id: Many2one
- document_type_id: Many2one
- confidentiality_levels: Char (JSON list)
- can_read: Boolean
- can_create: Boolean
- can_write: Boolean
- can_delete: Boolean
- can_archive: Boolean
- can_share: Boolean

Methods:
- check_permission(user, document, action)
```

### 3.2 nbs.document.share ⭐ NEW
**مشاركة المستندات**

```python
Fields:
- document_id: Many2one
- share_link: Char (compute/unique)
- created_by: Many2one
- expires_at: Datetime
- can_download: Boolean
- can_edit: Boolean
- access_count: Integer
- last_accessed: Datetime

Methods:
- generate_share_link()
- validate_access()
```

---

## 4. Versioning Models (Week 5-6)

### 4.1 nbs.document.version
**إصدارات المستندات (Enhanced)**

```python
Fields (Original):
- document_id: Many2one
- version_number: Integer
- file_data: Binary
- change_notes: Text
- created_by: Many2one
- created_at: Datetime

New Fields (Week 5-6):
- changes_summary: Text (compute)
- diff_content: Text
- version_tag: Char
- is_major: Boolean
- approval_status: Selection [pending, approved, rejected]
- approved_by: Many2one
- approved_at: Datetime
- rejection_reason: Text

Methods:
- compare_with_version(other_version)
- approve_version()
- rollback_to_this_version()
```

---

## 5. Workflow Models (Week 7-8)

### 5.1 nbs.workflow.template ⭐ NEW
**قوالب سير العمل**

```python
Fields:
- name: Char
- description: Text
- department_id: Many2one
- document_type_id: Many2one
- step_ids: One2many
- active: Boolean

Methods:
- start_workflow(document)
```

### 5.2 nbs.workflow.step ⭐ NEW
**خطوات سير العمل**

```python
Fields:
- workflow_id: Many2one
- name: Char
- sequence: Integer
- action_type: Selection [approval, review, sign, notify, auto]
- assigned_user_id: Many2one
- assigned_group_id: Many2one
- deadline_days: Integer
```

### 5.3 nbs.workflow.instance ⭐ NEW
**تشغيل سير العمل**

```python
Fields:
- workflow_template_id: Many2one
- document_id: Many2one
- current_step_id: Many2one
- state: Selection [running, completed, cancelled]
- started_at: Datetime
- completed_at: Datetime
- progress_percentage: Float (compute)

Methods:
- move_to_next_step()
- approve_step()
- reject_step()
- cancel_workflow()
```

---

## 6. OCR Models (Week 9-10)

### 6.1 nbs.ocr.service ⭐ NEW
**خدمة التعرف الضوئي**

```python
Fields:
- name: Char
- attachment_id: Many2one
- document_id: Many2one
- status: Selection [pending, processing, completed, failed]
- extracted_text: Text
- confidence_score: Float
- language: Char
- processed_at: Datetime
- error_message: Text

Methods:
- process_ocr()
  - Uses pytesseract
  - Supports Arabic & English
  - PDF & Image support
```

---

## 7. Notification Models (Week 11-12)

### 7.1 nbs.email.notification ⭐ NEW
**إشعارات البريد الإلكتروني**

```python
Fields:
- name: Char (subject)
- recipient_ids: Many2many
- body: Html
- template_id: Many2one
- sent_at: Datetime
- status: Selection [pending, sent, failed]
- error_message: Text

Methods:
- send_notification()
```

---

## 8. Analytics Models (Week 13-14)

### 8.1 nbs.document.analytics ⭐ NEW
**التحليلات والتقارير**

```python
Fields:
- name: Char
- report_type: Selection [department, type, user, timeline, storage]
- date_from: Date
- date_to: Date
- department_id: Many2one
- total_documents: Integer (compute)
- active_documents: Integer (compute)
- archived_documents: Integer (compute)
- trash_documents: Integer (compute)
- total_size_mb: Float (compute)

Methods:
- _compute_stats()
- _compute_storage()
- generate_report()
```

---

## 9. Mobile Models (Week 15-16)

### 9.1 nbs.mobile.session ⭐ NEW
**جلسات الهاتف**

```python
Fields:
- user_id: Many2one
- device_id: Char
- device_type: Selection [android, ios]
- fcm_token: Char
- app_version: Char
- last_sync: Datetime
- active: Boolean
```

### 9.2 nbs.mobile.sync ⭐ NEW
**مزامنة البيانات**

```python
Fields:
- session_id: Many2one
- sync_type: Selection [full, incremental, selective]
- started_at: Datetime
- completed_at: Datetime
- status: Selection [pending, syncing, completed, failed]
- documents_synced: Integer
- attachments_synced: Integer
- error_log: Text
```

---

## 10. Bulk Upload Models (Week 1)

### 10.1 nbs.bulk.upload.job
**وظائف الرفع الجماعي**

```python
Fields:
- job_id: Char (unique)
- user_id: Many2one
- department_id: Many2one
- document_type_id: Many2one
- folder_id: Many2one
- status: Selection [pending, processing, completed, cancelled, failed]
- total_files: Integer
- processed_files: Integer
- progress_percentage: Float (compute)
- created_document_ids: Many2many
- error_log: Text

Methods:
- process_upload(files)
- get_progress_info()
```

---

## 📊 Total Models Summary

```yaml
Core Models:           4
Organization:          4 (Week 2)
Security:              2 (Week 3-4)
Versioning:            1 enhanced (Week 5-6)
Workflow:              3 (Week 7-8)
OCR:                   1 (Week 9-10)
Notifications:         1 (Week 11-12)
Analytics:             1 (Week 13-14)
Mobile:                2 (Week 15-16)
Bulk Upload:           1 (Week 1)

TOTAL:                20 Models ✅
```

Plus inherited/existing Odoo models.

---

## 🔗 Relationships

```
nbs.document
  ├── department_id → nbs.department
  ├── document_type_id → nbs.document.type
  ├── folder_id → nbs.document.folder (NEW)
  ├── attachment_ids → nbs.document.attachment
  ├── version_ids → nbs.document.version
  └── workflow_ids → nbs.workflow.instance

nbs.document.folder (Hierarchical)
  ├── parent_id → self
  └── child_ids → self

nbs.workflow.template
  ├── step_ids → nbs.workflow.step
  └── instance_ids → nbs.workflow.instance

nbs.document.analytics
  └── Computes stats from all documents
```

---

**Version:** 2.0.0  
**Status:** Complete  
**Last Updated:** February 7, 2026
