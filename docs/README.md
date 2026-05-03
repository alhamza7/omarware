# 📦 NBS Archive System

**Enterprise Document Archiving System for Noor Al Nibras (NBS) - FMCG Company**

A complete, production-ready document management system built on **Odoo 19** with a modern **React frontend**.

---

## 🌟 Features

### Core Functionality
- ✅ **Department-based document management** with strict isolation
- ✅ **Role-based access control** (Admin, Manager, User)
- ✅ **Document versioning** with full history
- ✅ **Edit request workflow** with manager approval
- ✅ **One-time unlock tokens** for secure editing
- ✅ **Barcode generation** and search
- ✅ **Advanced search** with filters
- ✅ **Audit logging** for all operations
- ✅ **Real-time notifications**
- ✅ **Bilingual** (Arabic RTL + English)
- ✅ **No hard deletes** - archive only

### Technical Features
- ✅ **OCR ready** (Tesseract for Arabic + English)
- ✅ **OpenSearch integration** for content search
- ✅ **REST API** (JSON-RPC)
- ✅ **Automatic backups**
- ✅ **Session-based authentication**

---

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.12+
- PostgreSQL 18
- Node.js 18+

### Installation

1. **Clone and navigate**:
```powershell
cd D:\capo_dev\Lugal-ai
```

2. **Start the system**:
```powershell
.\start_nbs_archive.ps1
```

3. **Open browser**:
```
http://localhost:5173
```

4. **Login**:
- Username: `admin`
- Password: `admin`

---

## 📁 Project Structure

```
Lugal-ai/
├── nbs_archive/              # Odoo module
│   ├── models/               # Database models
│   ├── controllers/          # API endpoints
│   ├── services/             # Business logic
│   ├── security/             # Access control
│   └── data/                 # Seed data
├── frontend/                 # React application
│   ├── src/
│   │   ├── api/              # API clients
│   │   ├── components/       # UI components
│   │   ├── pages/            # Application pages
│   │   ├── stores/           # State management
│   │   └── i18n/             # Translations
│   └── vite.config.ts        # Vite configuration
└── scripts/                  # Utility scripts
    ├── backup.ps1            # Backup script
    └── restore.ps1           # Restore script
```

---

## 🔧 Configuration

### Database
- **Host**: localhost
- **Port**: 5432
- **Database**: lugal
- **User**: odoo_user
- **Password**: root

### Ports
- **Odoo Backend**: 8070
- **React Frontend**: 5173

---

## 🎯 Usage

### Document Management

1. **Upload Document**:
   - Navigate to "Documents" → "Upload"
   - Select department and document type
   - Fill metadata and upload file
   - Document is automatically **locked** after upload

2. **Request Edit**:
   - Open document
   - Click "Request Edit"
   - Provide reason
   - Manager receives notification

3. **Approve Edit** (Manager only):
   - Go to "Edit Requests"
   - Review pending requests
   - Approve or reject
   - System generates one-time unlock token

4. **Upload New Version**:
   - Use unlock token from approval
   - Upload new file
   - Previous versions are preserved
   - Document is re-locked

### Search

- **Basic**: Search by title, barcode, or metadata
- **Barcode**: Scan or enter barcode manually
- **Advanced**: Filter by department, type, date range
- **Content** (requires OpenSearch): Search inside documents

### Backup & Restore

**Backup**:
```powershell
.\scripts\backup.ps1
```

**Restore**:
```powershell
.\scripts\restore.ps1 -BackupPath "D:\nbs_backups\nbs_archive_backup_20251217_120000"
```

---

## 👥 User Roles

### Admin
- Full system access
- Manage departments and document types
- View all audit logs
- Archive/unarchive documents

### Manager (per department)
- Approve/reject edit requests
- Archive/unarchive documents in their department
- View department documents
- Manage tags

### User (per department)
- Upload documents
- View documents in their department
- Request document edits
- Download documents

---

## 🔐 Security

- **Department Isolation**: Users only see their department's documents
- **Confidentiality Levels**:
  - Public: All department members
  - Internal: All department members
  - Confidential: Managers + Admins only
  - Strict: Admins only
- **No Hard Deletes**: Only archiving/soft delete
- **Audit Trail**: Every action is logged
- **Session-based Auth**: Secure Odoo sessions

---

## 🛠️ Maintenance

### Start Services
```powershell
.\start_nbs_archive.ps1
```

### Stop Services
```powershell
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

### View Logs
- Odoo: `D:\capo_dev\Lugal-ai\odoo.log`
- Frontend: Console in terminal

### Update Module
```powershell
.\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal -u nbs_archive --stop-after-init
```

---

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh token

### Documents
- `POST /api/documents` - List documents
- `POST /api/documents/{id}` - Get document details
- `POST /api/documents/upload` - Upload new document
- `GET /api/documents/{id}/download` - Download document
- `POST /api/documents/{id}/archive` - Archive document
- `POST /api/documents/{id}/upload-version` - Upload new version

### Edit Requests
- `POST /api/edit-requests` - List edit requests
- `POST /api/edit-requests/create` - Create edit request
- `POST /api/edit-requests/{id}/approve` - Approve request
- `POST /api/edit-requests/{id}/reject` - Reject request

### Search
- `POST /api/search` - Search documents
- `POST /api/search/barcode` - Search by barcode

### Notifications
- `POST /api/notifications` - Get notifications
- `POST /api/notifications/{id}/mark-read` - Mark as read
- `POST /api/notifications/mark-all-read` - Mark all as read

### Admin
- `POST /api/departments` - List departments
- `POST /api/document-types` - List document types
- `POST /api/stats/dashboard` - Dashboard statistics
- `POST /api/audit-logs` - Audit logs (Admin only)

---

## 🐛 Troubleshooting

### Odoo won't start
```powershell
# Check if port 8070 is in use
netstat -ano | findstr "8070"

# Check database connection
psql -h localhost -p 5432 -U odoo_user -d lugal
```

### Frontend won't start
```powershell
# Clear node_modules and reinstall
cd frontend
rm -r node_modules
npm install
```

### Database issues
```powershell
# Recreate database
$env:PGPASSWORD = "root"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -c "DROP DATABASE lugal;"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -c "CREATE DATABASE lugal WITH OWNER = odoo_user ENCODING = 'UTF8';"

# Reinitialize
.\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal -i nbs_archive --stop-after-init
```

---

## 📚 Documentation

- **Architecture**: See `NBS_ARCHIVE_HYBRID_ARCHITECTURE.md`
- **Arabic docs**: See `README_AR.md`
- **Project status**: See `PROJECT_STATUS.md`

---

## 🤝 Support

For issues or questions:
1. Check logs in `odoo.log`
2. Check browser console (F12)
3. Review `PROJECT_STATUS.md` for known limitations

---

## 📝 License

LGPL-3

---

**Built with ❤️ for Noor Al Nibras (NBS)**
