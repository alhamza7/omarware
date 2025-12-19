# نظام أرشفة نور النبراس - المعمار الهجين
## Backend في Odoo + Frontend مستقل بـ React

<div dir="rtl">

---

## الملخص التنفيذي

بناء نظام الأرشفة المؤسسي بمعمار **هجين مثالي**:

- **الخلفية (Backend)**: وحدة Odoo كاملة (منطق الأعمال، قاعدة البيانات، الأمان)
- **الواجهة (Frontend)**: تطبيق React مستقل تماماً (مرونة كاملة في التصميم)
- **التكامل**: REST API + WebSocket من Odoo إلى React
- **المصادقة**: JWT tokens من Odoo
- **المرونة**: تحكم كامل في UI/UX مع الاستفادة من قوة Odoo

---

## الهيكل المعماري

```
┌────────────────────────────────────────────────────┐
│           الواجهة الأمامية (Port 5173)             │
│                                                     │
│  React + Vite + TypeScript                         │
│  ├── صفحات (لوحة التحكم، المستندات، البحث)         │
│  ├── مكونات (عارض PDF، ماسح باركود، بحث صوتي)     │
│  ├── إدارة الحالة (Zustand/Redux)                 │
│  ├── واجهة برمجية (Axios)                          │
│  └── ثنائي اللغة (عربي RTL + إنجليزي)             │
└────────────────────────────────────────────────────┘
                    │
                    │ REST API (JSON)
                    │ WebSocket (إشعارات فورية)
                    ▼
┌────────────────────────────────────────────────────┐
│             الخلفية (Port 8069)                    │
│             نسخة Odoo + وحدة nbs_archive            │
│                                                     │
│  ├── Models (قاعدة البيانات)                       │
│  │   ├── الأقسام، المستندات، الإصدارات             │
│  │   ├── طلبات التعديل، الإشعارات                  │
│  │   └── سجل التدقيق                               │
│  │                                                  │
│  ├── REST API (واجهات برمجية)                      │
│  │   ├── /api/auth (تسجيل دخول، JWT)              │
│  │   ├── /api/documents (CRUD)                    │
│  │   ├── /api/search (بحث ذكي)                    │
│  │   ├── /api/upload (رفع ملفات)                  │
│  │   ├── /api/edit-requests (الموافقات)           │
│  │   └── /api/notifications (إشعارات)             │
│  │                                                  │
│  ├── Business Logic (منطق الأعمال)                │
│  │   ├── خدمة المستندات                            │
│  │   ├── خدمة OCR (التعرف الضوئي)                 │
│  │   ├── خدمة البحث (OpenSearch)                  │
│  │   └── خدمة الإشعارات                           │
│  │                                                  │
│  ├── Security (الأمان)                            │
│  │   ├── JWT authentication                       │
│  │   ├── عزل الأقسام                              │
│  │   ├── مستويات السرية                           │
│  │   └── صلاحيات حسب الدور                        │
│  │                                                  │
│  └── Background Jobs (مهام خلفية)                 │
│      ├── معالجة OCR                                │
│      └── الفهرسة في OpenSearch                     │
└────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    PostgreSQL    OpenSearch        Redis
```

---

## التقنيات المستخدمة

### الخلفية (Odoo Module)
- **الإطار**: Odoo 17+ (Python 3.11+)
- **قاعدة البيانات**: PostgreSQL 15+
- **API**: REST controllers مخصصة
- **المصادقة**: JWT (PyJWT)
- **المهام الخلفية**: Odoo Queue Job
- **التعرف الضوئي**: Tesseract
- **البحث**: OpenSearch

### الواجهة الأمامية (React App)
- **الإطار**: React 18+
- **أداة البناء**: Vite
- **اللغة**: TypeScript
- **مكتبة الواجهة**: Material-UI (MUI) أو Ant Design
- **إدارة الحالة**: Zustand أو Redux Toolkit
- **HTTP Client**: Axios
- **ثنائي اللغة**: react-i18next
- **عارض PDF**: react-pdf
- **الباركود**: @zxing/library
- **البحث الصوتي**: Web Speech API
- **التوجيه**: React Router v6
- **التنسيق**: Tailwind CSS + دعم RTL

