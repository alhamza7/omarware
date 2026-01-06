# NBS Archive System - Quick Start Guide

## What You Have

Three comprehensive planning documents have been created for the NBS Enterprise Archiving System:

### 1. **NBS_ARCHIVE_HYBRID_ARCHITECTURE.md** (English, 60+ pages)
Complete technical specification with:
- Full architecture diagram (Odoo Backend + React Frontend)
- All REST API endpoints with request/response examples
- Authentication flow (JWT)
- Database models (7 core models)
- File structures for both Backend and Frontend
- Docker Compose setup
- CORS configuration
- WebSocket for real-time notifications

### 2. **NBS_ARCHIVE_HYBRID_AR.md** (Arabic, 30+ pages)
Arabic summary covering:
- Architecture overview
- API examples in Arabic
- Benefits and considerations
- Implementation timeline (12-15 weeks)
- Technology stack

### 3. **NBS_ARCHIVE_ODOO_MODULE_PLAN.md** (Original Odoo-only plan)
Previous plan for pure Odoo module approach (for reference)

---

## Architecture Summary

```
┌─────────────────────────┐
│   React Frontend        │  <- Full design freedom
│   (Port 5173)           │  <- TypeScript + Vite
│   - Modern UI/UX        │  <- Material-UI / Ant Design
│   - RTL Arabic support  │  <- i18next
│   - PDF Viewer          │  <- react-pdf
│   - Barcode Scanner     │  <- zxing
│   - Voice Search        │  <- Web Speech API
└────────┬────────────────┘
         │
         │ REST API + WebSocket
         │
┌────────▼────────────────┐
│   Odoo Backend          │  <- Business logic
│   (Port 8069)           │  <- Odoo ORM + PostgreSQL
│   nbs_archive module    │  <- Security + Permissions
│   - REST Controllers    │  <- Queue Job (OCR)
│   - JWT Auth            │  <- OpenSearch integration
│   - Department isolation│  <- File storage
│   - Versioning workflow │  <- Audit logging
└─────────────────────────┘
```

---

## Key Features Covered

### ✅ Document Management
- Upload documents with metadata
- Automatic barcode generation
- Document locking (no edits without approval)
- Version control (all versions preserved)
- Download/view documents
- Archive (never delete)

### ✅ OCR & Search
- Background OCR processing (Tesseract)
- Arabic + English support
- Full-text search in OpenSearch
- Highlight matched text
- Search by barcode
- Voice search
- Fuzzy search
- Filter by metadata

### ✅ Edit Request Workflow
- User requests edit with reason
- Manager receives real-time notification
- Approve/Reject with notes
- One-time unlock token (24h expiry)
- Upload new version
- Document locks again
- Old versions preserved

### ✅ Security & Permissions
- Department isolation (users see only their department)
- Confidentiality levels (Public, Internal, Confidential, Strict)
- Role-based access (User, Manager, Admin)
- JWT authentication
- Audit logging (every action logged)

### ✅ Bilingual Support
- Arabic (RTL) + English
- User language preference
- Translation files (ar.po, en_US.po)
- RTL-aware CSS

### ✅ Notifications
- Real-time via WebSocket
- Notification center
- Mark as read
- Triggers: upload, edit request, approval, new version

### ✅ Audit Trail
- Log everything: view, download, upload, edit, archive
- Track user, timestamp, IP, user-agent
- Metadata snapshots

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | Odoo 17+ (Python 3.11+) |
| **Database** | PostgreSQL 15+ |
| **ORM** | Odoo ORM |
| **API** | Custom REST Controllers (JSON) |
| **Authentication** | JWT (PyJWT) |
| **Background Jobs** | Odoo Queue Job + Redis |
| **OCR** | Tesseract (ara+eng) |
| **Search Engine** | OpenSearch 2.11+ |
| **File Storage** | Odoo filestore + organized structure |
| | |
| **Frontend Framework** | React 18+ |
| **Build Tool** | Vite |
| **Language** | TypeScript |
| **UI Library** | Material-UI (MUI) or Ant Design |
| **State Management** | Zustand or Redux Toolkit |
| **HTTP Client** | Axios |
| **i18n** | react-i18next |
| **PDF Viewer** | react-pdf (pdf.js) |
| **Barcode** | @zxing/library |
| **Voice Search** | Web Speech API |
| **Routing** | React Router v6 |
| **Styling** | Tailwind CSS + RTL |
| | |
| **Infrastructure** | Docker Compose |
| **Reverse Proxy** | Nginx |
| **Cache/Queue** | Redis |

---

## API Endpoints Overview

### Authentication
- `POST /api/auth/login` - Login with username/password → JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout

