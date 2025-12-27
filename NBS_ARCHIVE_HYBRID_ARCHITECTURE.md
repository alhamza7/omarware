# NBS Archive System - Hybrid Architecture Plan
## Odoo Backend + Standalone React Frontend

---

## Executive Summary

Building the NBS Enterprise Archiving System with a **hybrid architecture**:

- **Backend**: Full Odoo module (business logic, ORM, security, workflows)
- **Frontend**: Completely independent React + Vite + TypeScript application
- **Integration**: RESTful API + WebSocket from Odoo to React
- **Authentication**: JWT tokens from Odoo backend
- **Flexibility**: Full control over UI/UX design while leveraging Odoo's powerful backend

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Port 5173)                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │          React + Vite + TypeScript                      │    │
│  │                                                          │    │
│  │  ├── Pages                                              │    │
│  │  │   ├── Dashboard                                      │    │
│  │  │   ├── Documents (List, Upload, View)                │    │
│  │  │   ├── Search (Advanced + Voice + Barcode)           │    │
│  │  │   ├── Edit Requests (Approval workflow)             │    │
│  │  │   └── Admin (Departments, Types)                    │    │
│  │                                                          │    │
│  │  ├── Components                                         │    │
│  │  │   ├── DocumentViewer (PDF.js)                       │    │
│  │  │   ├── BarcodeScanner (zxing)                        │    │
│  │  │   ├── VoiceSearch (Web Speech API)                  │    │
│  │  │   ├── NotificationCenter                            │    │
│  │  │   └── RTL Layout (Arabic support)                   │    │
│  │                                                          │    │
│  │  ├── API Client (axios + interceptors)                 │    │
│  │  ├── State Management (Zustand / Redux)                │    │
│  │  ├── i18n (Arabic RTL + English)                       │    │
│  │  └── UI Library (MUI / Ant Design / Custom)            │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API (JSON)
                              │ WebSocket (notifications)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (Port 8069)                         │
│                         Odoo Instance                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │          Custom Module: nbs_archive                     │    │
│  │                                                          │    │
│  │  ├── Models (Odoo ORM)                                 │    │
│  │  │   ├── nbs.department                                │    │
│  │  │   ├── nbs.document                                  │    │
│  │  │   ├── nbs.document.version                          │    │
│  │  │   ├── nbs.edit.request                              │    │
│  │  │   ├── nbs.audit.log                                 │    │
│  │  │   └── nbs.notification                              │    │
│  │                                                          │    │
│  │  ├── REST API Controllers                              │    │
│  │  │   ├── /api/auth (login, refresh, logout)           │    │
│  │  │   ├── /api/documents (CRUD)                         │    │
│  │  │   ├── /api/search (OpenSearch proxy)               │    │
│  │  │   ├── /api/upload (multipart)                       │    │
│  │  │   ├── /api/versions (list, download)               │    │
│  │  │   ├── /api/edit-requests (workflow)                │    │
│  │  │   ├── /api/notifications (list, mark read)         │    │
│  │  │   └── /api/audit-logs                              │    │
│  │                                                          │    │
│  │  ├── Business Logic (Services)                         │    │
│  │  │   ├── Document service                              │    │
│  │  │   ├── OCR service                                   │    │
│  │  │   ├── Search service                                │    │
│  │  │   └── Notification service                          │    │
│  │                                                          │    │
│  │  ├── Security & Permissions                            │    │
│  │  │   ├── JWT authentication                            │    │
│  │  │   ├── Department isolation                          │    │
│  │  │   ├── Confidentiality levels                        │    │
│  │  │   └── Role-based access                             │    │
│  │                                                          │    │
│  │  └── Background Jobs (Queue Job)                       │    │
│  │      ├── OCR processing                                │    │
│  │      └── OpenSearch indexing                           │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────┐        ┌─────────────┐      ┌──────────────┐
    │PostgreSQL│        │ OpenSearch  │      │    Redis     │
    │  (Odoo)  │        │   (Search)  │      │(Queue/Cache) │
    └──────────┘        └─────────────┘      └──────────────┘