---

## أمثلة على واجهات API

### تسجيل الدخول

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "Admin123!"
}
```

**الرد:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 2,
    "name": "مدير النظام",
    "username": "admin",
    "departments": [
      {"id": 1, "name": "سلسلة التوريد", "role": "manager"}
    ],
    "language": "ar_SA",
    "is_admin": true
  }
}
```

### قائمة المستندات

```http
GET /api/documents?department_id=1&page=1&per_page=20
Authorization: Bearer <access_token>
```

**الرد:**
```json
{
  "data": [
    {
      "id": 123,
      "name": "عقد توريد 2024",
      "barcode": "NBS000123",
      "department": {"id": 1, "name": "سلسلة التوريد"},
      "document_type": {"id": 2, "name": "عقد"},
      "uploader": {"id": 5, "name": "أحمد محمد"},
      "upload_date": "2024-12-17T10:30:00Z",
      "current_version": 2,
      "status": "active",
      "tags": ["عاجل", "موردين"],
      "po_number": "PO-2024-001"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 20
  }
}
```

### رفع مستند جديد

```http
POST /api/documents/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <binary>
name: "عقد توريد 2024"
department_id: 1
document_type_id: 2
confidentiality_level: "internal"
tags: ["عاجل", "موردين"]
po_number: "PO-2024-001"
```

**الرد:**
```json
{
  "id": 123,
  "name": "عقد توريد 2024",
  "barcode": "NBS000123",
  "upload_date": "2024-12-17T10:30:00Z",
  "version_id": 245,
  "ocr_status": "pending"
}
```

### البحث الذكي

```http
POST /api/search
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "query": "عقد توريد ABC",
  "filters": {
    "department_ids": [1, 2],
    "date_from": "2024-01-01"
  },
  "fuzzy": true,
  "page": 1
}
```

**الرد:**
```json
{
  "results": [
    {
      "document_id": 123,
      "title": "عقد توريد 2024",
      "score": 8.5,
      "highlights": {
        "title": ["<mark>عقد</mark> <mark>توريد</mark> 2024"],
        "content": [
          "نص العقد مع شركة <mark>ABC</mark> لتوريد المواد...",
          "...البند الثاني من <mark>العقد</mark>..."
        ],
        "pages": [
          {"page": 1, "snippet": "...شركة <mark>ABC</mark>..."},
          {"page": 3, "snippet": "...بموجب هذا <mark>العقد</mark>..."}
        ]
      },
      "department": "سلسلة التوريد",
      "upload_date": "2024-12-17T10:30:00Z"
    }
  ],
  "pagination": {"total": 5, "page": 1},
  "took_ms": 45
}
```

### طلب تعديل

```http
POST /api/edit-requests
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "document_id": 123,
  "reason": "تحديث شروط الدفع"
}
```

**الرد:**
```json
{
  "id": 45,
  "document_id": 123,
  "requester": {"id": 7, "name": "جين سميث"},
  "request_date": "2024-12-18T09:00:00Z",
  "reason": "تحديث شروط الدفع",
  "status": "pending"
}
```

### الموافقة على طلب تعديل

```http
POST /api/edit-requests/45/approve
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "notes": "موافق على التحديث"
}
```

**الرد:**
```json
{
  "id": 45,
  "status": "approved",
  "approver": {"id": 3, "name": "المدير"},
  "approval_date": "2024-12-18T09:30:00Z",
  "unlock_token": "abc123xyz..."
}
```

### الإشعارات

```http
GET /api/notifications?unread_only=true
Authorization: Bearer <access_token>
```

**الرد:**
```json
{
  "data": [
    {
      "id": 567,
      "title": "تمت الموافقة على طلب التعديل",
      "message": "تمت الموافقة على طلبك لتعديل 'عقد توريد 2024'",
      "type": "approval",
      "document_id": 123,
      "is_read": false,
      "created_at": "2024-12-18T09:30:00Z"
    }
  ],
  "unread_count": 5
}
```

