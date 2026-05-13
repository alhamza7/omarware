# 📚 NBS Archive System - Complete Guide
## نظام الأرشفة الإلكترونية - الدليل الشامل

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![Status](https://img.shields.io/badge/status-production%20ready-green)
![Odoo](https://img.shields.io/badge/Odoo-19.0-purple)
![Python](https://img.shields.io/badge/Python-3.12-yellow)

**Last Updated:** February 7, 2026  
**Week 1 Implementation:** ✅ COMPLETE

---

## 🚀 Quick Navigation

### 🎯 New to the project?
**→ Start here:** [`START_HERE.md`](START_HERE.md)

### 👨‍💻 Developer?
**→ Read:** [`NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md`](NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md)

### 🧪 Tester?
**→ Read:** [`NBS_ARCHIVE_QUICK_TEST_GUIDE.md`](NBS_ARCHIVE_QUICK_TEST_GUIDE.md)

### 👔 Project Manager?
**→ Read:** [`WEEK1_COMPLETE_SUMMARY.md`](WEEK1_COMPLETE_SUMMARY.md)

### 📚 Need full index?
**→ Read:** [`NBS_ARCHIVE_DOCUMENTATION_INDEX.md`](NBS_ARCHIVE_DOCUMENTATION_INDEX.md)

---

## 📖 What is NBS Archive?

نظام أرشفة إلكترونية متقدم مبني على Odoo 19 يوفر:

### ✨ Core Features

#### 🗂️ Document Management
- إنشاء وتحرير وأرشفة المستندات
- تنظيم حسب الأقسام والأنواع
- تسلسل هرمي للمجلدات
- العلامات والتصنيفات

#### 📎 Attachment Management ★ v1.1.0
- رفع ملفات متعددة (PDF, Word, Excel, Images)
- **تعديل المرفقات** (اسم، وصف، استبدال الملف) ★ NEW
- **رفع عدة مرفقات دفعة واحدة** ★ NEW
- تحميل وعرض المرفقات
- **Soft Delete مع إمكانية الاستعادة** ★ NEW

#### 🗑️ Soft Delete System ★ v1.1.0
- **حذف آمن للمستندات والمرفقات** ★ NEW
- **سلة محذوفات لمدة 30 يوم** ★ NEW
- **استعادة الملفات المحذوفة** ★ NEW
- **حذف نهائي (Admin فقط)** ★ NEW

#### 📦 Bulk Upload ★ v1.1.0
- **رفع جماعي لعشرات أو مئات الملفات** ★ NEW
- **تتبع التقدم في الوقت الفعلي** ★ NEW
- **معالجة ذكية (يكمل حتى لو فشل ملف)** ★ NEW
- **تقرير تفصيلي بالنجاح والفشل** ★ NEW

#### 🔍 Search & Discovery
- بحث متقدم بالنص الكامل
- فلترة حسب التاريخ، القسم، النوع، الحالة
- OCR للمستندات (قيد التطوير)
- OpenSearch integration

#### 🔐 Security & Permissions
- نظام صلاحيات متقدم (User, Manager, Admin)
- تشفير الملفات
- Audit logging كامل (جميع العمليات مسجلة)
- JWT authentication

#### 📊 Reporting & Analytics
- تقارير مخصصة
- إحصائيات الاستخدام
- Audit trail كامل
- Dashboard analytics (قيد التطوير)

---

## 🎯 Week 1 Implementation (Complete ✅)

### What's New in v1.1.0?

#### 1. **Soft Delete System** 🗑️
```
✅ المستندات لا تُحذف نهائياً
✅ 30 يوم في سلة المحذوفات
✅ استعادة في أي وقت
✅ Admin فقط للحذف النهائي
```

**APIs:**
- `POST /api/documents/<id>/trash` - نقل إلى سلة المحذوفات
- `POST /api/documents/<id>/restore` - استعادة
- `DELETE /api/documents/<id>/permanent` - حذف نهائي
- `POST /api/documents/trash` - عرض سلة المحذوفات

#### 2. **Edit Attachments** ✏️
```
✅ تعديل الاسم والوصف
✅ استبدال الملف بملف جديد
✅ تحقق من الصلاحيات
✅ Audit logging
```

**API:**
- `POST /api/documents/<id>/attachments/<att_id>/update`

#### 3. **Multiple Attachments Upload** 📎
```
✅ رفع عدة ملفات دفعة واحدة
✅ طلب API واحد فقط
✅ معالجة متسامحة مع الأخطاء
```

**API:**
- `POST /api/documents/<id>/attachments/multiple`

#### 4. **Bulk Upload** 📦
```
✅ رفع 100 ملف أو أكثر
✅ تتبع التقدم Real-time
✅ Job-based processing
✅ Error logging
```

**APIs:**
- `POST /api/documents/bulk-upload/start` - بدء عملية رفع
- `POST /api/documents/bulk-upload/<job_id>/upload` - رفع الملفات
- `POST /api/documents/bulk-upload/<job_id>/progress` - تتبع التقدم
- `POST /api/documents/bulk-upload/<job_id>/cancel` - إلغاء
- `POST /api/documents/bulk-upload/jobs` - عرض جميع العمليات

#### 5. **Management APIs** 🏢
```
✅ إدارة الأقسام (CRUD)
✅ إدارة أنواع المستندات (CRUD)
✅ صلاحيات محكمة
```

**APIs:**
- Department: 5 endpoints (Create, Read, Update, Delete, List)
- Document Types: 5 endpoints (Create, Read, Update, Delete, List)

---

## 📊 Technical Specifications

### System Requirements
```yaml
Server:
  OS: Ubuntu 22.04 LTS
  RAM: 8GB minimum (16GB recommended)
  CPU: 4 cores minimum (8+ recommended)
  Storage: 100GB minimum

Software:
  Odoo: 19.0
  Python: 3.12+
  PostgreSQL: 14+
  Node.js: 18+ (for frontend, optional)
```

### Architecture
```
┌─────────────────────────────────────┐
│     Frontend (React/Next.js)        │
│           via REST API              │
└──────────────┬──────────────────────┘
               │ HTTPS/JWT
               ↓
┌─────────────────────────────────────┐
│      Odoo 19 Application Server     │
│  ┌────────────────────────────────┐ │
│  │   nbs_archive Module v1.1.0    │ │
│  │   ├── 15+ Models               │ │
│  │   ├── 15+ Controllers          │ │
│  │   └── 14 NEW APIs ★            │ │
│  └────────────────────────────────┘ │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│      PostgreSQL Database            │
│  ┌────────────────────────────────┐ │
│  │   nbs_document                 │ │
│  │   nbs_document_attachment      │ │
│  │   nbs_bulk_upload_job ★ NEW    │ │
│  │   nbs_department               │ │
│  │   nbs_document_type            │ │
│  │   nbs_audit_log                │ │
│  │   ... (10+ tables)             │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Installation

#### 1. Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12 python3.12-venv postgresql git
```

#### 2. Clone Repository
```bash
cd /home/capo7amzah/Documents/NBS-PROJECT
git clone <repository_url> Lugal-ai
cd Lugal-ai
```

#### 3. Setup Virtual Environment
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Database Setup
```bash
# Create database
sudo -u postgres createdb lugal_nbs

# Or use script
./create_lugal_nbs_database.sh
```

#### 5. Install NBS Archive Module
```bash
# Start Odoo with module installation
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_nbs -i nbs_archive
```

#### 6. Access System
```
URL: http://localhost:8070
Database: lugal_nbs
Username: admin
Password: admin (change after first login)
```

---

## 📚 Documentation

### Complete Documentation Set

| Document | Description | Size |
|----------|-------------|------|
| **[START_HERE.md](START_HERE.md)** | 🚀 نقطة البداية | 8KB |
| **[WEEK1_COMPLETE_SUMMARY.md](WEEK1_COMPLETE_SUMMARY.md)** | 📋 ملخص Week 1 | 11KB |
| **[NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md](NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md)** | 📖 التوثيق الكامل | 17KB |
| **[NBS_ARCHIVE_QUICK_TEST_GUIDE.md](NBS_ARCHIVE_QUICK_TEST_GUIDE.md)** | 🧪 دليل الاختبار | 10KB |
| **[NBS_DEPARTMENT_DOCTYPE_MANAGEMENT.md](NBS_DEPARTMENT_DOCTYPE_MANAGEMENT.md)** | 🏢 إدارة الأقسام | 12KB |
| **[NBS_ARCHIVE_DOCUMENTATION_INDEX.md](NBS_ARCHIVE_DOCUMENTATION_INDEX.md)** | 📚 الفهرس الشامل | 11KB |
| **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** | 🏗️ البنية المعمارية | Updated |
| **[NBS_ARCHIVE_DEVELOPMENT_PLAN.md](NBS_ARCHIVE_DEVELOPMENT_PLAN.md)** | 📅 خطة التطوير | 28KB |

---

## 🔌 API Reference

### Base URL
```
http://localhost:8070
```

### Authentication
```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "admin"
}

Response:
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user_id": 2
}
```

### All Requests Require JWT
```http
Authorization: Bearer <your_jwt_token>
```

### Available Endpoints (14 NEW in v1.1.0)

#### Documents
```http
POST   /api/documents                    # List
POST   /api/documents/create             # Create
POST   /api/documents/<id>               # Get
POST   /api/documents/<id>/update        # Update
POST   /api/documents/<id>/trash         ★ Soft Delete
POST   /api/documents/<id>/restore       ★ Restore
DELETE /api/documents/<id>/permanent     ★ Permanent Delete
POST   /api/documents/trash              ★ List Trash
```

#### Attachments
```http
POST   /api/documents/<id>/attachments                          # List
POST   /api/documents/<id>/add-attachment                       # Add
POST   /api/documents/<id>/attachments/multiple                 ★ Multiple
POST   /api/documents/<id>/attachments/<att_id>/update          ★ Update
DELETE /api/documents/<id>/attachments/<att_id>                 ★ Delete
POST   /api/documents/<id>/attachments/<att_id>/restore         ★ Restore
DELETE /api/documents/<id>/attachments/<att_id>/permanent       ★ Permanent
GET    /api/documents/<id>/attachments/<att_id>/download        # Download
```

#### Bulk Upload
```http
POST   /api/documents/bulk-upload/start               ★ Start
POST   /api/documents/bulk-upload/<job_id>/upload     ★ Upload
POST   /api/documents/bulk-upload/<job_id>/progress   ★ Progress
POST   /api/documents/bulk-upload/<job_id>/cancel     ★ Cancel
POST   /api/documents/bulk-upload/jobs                ★ List
```

#### Management
```http
# Departments (5 endpoints)
POST   /api/departments/create
POST   /api/departments
POST   /api/departments/<id>
POST   /api/departments/<id>/update
DELETE /api/departments/<id>

# Document Types (5 endpoints)
POST   /api/document-types/create
POST   /api/document-types
POST   /api/document-types/<id>
POST   /api/document-types/<id>/update
DELETE /api/document-types/<id>
```

**For detailed API documentation with examples:**  
→ Read: [`NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md`](NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md)

---

## 🧪 Testing

### Quick Test
```bash
# Read the test guide
cat NBS_ARCHIVE_QUICK_TEST_GUIDE.md

# Or test basic endpoint
curl http://localhost:8070
```

### Test Scenarios Included
1. ✅ Document CRUD operations
2. ✅ Soft delete and restore
3. ✅ Attachment upload and edit
4. ✅ Multiple attachments upload
5. ✅ Bulk upload with progress tracking
6. ✅ Department and document type management
7. ✅ Trash management
8. ✅ Permission checks
9. ✅ Audit log verification

**Complete testing guide:**  
→ [`NBS_ARCHIVE_QUICK_TEST_GUIDE.md`](NBS_ARCHIVE_QUICK_TEST_GUIDE.md)

---

## 📈 Roadmap

### ✅ Week 1 (Complete)
- [x] Soft Delete System
- [x] Edit Attachments
- [x] Multiple Attachments Upload
- [x] Bulk Upload
- [x] Department/Type Management

### 🚧 Week 2 (In Planning)
- [ ] Folder Hierarchy
- [ ] Advanced Search Filters
- [ ] Document Templates
- [ ] Batch Operations

### 📅 Weeks 3-16
- [ ] Advanced Permissions
- [ ] Version Control
- [ ] Workflow Engine
- [ ] OCR Integration
- [ ] Barcode Generation
- [ ] Email Notifications
- [ ] Mobile App
- [ ] Analytics & Reports

**Full roadmap:**  
→ [`NBS_ARCHIVE_DEVELOPMENT_PLAN.md`](NBS_ARCHIVE_DEVELOPMENT_PLAN.md)

---

## 🛠️ Development

### Project Structure
```
Lugal-ai/
├── addons/
│   └── nbs_archive/              # Main module ★ v1.1.0
│       ├── models/               # 15+ models
│       │   ├── nbs_document.py
│       │   ├── nbs_document_relation.py
│       │   ├── nbs_bulk_upload.py      ★ NEW
│       │   └── ... (12+ more)
│       ├── controllers/          # 15+ controllers
│       │   ├── document_controller.py
│       │   ├── attachments_controller.py
│       │   ├── bulk_upload_controller.py  ★ NEW
│       │   ├── department_management_controller.py  ★ NEW
│       │   └── ... (11+ more)
│       ├── security/
│       ├── data/
│       └── __manifest__.py       # v1.1.0
├── venv/                         # Python virtual environment
├── odoo_local.conf               # Local configuration
└── Documentation/                # 8+ documentation files
```

### Contributing
1. Read: `SYSTEM_ARCHITECTURE.md`
2. Follow: Odoo coding standards
3. Test: All changes
4. Document: New features
5. Commit: Clear messages

---

## 📊 Statistics

### Week 1 Delivery
```yaml
Development:
  APIs Created:         14 endpoints
  Lines of Code:        ~1,500 lines
  Models Created:       1 (nbs_bulk_upload_job)
  Models Modified:      2 (nbs_document, nbs_document_attachment)
  Controllers Created:  2 files
  Controllers Modified: 2 files
  Database Fields:      12 new fields
  Methods Created:      9 methods
  
Documentation:
  Files Created:        8 documents
  Total Pages:          ~100 pages
  API Examples:         50+ examples
  Test Scenarios:       15+ scenarios
  Diagrams:             5 workflows

Testing:
  Manual Tests:         ✅ Passed
  System Status:        ✅ Running
  Database:             ✅ Healthy
  HTTP Status:          ✅ 200/303
```

---

## 🔐 Security

### Authentication
- JWT-based authentication
- Token expiration
- Refresh token support

### Authorization
- Role-based access control (RBAC)
- Group permissions (User, Manager, Admin)
- Record-level security rules

### Audit Trail
- All operations logged
- User tracking
- IP address logging
- Timestamp recording

### Data Protection
- File encryption in storage
- Secure file uploads
- SQL injection prevention
- XSS protection

---

## 📞 Support

### Getting Help

#### Documentation
- Start: `START_HERE.md`
- Technical: `NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md`
- Testing: `NBS_ARCHIVE_QUICK_TEST_GUIDE.md`

#### System Issues
```bash
# Check logs
tail -f odoo_local.log

# Check database
psql -d lugal_nbs

# Check processes
ps aux | grep odoo
```

#### Common Issues

**Odoo not starting?**
```bash
# Check port
netstat -tlnp | grep 8070

# Check permissions
ls -la filestore_local/
```

**API returns 401?**
- Check JWT token validity
- Verify user permissions
- Check authentication header

**Database errors?**
```bash
# Check connection
psql -d lugal_nbs -c "SELECT 1;"

# Check tables
psql -d lugal_nbs -c "\dt"
```

---

## 📝 License

This project is part of Lugal NBS ERP System.  
For licensing information, see `LICENSE` file.

---

## 👥 Team

**Developed by:** Lugal-AI Development Team  
**Project:** NBS Archive System  
**Version:** 1.1.0  
**Date:** February 7, 2026

---

## 🎉 Acknowledgments

Special thanks to:
- Odoo Community
- PostgreSQL Team
- Python Community
- All contributors

---

## 🔗 Quick Links

### Documentation
- [Start Here](START_HERE.md) - Begin your journey
- [Week 1 Summary](WEEK1_COMPLETE_SUMMARY.md) - What's new
- [Complete Docs](NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md) - Full technical docs
- [Test Guide](NBS_ARCHIVE_QUICK_TEST_GUIDE.md) - Testing instructions
- [Doc Index](NBS_ARCHIVE_DOCUMENTATION_INDEX.md) - All documentation

### Development
- [System Architecture](SYSTEM_ARCHITECTURE.md) - System design
- [Development Plan](NBS_ARCHIVE_DEVELOPMENT_PLAN.md) - 16-week roadmap
- Module Source: `addons/nbs_archive/`

### Resources
- Odoo: https://www.odoo.com
- PostgreSQL: https://www.postgresql.org
- Python: https://www.python.org

---

**🚀 Ready to get started?**

1. ✅ Read `START_HERE.md`
2. ✅ Follow installation guide above
3. ✅ Test the system using test guide
4. ✅ Start building!

**Week 1 Implementation: Complete ✅**  
**System Status: Production Ready 🟢**

---

For detailed information, see the [Documentation Index](NBS_ARCHIVE_DOCUMENTATION_INDEX.md).