```

---

## Technology Stack

### Backend (Odoo Module)
- **Framework**: Odoo 17+ (Python 3.11+)
- **ORM**: Odoo ORM
- **Database**: PostgreSQL 15+
- **API Framework**: Custom REST controllers (no external FastAPI)
- **Authentication**: JWT (PyJWT library)
- **Background Jobs**: Odoo Queue Job module
- **OCR**: Tesseract (subprocess)
- **Search**: OpenSearch client
- **File Storage**: Odoo filestore + organized structure

### Frontend (Independent React App)
- **Framework**: React 18+
- **Build Tool**: Vite
- **Language**: TypeScript
- **UI Library**: Material-UI (MUI) OR Ant Design (your choice)
- **State Management**: Zustand (lightweight) OR Redux Toolkit
- **HTTP Client**: Axios
- **i18n**: react-i18next
- **PDF Viewer**: react-pdf (pdf.js wrapper)
- **Barcode**: @zxing/library
- **Voice**: Web Speech API (native)
- **Charts**: Recharts / Chart.js
- **Forms**: React Hook Form + Zod validation
- **Router**: React Router v6
- **Styling**: Tailwind CSS + RTL support

### Infrastructure
- **Docker Compose**: All services
- **Reverse Proxy**: Nginx (frontend static + API proxy)
- **SSL**: Let's Encrypt (production)

---

## API Design

### Authentication Endpoints

#### POST /api/auth/login
```json
Request:
{
  "username": "admin",
  "password": "Admin123!"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 2,
    "name": "Admin User",
    "username": "admin",
    "email": "admin@nbs.com",
    "departments": [
      {"id": 1, "name": "Supply Chain", "role": "manager"},
      {"id": 2, "name": "Finance", "role": "user"}
    ],
    "language": "ar_SA",
    "is_admin": true
  }
}
```

#### POST /api/auth/refresh
```json
Request:
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST /api/auth/logout
```json
Request:
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
  "success": true
}
```

---

### Document Endpoints

#### GET /api/documents
```json
Query params:
?department_id=1
&document_type_id=2
&status=active
&page=1
&per_page=20
&sort_by=upload_date
&sort_order=desc

Response:
{
  "data": [
    {
      "id": 123,
      "name": "عقد توريد 2024",
      "barcode": "NBS000123",
      "department": {"id": 1, "name": "Supply Chain"},
      "document_type": {"id": 2, "name": "Contract"},
      "uploader": {"id": 5, "name": "John Doe"},
      "upload_date": "2024-12-17T10:30:00Z",
      "current_version": 2,
      "version_count": 2,
      "confidentiality_level": "internal",
      "status": "active",
      "tags": ["urgent", "supplier"],
      "po_number": "PO-2024-001",
      "ocr_status": "completed",
      "thumbnail_url": "/api/documents/123/thumbnail"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "total_pages": 8
  }
}
```

#### GET /api/documents/:id
```json
Response:
{
  "id": 123,
  "name": "عقد توريد 2024",
  "barcode": "NBS000123",
  "department": {"id": 1, "name": "Supply Chain", "code": "SC"},
  "document_type": {"id": 2, "name": "Contract", "code": "CONTRACT"},
  "uploader": {"id": 5, "name": "John Doe"},
  "upload_date": "2024-12-17T10:30:00Z",
  "current_version_id": 246,
  "versions": [
    {
      "id": 246,
      "version_number": 2,
      "file_name": "contract_v2.pdf",
      "file_size": 2048576,
      "file_type": "application/pdf",
      "upload_date": "2024-12-18T14:00:00Z",
      "uploader": {"id": 5, "name": "John Doe"},
      "notes": "Updated pricing section",
      "ocr_completed": true,
      "download_url": "/api/documents/123/versions/246/download"
    },
    {
      "id": 245,
      "version_number": 1,
      "file_name": "contract_v1.pdf",
      "file_size": 1987234,
      "upload_date": "2024-12-17T10:30:00Z",
      "download_url": "/api/documents/123/versions/245/download"
    }
  ],
  "tags": ["urgent", "supplier"],
  "po_number": "PO-2024-001",
  "bl_number": null,
  "container_number": null,
  "invoice_number": "INV-2024-056",
  "confidentiality_level": "internal",
  "status": "active",
  "is_locked": true,
  "unlock_token": null,
  "custom_fields": {
    "supplier_name": "ABC Company",
    "contract_value": "500000",
    "currency": "SAR"
  },
  "ocr_status": "completed",
  "can_request_edit": true,
  "can_archive": false,
  "edit_requests": [
    {
      "id": 45,
      "requester": {"id": 7, "name": "Jane Smith"},
      "request_date": "2024-12-18T09:00:00Z",
      "reason": "Need to update payment terms",
      "status": "approved",
      "approver": {"id": 3, "name": "Manager"},
      "approval_date": "2024-12-18T09:30:00Z"
    }
  ]
}
```