---

## هيكل الملفات

### وحدة Odoo (Backend)

```
nbs_archive/
├── __init__.py
├── __manifest__.py
│
├── models/                    # نماذج قاعدة البيانات
│   ├── nbs_department.py
│   ├── nbs_document.py
│   ├── nbs_document_version.py
│   ├── nbs_edit_request.py
│   ├── nbs_audit_log.py
│   └── nbs_notification.py
│
├── controllers/               # واجهات API
│   ├── auth_controller.py     # JWT
│   ├── document_controller.py # المستندات
│   ├── search_controller.py   # البحث
│   └── websocket_controller.py # WebSocket
│
├── services/                  # الخدمات
│   ├── jwt_service.py
│   ├── ocr_service.py
│   ├── search_service.py
│   └── notification_service.py
│
├── security/                  # الصلاحيات
│   ├── nbs_security.xml
│   └── ir.model.access.csv
│
└── data/                      # بيانات أولية
    ├── nbs_department_data.xml
    └── nbs_document_type_data.xml
```

### تطبيق React (Frontend)

```
nbs-archive-frontend/
├── src/
│   ├── api/                   # واجهات API
│   │   ├── client.ts
│   │   ├── auth.api.ts
│   │   ├── documents.api.ts
│   │   └── search.api.ts
│   │
│   ├── components/            # المكونات
│   │   ├── layout/
│   │   ├── documents/
│   │   │   ├── DocumentViewer.tsx
│   │   │   ├── DocumentUpload.tsx
│   │   │   └── VersionHistory.tsx
│   │   ├── search/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── BarcodeScanner.tsx
│   │   │   └── VoiceSearch.tsx
│   │   └── notifications/
│   │
│   ├── pages/                 # الصفحات
│   │   ├── auth/
│   │   │   └── Login.tsx
│   │   ├── dashboard/
│   │   │   └── Dashboard.tsx
│   │   ├── documents/
│   │   │   ├── DocumentsPage.tsx
│   │   │   └── DocumentDetailPage.tsx
│   │   └── search/
│   │       └── SearchPage.tsx
│   │
│   ├── store/                 # إدارة الحالة
│   │   ├── useAuthStore.ts
│   │   ├── useDocumentStore.ts
│   │   └── useNotificationStore.ts
│   │
│   ├── hooks/                 # Custom Hooks
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   └── useRTL.ts
│   │
│   ├── types/                 # أنواع TypeScript
│   ├── i18n/                  # الترجمات
│   └── styles/                # التنسيقات
│
├── public/
│   └── locales/
│       ├── ar/translation.json
│       └── en/translation.json
│
├── .env.development
├── .env.production
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## سير العمل - المصادقة

1. المستخدم يدخل username + password في React
2. React يرسل POST /api/auth/login إلى Odoo
3. Odoo يتحقق من البيانات في PostgreSQL
4. Odoo يولد JWT tokens (access + refresh)
5. React يحفظ الـ tokens (memory أو cookie)
6. React يرفق access_token في كل طلب API
7. Odoo يتحقق من الـ token ويرجع البيانات
8. عند انتهاء الـ token، React يطلب token جديد بـ refresh_token

---

## إعداد CORS

لكي يتواصل React (localhost:5173) مع Odoo (localhost:8069)، نحتاج إعداد CORS:

**في Odoo Controller:**
```python
def _set_cors_headers(self):
    allowed_origins = [
        'http://localhost:5173',      # تطوير
        'https://archive.nbs.com'     # إنتاج
    ]
    
    origin = request.httprequest.headers.get('Origin')
    if origin in allowed_origins:
        return {
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Credentials': 'true'
        }
    return {}