### Documents
- `GET /api/documents` - List documents (with filters, pagination)
- `GET /api/documents/:id` - Get document details
- `POST /api/documents/upload` - Upload new document
- `POST /api/documents/:id/versions/upload` - Upload new version (with unlock token)
- `GET /api/documents/:id/versions/:version_id/download` - Download version
- `PUT /api/documents/:id` - Update (tags only, by manager)
- `POST /api/documents/:id/archive` - Archive document

### Search
- `POST /api/search` - Full-text search with highlights
- `POST /api/search/barcode` - Search by barcode

### Edit Requests
- `GET /api/edit-requests` - List edit requests (for managers)
- `POST /api/edit-requests` - Create edit request
- `POST /api/edit-requests/:id/approve` - Approve (returns unlock token)
- `POST /api/edit-requests/:id/reject` - Reject

### Notifications
- `GET /api/notifications` - List notifications
- `PUT /api/notifications/:id/read` - Mark as read
- `PUT /api/notifications/read-all` - Mark all as read

### Admin
- `GET /api/departments` - List departments
- `GET /api/document-types` - List document types
- `GET /api/audit-logs` - View audit logs

### WebSocket
- `ws://localhost:8069/websocket?token=<jwt>` - Real-time notifications

---

## Docker Services

```yaml
services:
  postgres      # Port 5432 - Database
  redis         # Port 6379 - Queue/Cache
  opensearch    # Port 9200 - Search engine
  odoo          # Port 8069 - Backend API
  frontend      # Port 5173 - React app (dev)
  nginx         # Port 80/443 - Reverse proxy (prod)
```

---

## Project Structure

```
nbs-archive-system/
├── nbs_archive/                    # Odoo module (Backend)
│   ├── models/                     # Database models
│   ├── controllers/                # REST API
│   ├── services/                   # Business logic
│   ├── security/                   # Permissions
│   └── data/                       # Seed data
│
├── nbs-archive-frontend/           # React app (Frontend)
│   ├── src/
│   │   ├── api/                    # API client
│   │   ├── components/             # UI components
│   │   ├── pages/                  # Page components
│   │   ├── store/                  # State management
│   │   ├── hooks/                  # Custom hooks
│   │   ├── types/                  # TypeScript types
│   │   └── i18n/                   # Translations
│   ├── public/
│   │   └── locales/                # Translation files
│   ├── .env.development
│   └── package.json
│
├── docker-compose.yml              # All services
├── nginx.conf                      # Reverse proxy config
├── .env.example                    # Environment variables
├── README.md                       # Setup instructions
└── README_AR.md                    # Arabic instructions
```

---

## Implementation Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1: Backend Core** | 4-5 weeks | Models, Controllers, Security, Seed data |
| **Phase 2: Frontend Core** | 5-6 weeks | Pages, Components, API client, State mgmt |
| **Phase 3: Advanced Features** | 3-4 weeks | OCR, Search, Versioning, Notifications |
| **Phase 4: Testing & Docs** | 2-3 weeks | Testing, Documentation, Deployment |
| **Total** | **12-15 weeks** | Full production-ready system |

---

## Benefits of This Hybrid Approach

### ✅ Pros
1. **Best of both worlds**: Odoo's powerful backend + React's flexible frontend
2. **Full UI freedom**: Design any interface you want
3. **Easy future expansion**: Mobile apps, external integrations
4. **Modern dev experience**: Hot reload, TypeScript, modern tooling
5. **Team separation**: Backend team (Python) + Frontend team (React/TS)
6. **Performance**: Static frontend, API caching, CDN deployment

### ⚠️ Cons
1. **Two deployments**: Separate backend and frontend
2. **CORS setup**: Need to configure cross-origin requests
3. **JWT management**: Handle tokens, refresh, expiry
4. **API documentation**: Must maintain clear API contract

---

## Next Steps

### Ready to Start?

I will generate the complete codebase including:

1. **Odoo Module (Backend)**
   - All models with full business logic
   - All REST API controllers
   - JWT authentication service
   - OCR service (Tesseract integration)
   - OpenSearch service
   - Notification service
   - Security rules
   - Seed data (departments, document types, admin user)

2. **React Frontend**
   - Complete project setup (Vite + TypeScript)
   - All pages (Dashboard, Documents, Search, Edit Requests)
   - All components (Viewer, Scanner, Voice Search, Notifications)
   - API client with interceptors
   - State management (Zustand)
   - i18n configuration (Arabic RTL + English)
   - Tailwind CSS + custom styling

3. **Infrastructure**
   - Docker Compose with all services
   - Nginx reverse proxy configuration
   - Environment variables
   - Setup scripts

4. **Documentation**
   - README (English) with setup instructions
   - README_AR (Arabic) with setup instructions
   - API documentation
   - Troubleshooting guide

---

## Confirm to Proceed

**Type "START" or "ابدأ" to begin code generation!** 🚀

I will create all files in this repository and organize them properly.