#### POST /api/documents/upload
```
Request: multipart/form-data
{
  file: <binary>,
  name: "عقد توريد 2024",
  department_id: 1,
  document_type_id: 2,
  confidentiality_level: "internal",
  tags: ["urgent", "supplier"],
  po_number: "PO-2024-001",
  custom_fields: {
    "supplier_name": "ABC Company",
    "contract_value": "500000"
  }
}

Response:
{
  "id": 123,
  "name": "عقد توريد 2024",
  "barcode": "NBS000123",
  "upload_date": "2024-12-17T10:30:00Z",
  "version_id": 245,
  "ocr_status": "pending"
}
```

#### POST /api/documents/:id/versions/upload
```
Request: multipart/form-data
{
  file: <binary>,
  unlock_token: "abc123xyz...",
  notes: "Updated pricing section"
}

Response:
{
  "version_id": 246,
  "version_number": 2,
  "upload_date": "2024-12-18T14:00:00Z"
}
```

#### GET /api/documents/:id/versions/:version_id/download
```
Response: Binary file stream
Headers:
  Content-Type: application/pdf
  Content-Disposition: attachment; filename="contract_v2.pdf"
```

#### GET /api/documents/:id/versions/:version_id/view
```
Response: Binary file stream (inline)
Headers:
  Content-Type: application/pdf
  Content-Disposition: inline
```

#### PUT /api/documents/:id
```json
Request (only tags editable by manager):
{
  "tags": ["urgent", "supplier", "reviewed"]
}

Response:
{
  "id": 123,
  "tags": ["urgent", "supplier", "reviewed"],
  "updated_at": "2024-12-18T15:00:00Z"
}
```

#### POST /api/documents/:id/archive
```json
Response:
{
  "id": 123,
  "status": "archived",
  "archived_at": "2024-12-18T15:30:00Z"
}
```

---

### Search Endpoints

#### POST /api/search
```json
Request:
{
  "query": "عقد توريد ABC",
  "filters": {
    "department_ids": [1, 2],
    "document_type_ids": [2],
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "confidentiality_levels": ["public", "internal"],
    "tags": ["urgent"]
  },
  "fuzzy": true,
  "page": 1,
  "per_page": 20
}

Response:
{
  "results": [
    {
      "document_id": 123,
      "title": "عقد توريد 2024",
      "barcode": "NBS000123",
      "score": 8.5,
      "highlights": {
        "title": ["<mark>عقد</mark> <mark>توريد</mark> 2024"],
        "content": [
          "نص العقد مع شركة <mark>ABC</mark> لتوريد المواد...",
          "...البند الثاني من <mark>العقد</mark> ينص على..."
        ],
        "pages": [
          {"page": 1, "snippet": "...شركة <mark>ABC</mark>..."},
          {"page": 3, "snippet": "...بموجب هذا <mark>العقد</mark>..."}
        ]
      },
      "department": "Supply Chain",
      "document_type": "Contract",
      "upload_date": "2024-12-17T10:30:00Z",
      "thumbnail_url": "/api/documents/123/thumbnail"
    }
  ],
  "pagination": {
    "total": 5,
    "page": 1,
    "per_page": 20
  },
  "took_ms": 45
}
```