```

---

## Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    # ... إعدادات PostgreSQL

  redis:
    image: redis:7-alpine
    # ... إعدادات Redis

  opensearch:
    image: opensearchproject/opensearch:2.11.0
    # ... إعدادات OpenSearch

  odoo:
    image: odoo:17.0
    volumes:
      - ./nbs_archive:/mnt/extra-addons/nbs_archive
    ports:
      - "8069:8069"
    # ... إعدادات Odoo

  frontend:
    build: ./nbs-archive-frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8069
    # ... إعدادات React

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    # ... إعدادات Nginx (reverse proxy)
```

---

## المزايا الرئيسية

### ✅ الفوائد

1. **الأفضل من كلا العالمين**
   - قوة Odoo في الخلفية (ORM، أمان، منطق أعمال)
   - مرونة React في الواجهة (UI/UX حديث)

2. **حرية كاملة في التصميم**
   - صمم أي واجهة تريدها
   - استخدم أي مكتبة React
   - لا قيود من Odoo UI

3. **سهولة التوسع المستقبلي**
   - إضافة تطبيق موبايل (React Native) بنفس API
   - تكامل مع أنظمة خارجية بسهولة
   - WhatsApp، تطبيقات موبايل، إلخ

4. **تجربة تطوير حديثة**
   - Hot reload في React (تحديث فوري)
   - TypeScript type safety
   - أدوات حديثة (Vite، ESLint، Prettier)

5. **فصل الفرق**
   - فريق الخلفية يعمل في Odoo (Python)
   - فريق الواجهة يعمل في React (TypeScript)
   - عقد API واضح بينهما

6. **الأداء**
   - واجهة ثابتة (تحميل سريع)
   - إمكانية التخزين المؤقت
   - نشر Frontend على CDN

### ⚠️ اعتبارات

1. **تعقيد إضافي**
   - نشر منفصل للخلفية والواجهة
   - إعداد CORS مطلوب
   - إدارة JWT

2. **عبء التطوير**
   - حاجة لتوثيق API
   - تنسيق بين الفرق

3. **النشر**
   - عمليتي بناء منفصلتين
   - حاجة لـ reverse proxy (Nginx)

---

## الخطوات التالية

**جاهز للبدء؟** سأقوم الآن بتوليد الكود الكامل:

### المرحلة 1: وحدة Odoo (Backend)
1. ✅ Models (قاعدة البيانات)
2. ✅ Controllers (REST API)
3. ✅ Services (منطق الأعمال)
4. ✅ Security (الصلاحيات)
5. ✅ Data (البيانات الأولية)
6. ✅ Background Jobs (OCR, Indexing)

### المرحلة 2: تطبيق React (Frontend)
1. ✅ Project Setup (Vite + TypeScript)
2. ✅ API Client (Axios + Interceptors)
3. ✅ Authentication (Login, JWT)
4. ✅ Components (Viewer, Scanner, Voice)
5. ✅ Pages (Dashboard, Documents, Search)
6. ✅ i18n (Arabic RTL + English)
7. ✅ State Management
8. ✅ WebSocket Integration

### المرحلة 3: البنية التحتية
1. ✅ Docker Compose
2. ✅ Nginx Configuration
3. ✅ Environment Variables
4. ✅ Setup Scripts

### المرحلة 4: التوثيق
1. ✅ README (English)
2. ✅ README_AR (Arabic)
3. ✅ API Documentation
4. ✅ Development Guide
5. ✅ Deployment Guide

---

## التقدير الزمني

- **المرحلة 1 (Backend)**: 4-5 أسابيع
- **المرحلة 2 (Frontend)**: 5-6 أسابيع
- **المرحلة 3 (Infrastructure)**: 1 أسبوع
- **المرحلة 4 (Testing + Docs)**: 2-3 أسابيع

**المجموع: 12-15 أسبوع**

---

## تأكيد البدء 🚀

**هل أنت جاهز لبدء التنفيذ؟**

سأقوم بتوليد:
- ✅ كامل كود وحدة Odoo (Python)
- ✅ كامل كود تطبيق React (TypeScript)
- ✅ إعدادات Docker Compose
- ✅ ملفات الإعداد
- ✅ التوثيق الكامل

**اكتب "ابدأ" للبدء!** 💪

</div>