#### POST /api/search/barcode
```json
Request:
{
  "barcode": "NBS000123"
}

Response:
{
  "found": true,
  "document": {
    "id": 123,
    "name": "عقد توريد 2024",
    "barcode": "NBS000123",
    ...
  }
}
```

---

### Edit Request Endpoints

#### POST /api/edit-requests
```json
Request:
{
  "document_id": 123,
  "reason": "Need to update payment terms"
}

Response:
{
  "id": 45,
  "document_id": 123,
  "requester": {"id": 7, "name": "Jane Smith"},
  "request_date": "2024-12-18T09:00:00Z",
  "reason": "Need to update payment terms",
  "status": "pending"
}
```

#### GET /api/edit-requests
```json
Query: ?status=pending&department_id=1

Response:
{
  "data": [
    {
      "id": 45,
      "document": {
        "id": 123,
        "name": "عقد توريد 2024",
        "barcode": "NBS000123"
      },
      "requester": {"id": 7, "name": "Jane Smith"},
      "request_date": "2024-12-18T09:00:00Z",
      "reason": "Need to update payment terms",
      "status": "pending"
    }
  ]
}
```

#### POST /api/edit-requests/:id/approve
```json
Request:
{
  "notes": "Approved for pricing update"
}

Response:
{
  "id": 45,
  "status": "approved",
  "approver": {"id": 3, "name": "Manager"},
  "approval_date": "2024-12-18T09:30:00Z",
  "unlock_token": "abc123xyz..."
}
```

#### POST /api/edit-requests/:id/reject
```json
Request:
{
  "notes": "Insufficient justification"
}

Response:
{
  "id": 45,
  "status": "rejected",
  "approver": {"id": 3, "name": "Manager"},
  "approval_date": "2024-12-18T09:30:00Z"
}
```

---

### Notification Endpoints

#### GET /api/notifications
```json
Query: ?unread_only=true&page=1&per_page=20

Response:
{
  "data": [
    {
      "id": 567,
      "title": "Edit Request Approved",
      "message": "Your edit request for 'عقد توريد 2024' has been approved",
      "type": "approval",
      "document_id": 123,
      "edit_request_id": 45,
      "is_read": false,
      "created_at": "2024-12-18T09:30:00Z"
    }
  ],
  "unread_count": 5,
  "pagination": {...}
}
```

#### PUT /api/notifications/:id/read
```json
Response:
{
  "id": 567,
  "is_read": true,
  "read_at": "2024-12-18T10:00:00Z"
}
```

#### PUT /api/notifications/read-all
```json
Response:
{
  "marked_read": 5
}
```

---

### WebSocket (Notifications)

```
Connection: ws://localhost:8069/websocket?token=<jwt_token>

Server -> Client messages:
{
  "type": "notification",
  "data": {
    "id": 567,
    "title": "New Document Uploaded",
    "message": "A new document has been uploaded to Supply Chain",
    "notification_type": "upload",
    "document_id": 124,
    "created_at": "2024-12-18T11:00:00Z"
  }
}

Client -> Server (heartbeat):
{
  "type": "ping"
}

Server -> Client (heartbeat response):
{
  "type": "pong"
}
```

---

### Admin Endpoints

#### GET /api/departments
```json
Response:
{
  "data": [
    {
      "id": 1,
      "name": "Supply Chain",
      "name_ar": "سلسلة التوريد",
      "code": "SC",
      "color": "#1976d2",
      "managers": [
        {"id": 3, "name": "Manager One"}
      ],
      "users": [
        {"id": 5, "name": "John Doe"},
        {"id": 7, "name": "Jane Smith"}
      ],
      "document_count": 150
    }
  ]
}
```

#### GET /api/document-types
```json
Query: ?department_id=1

Response:
{
  "data": [
    {
      "id": 2,
      "name": "Contract",
      "name_ar": "عقد",
      "code": "CONTRACT",
      "department_id": 1,
      "custom_fields": [
        {
          "name": "supplier_name",
          "type": "char",
          "label": "Supplier Name",
          "label_ar": "اسم المورد",
          "required": true
        },
        {
          "name": "contract_value",
          "type": "float",
          "label": "Contract Value",
          "label_ar": "قيمة العقد",
          "required": true
        }
      ]
    }
  ]
}
```

#### GET /api/audit-logs
```json
Query: ?document_id=123&action=download&date_from=2024-12-01

Response:
{
  "data": [
    {
      "id": 8901,
      "timestamp": "2024-12-18T10:15:00Z",
      "user": {"id": 7, "name": "Jane Smith"},
      "action": "download",
      "document": {"id": 123, "name": "عقد توريد 2024"},
      "department": {"id": 1, "name": "Supply Chain"},
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "details": {
        "version_id": 246,
        "version_number": 2
      }
    }
  ],
  "pagination": {...}
}
```

---

## Odoo Module Structure

```
nbs_archive/
├── __init__.py
├── __manifest__.py
│
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
│   └── res_users.py
│
├── controllers/
│   ├── __init__.py
│   ├── auth_controller.py          # JWT authentication
│   ├── document_controller.py      # Document CRUD
│   ├── search_controller.py        # Search API
│   ├── edit_request_controller.py  # Edit workflow
│   ├── notification_controller.py  # Notifications
│   ├── admin_controller.py         # Admin endpoints
│   └── websocket_controller.py     # WebSocket
│
├── services/
│   ├── __init__.py
│   ├── jwt_service.py              # JWT generation/validation
│   ├── document_service.py         # Business logic
│   ├── ocr_service.py              # OCR processing
│   ├── search_service.py           # OpenSearch integration
│   └── notification_service.py     # Notification sending
│
├── security/
│   ├── nbs_security.xml
│   ├── ir.model.access.csv
│   └── nbs_record_rules.xml
│
├── data/
│   ├── nbs_department_data.xml
│   ├── nbs_document_type_data.xml
│   └── ir_sequence_data.xml
│
├── static/
│   └── description/
│       ├── icon.png
│       └── index.html
│
├── i18n/
│   ├── ar.po
│   └── en_US.po
│
└── README.md
```

---

## React Frontend Structure

```
nbs-archive-frontend/
├── public/
│   ├── locales/
│   │   ├── ar/
│   │   │   └── translation.json
│   │   └── en/
│   │       └── translation.json
│   └── favicon.ico
│
├── src/
│   ├── api/
│   │   ├── client.ts                # Axios instance with interceptors
│   │   ├── auth.api.ts
│   │   ├── documents.api.ts
│   │   ├── search.api.ts
│   │   ├── editRequests.api.ts
│   │   ├── notifications.api.ts
│   │   └── admin.api.ts
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Footer.tsx
│   │   │
│   │   ├── documents/
│   │   │   ├── DocumentCard.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentViewer.tsx      # PDF viewer
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentMetadata.tsx
│   │   │   └── VersionHistory.tsx
│   │   │
│   │   ├── search/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── SearchFilters.tsx
│   │   │   ├── SearchResults.tsx
│   │   │   ├── BarcodeScanner.tsx
│   │   │   └── VoiceSearch.tsx
│   │   │
│   │   ├── editRequests/
│   │   │   ├── EditRequestForm.tsx
│   │   │   ├── EditRequestList.tsx
│   │   │   └── ApprovalDialog.tsx
│   │   │
│   │   ├── notifications/
│   │   │   ├── NotificationCenter.tsx
│   │   │   ├── NotificationItem.tsx
│   │   │   └── NotificationBadge.tsx
│   │   │
│   │   └── common/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       ├── Modal.tsx
│   │       ├── Table.tsx
│   │       ├── Spinner.tsx
│   │       └── RTLProvider.tsx
│   │
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── Login.tsx
│   │   │   └── ForgotPassword.tsx
│   │   │
│   │   ├── dashboard/
│   │   │   └── Dashboard.tsx
│   │   │
│   │   ├── documents/
│   │   │   ├── DocumentsPage.tsx
│   │   │   ├── DocumentDetailPage.tsx
│   │   │   └── DocumentUploadPage.tsx
│   │   │
│   │   ├── search/
│   │   │   └── SearchPage.tsx
│   │   │
│   │   ├── editRequests/
│   │   │   └── EditRequestsPage.tsx
│   │   │
│   │   └── admin/
│   │       ├── DepartmentsPage.tsx
│   │       ├── DocumentTypesPage.tsx
│   │       └── AuditLogsPage.tsx
│   │
│   ├── store/
│   │   ├── useAuthStore.ts
│   │   ├── useDocumentStore.ts
│   │   ├── useNotificationStore.ts
│   │   └── useSearchStore.ts
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useDocuments.ts
│   │   ├── useWebSocket.ts
│   │   ├── usePermissions.ts
│   │   └── useRTL.ts
│   │
│   ├── utils/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   └── constants.ts
│   │
│   ├── types/
│   │   ├── api.types.ts
│   │   ├── document.types.ts
│   │   ├── user.types.ts
│   │   └── notification.types.ts
│   │
│   ├── i18n/
│   │   └── config.ts
│   │
│   ├── styles/
│   │   ├── globals.css
│   │   ├── rtl.css
│   │   └── theme.ts
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
│
├── .env.example
├── .env.development
├── .env.production
├── .gitignore
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── README.md
```

---

## Authentication Flow

```
┌─────────┐                 ┌─────────┐                 ┌──────────┐
│ React   │                 │  Odoo   │                 │PostgreSQL│
│ Frontend│                 │ Backend │                 │          │
└────┬────┘                 └────┬────┘                 └────┬─────┘
     │                           │                           │
     │ POST /api/auth/login      │                           │
     │ {username, password}      │                           │
     ├──────────────────────────>│                           │
     │                           │                           │
     │                           │ Verify credentials        │
     │                           ├──────────────────────────>│
     │                           │                           │
     │                           │ User data                 │
     │                           │<──────────────────────────┤
     │                           │                           │
     │                           │ Generate JWT tokens       │
     │                           │ (access + refresh)        │
     │                           │                           │
     │ {access_token,            │                           │
     │  refresh_token,           │                           │
     │  user}                    │                           │
     │<──────────────────────────┤                           │
     │                           │                           │
     │ Store in memory/cookie    │                           │
     │                           │                           │
     │ GET /api/documents        │                           │
     │ Authorization: Bearer ... │                           │
     ├──────────────────────────>│                           │
     │                           │                           │
     │                           │ Validate JWT              │
     │                           │ Extract user_id           │
     │                           │                           │
     │                           │ Check permissions         │
     │                           │ Query documents           │
     │                           ├──────────────────────────>│
     │                           │                           │
     │ {documents: [...]}        │                           │
     │<──────────────────────────┤                           │
     │                           │                           │
     │ (Token expires)           │                           │
     │                           │                           │
     │ POST /api/auth/refresh    │                           │
     │ {refresh_token}           │                           │
     ├──────────────────────────>│                           │
     │                           │                           │
     │                           │ Validate refresh token    │
     │                           │ Generate new access token │
     │                           │                           │
     │ {access_token}            │                           │
     │<──────────────────────────┤                           │
     │                           │                           │
```

---

## CORS Configuration

In Odoo `odoo.conf`:
```ini
[options]
; Enable CORS for React frontend
proxy_mode = True

; Custom CORS headers (via controller)
```

In Odoo controller:
```python
# controllers/main.py
from odoo import http
from odoo.http import request

class NBSCORSController(http.Controller):
    
    def _set_cors_headers(self):
        """Set CORS headers for all API responses"""
        allowed_origins = [
            'http://localhost:5173',  # Development
            'https://archive.nbs.com'  # Production
        ]
        
        origin = request.httprequest.headers.get('Origin')
        if origin in allowed_origins:
            headers = {
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Max-Age': '3600'
            }
            return headers
        return {}
    
    @http.route('/api/<path:path>', type='http', auth='none', methods=['OPTIONS'], csrf=False)
    def preflight(self, **kw):
        """Handle CORS preflight requests"""
        headers = self._set_cors_headers()
        return request.make_response('', headers=headers)
```

---

## Docker Compose Setup

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
    networks:
      - nbs_network
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    networks:
      - nbs_network
    ports:
      - "6379:6379"

  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - DISABLE_SECURITY_PLUGIN=true
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    networks:
      - nbs_network
    ports:
      - "9200:9200"

  odoo:
    image: odoo:17.0
    depends_on:
      - postgres
      - redis
      - opensearch
    volumes:
      - ./nbs_archive:/mnt/extra-addons/nbs_archive
      - odoo_data:/var/lib/odoo
      - ./odoo.conf:/etc/odoo/odoo.conf
    environment:
      - HOST=postgres
      - USER=odoo_user
      - PASSWORD=root
    networks:
      - nbs_network
    ports:
      - "8069:8069"
    command: odoo --config=/etc/odoo/odoo.conf

  frontend:
    build:
      context: ./nbs-archive-frontend
      dockerfile: Dockerfile
    volumes:
      - ./nbs-archive-frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8069
      - VITE_WS_URL=ws://localhost:8069
    networks:
      - nbs_network
    ports:
      - "5173:5173"
    command: npm run dev

  nginx:
    image: nginx:alpine
    depends_on:
      - odoo
      - frontend
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - nbs_network
    ports:
      - "80:80"
      - "443:443"

volumes:
  postgres_data:
  opensearch_data:
  odoo_data:

networks:
  nbs_network:
    driver: bridge
```

---

## Environment Variables

### Frontend `.env.development`
```env
VITE_API_URL=http://localhost:8069
VITE_WS_URL=ws://localhost:8069/websocket
VITE_APP_NAME=NBS Archive
VITE_DEFAULT_LANGUAGE=ar
```

### Frontend `.env.production`
```env
VITE_API_URL=https://api.nbs-archive.com
VITE_WS_URL=wss://api.nbs-archive.com/websocket
VITE_APP_NAME=NBS Archive
VITE_DEFAULT_LANGUAGE=ar
```

---

## Benefits of This Architecture

### ✅ Advantages

1. **Best of Both Worlds**
   - Odoo's robust backend (ORM, security, business logic)
   - React's modern, flexible frontend

2. **Complete UI Freedom**
   - Design any UI/UX you want
   - Use any React library
   - No Odoo UI limitations

3. **Easy Future Expansion**
   - Add mobile app (React Native) using same API
   - Add external integrations easily
   - WhatsApp, mobile apps, etc.

4. **Modern Development Experience**
   - Hot reload in React
   - TypeScript type safety
   - Modern tooling (Vite, ESLint, Prettier)

5. **Team Separation**
   - Backend team works in Odoo (Python)
   - Frontend team works in React (TypeScript)
   - Clear API contract

6. **Performance**
   - Static frontend (fast loading)
   - API caching possible
   - CDN deployment for frontend

### ⚠️ Considerations

1. **Additional Complexity**
   - Two separate deployments
   - CORS configuration needed
   - JWT management

2. **Development Overhead**
   - Need to maintain API documentation
   - Frontend-backend coordination

3. **Deployment**
   - Two separate build processes
   - Need reverse proxy (Nginx)

---

## Next Steps

**Ready to proceed?** I will now generate the complete codebase:

1. ✅ Full Odoo module (Python)
2. ✅ Complete React frontend (TypeScript)
3. ✅ Docker Compose setup
4. ✅ Nginx configuration
5. ✅ Documentation (EN + AR)
6. ✅ Setup scripts

**Confirm to start implementation!** 🚀













