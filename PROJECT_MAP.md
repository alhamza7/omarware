# NBS / Lugal ERP — Project Map
> آخر تحديث: مارس 2026  
> المشروع: نظام ERP متكامل مبني على Odoo 19 + React frontends

---

## فهرس المحتويات

1. [نظرة عامة على المشروع](#1-نظرة-عامة)
2. [خريطة الـ Repos المقترحة على GitHub](#2-خريطة-repos-github)
3. [Backend — موديولات Odoo المخصصة](#3-backend--موديولات-odoo)
4. [Frontend — تطبيقات React](#4-frontend--تطبيقات-react)
5. [البنية التحتية](#5-infrastructure)
6. [خريطة التبعيات (Dependency Map)](#6-dependency-map)
7. [توزيع الفرق والصلاحيات](#7-teams--permissions)
8. [APIs الرئيسية](#8-apis)
9. [Third-Party Modules](#9-third-party-modules)

---

## 1. نظرة عامة

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NBS Lugal ERP System                           │
│                                                                     │
│  Backend: Odoo 19.0 (Python)        Server: Ubuntu Linux            │
│  Database: PostgreSQL               Port: 8070                      │
│  Workers: 9                         RAM: 62 GB  /  CPUs: 28         │
│  DB Name: lugal_local               version_info: (19,0,0,final,0)  │
├─────────────────────────────────────────────────────────────────────┤
│  Custom Modules : 16                                                │
│  Frontend Apps  : 3  (CRM, Inventory, POS, Email)                  │
│  REST API Routes: 150+ endpoints                                    │
│  Total Py Files : ~430 files                                        │
│  Total XML Files: ~150 files                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. خريطة Repos GitHub

```
NBS-ORG (GitHub Organization)
│
├── 🗂️  lugal-addons          ← Umbrella repo (submodules فقط — لا كود)
│
│── ═══════════ Backend Module Repos ═══════════
│
├── 📦  module-auth            layer-0 | 10 py files  | no custom deps
├── 📦  module-sap             layer-0 | 94 py files  | no custom deps
├── 📦  module-archive         layer-0 | 63 py files  | no custom deps
├── 📦  module-supply          layer-0 |  5 py files  | no custom deps
├── 📦  module-whatsapp        layer-0 |  5 py files  | no custom deps
├── 📦  module-fragrantica     layer-0 | 15 py files  | no custom deps
├── 📦  module-ai              layer-0 | 13 py files  | no custom deps
├── 📦  module-showcase        layer-0 | 10 py files  | no custom deps
├── 📦  module-pricelist       layer-0 |  7 py files  | no custom deps
│
├── 📦  module-email           layer-1 |  7 py files  | ← auth
├── 📦  module-inventory       layer-1 | 16 py files  | ← sap
├── 📦  module-label-designer  layer-1 | 23 py files  | ← sap
├── 📦  module-invoice-design  layer-1 |  8 py files  | (none custom)
│
├── 📦  module-pos             layer-2 | 21 py files  | ← sap, whatsapp
│
├── 📦  module-crm             layer-2 | 51 py files  | ← auth, email, supply
│
├── 📦  module-repzo           layer-3 | 15 py files  | ← auth, crm
│
│── ═══════════ Frontend App Repos ═══════════
│
├── 💻  app-crm                React + TypeScript | 54 tsx/ts files
├── 💻  app-email              React + TypeScript | 15 tsx/ts files
├── 💻  app-inventory          React + TypeScript | 80 tsx/ts files
├── 💻  app-pos                React + TypeScript | POS interface
│
│── ═══════════ Infrastructure ═══════════
│
└── 🐳  lugal-infra            docker + nginx + scripts + configs
```

---

## 3. Backend — موديولات Odoo المخصصة

### ━━━ LAYER 0 — Foundation (لا تعتمد على أي موديول منا) ━━━

---

#### `lugal_auth` → **module-auth**

| | |
|--|--|
| **الوصف** | خدمة JWT مركزية — كل موديول يحتاج مصادقة يعتمد على هذا فقط |
| **الملفات** | 10 Python · 1 XML |
| **Models** | `lugal_jwt_service` · `lugal_jwt_blacklist` · `lugal_auth_rate_limit` |
| **Controllers** | `auth_controller` (login/refresh/logout) · `_auth` (helper) |
| **API Routes** | `POST /lugal/auth/login` · `POST /lugal/auth/refresh` · `POST /lugal/auth/logout` |
| **External Deps** | `PyJWT` |
| **Custom Deps** | ❌ none |
| **الفريق** | Auth & Security |

---

#### `sap_integration` → **module-sap**

| | |
|--|--|
| **الوصف** | تكامل كامل مع SAP (منتجات، عملاء، طلبات) |
| **الملفات** | 94 Python · 50 XML — **أكبر موديول في المشروع** |
| **Models** | 42 ملف نموذج (sap_product, sap_order, sap_barcode...) |
| **Controllers** | لا controllers HTTP مباشرة — يُستهلك من موديولات أخرى |
| **External Deps** | `requests` · `cachetools` |
| **Custom Deps** | ❌ none |
| **الفريق** | SAP Integration Team |

---

#### `nbs_archive` → **module-archive**

| | |
|--|--|
| **الوصف** | نظام أرشفة وثائق متكامل (departments, versions, OCR, workflows) |
| **الملفات** | 63 Python · 16 XML |
| **Models** | document · folder · department · version · audit · workflow · notification · signature · OCR |
| **Controllers** | 26 controller (document, folder, search, OCR, signature, websocket...) |
| **API Routes** | `/api/nbs/*` — أكثر من 60 endpoint |
| **External Deps** | `opensearch-py` · `PyJWT` · `requests` |
| **Custom Deps** | ❌ none |
| **الفريق** | Archive Team |

---

#### `lugal_supply` → **module-supply**

| | |
|--|--|
| **الوصف** | موردون وحاويات (containers & vendors) |
| **الملفات** | 5 Python · 0 XML |
| **Models** | `lugal_supply_container` · `lugal_supply_vendor` |
| **Controllers** | ❌ none (يُستهلك عبر CRM API) |
| **Custom Deps** | ❌ none |
| **الفريق** | Supply Team |

---

#### `ultramsg_integration` → **module-whatsapp**

| | |
|--|--|
| **الوصف** | إرسال رسائل WhatsApp عبر UltraMsg API |
| **الملفات** | 5 Python · 2 XML · 1 JS |
| **Models** | `ultramsg_config` · `ultramsg_message` |
| **API** | يُستدعى من pos_perfume_custom لإرسال الفواتير |
| **External Deps** | `requests` |
| **Custom Deps** | ❌ none |
| **الفريق** | POS Team |

---

#### `lugal_fragrantica` → **module-fragrantica**

| | |
|--|--|
| **الوصف** | ربط المنتجات مع قاعدة بيانات Fragrantica (49,000+ عطر) |
| **الملفات** | 15 Python · 6 XML · 1 CSS |
| **Models** | `fragrantica_perfume` · `fragrantica_note` · `fragrantica_accord` · `fragrantica_pending_request` |
| **Custom Deps** | ❌ none |
| **الفريق** | Fragrantica Team |

---

#### `lugal_ai` → **module-ai**

| | |
|--|--|
| **الوصف** | طبقة AI باستخدام Gemini API — بحث المنتجات، محادثات، KPIs |
| **الملفات** | 13 Python · 9 XML · 3 JS |
| **Models** | `lugal_config` · `lugal_conversation` · `lugal_cache` · `lugal_question_index` |
| **Controllers** | `chat_controller` · `product_search` · `public_product_api` · `gemini_api` |
| **Custom Deps** | ❌ none |
| **الفريق** | AI Team |

---

#### `perfume_showcase_api` → **module-showcase**

| | |
|--|--|
| **الوصف** | API لموقع عرض العطور العام (brands, perfumes, notes, tags) |
| **الملفات** | 10 Python · 5 XML |
| **Models** | `perfume_brand` · `perfume_perfume` · `perfume_note` · `perfume_tag` |
| **Controllers** | `perfume_api_controller` |
| **Custom Deps** | ❌ none |
| **الفريق** | Showcase Team |

---

#### `custom_pricelist_packaging` → **module-pricelist**

| | |
|--|--|
| **الوصف** | دعم التسعير بالتعبئة (packaging-based pricing) في قوائم الأسعار |
| **الملفات** | 7 Python · 1 XML |
| **Models** | `product_pricelist_item` (extend) · `sale_order_line` (extend) |
| **Custom Deps** | ❌ none |
| **الفريق** | POS / Sales Team |

---

### ━━━ LAYER 1 — يعتمد على Layer 0 ━━━

---

#### `lugal_email` → **module-email**

| | |
|--|--|
| **الوصف** | نظام بريد إلكتروني متكامل (IMAP/SMTP) — حسابات متعددة لكل موظف |
| **الملفات** | 7 Python · 4 XML |
| **Models** | `lugal_email_account` · `lugal_email_message` |
| **Controllers** | `email_controller` (REST API كامل) |
| **API Routes** | `GET/POST /api/lugal/email/accounts` · `/messages` · `/send` · `/notifications` |
| **Odoo Views** | قائمة + نموذج إضافة حسابات البريد في Odoo UI |
| **Security** | `group_email_user` · `group_email_admin` + row-level rules |
| **Custom Deps** | `lugal_auth` |
| **Extended by** | `lugal_crm` (يضيف حقول customer/ticket) |
| **الفريق** | Email Team |

---

#### `lugal_inventory` → **module-inventory**

| | |
|--|--|
| **الوصف** | جلسات جرد المخزون مع API للموبايل والويب |
| **الملفات** | 16 Python · 4 XML |
| **Models** | `inventory_session` · `inventory_audit` · `inventory_user` |
| **Controllers** | `api/items` · `api/barcodes` · `api/warehouses` · `api/users` · `api/search` · `api/audits` |
| **API Routes** | `/api/lugal/inventory/*` |
| **Custom Deps** | `sap_integration` |
| **الفريق** | Inventory Team |

---

#### `product_label_designer` → **module-label-designer**

| | |
|--|--|
| **الوصف** | تصميم وطباعة ملصقات المنتجات مع دعم الباركود وSAP |
| **الملفات** | 23 Python · 20 XML · 4 JS |
| **Models** | `product_label` · `customer_label` · `product_barcode_alternative` |
| **Controllers** | `label_designer` |
| **Custom Deps** | `sap_integration` |
| **الفريق** | Label Design Team |

---

#### `invoice_designer` → **module-invoice-design**

| | |
|--|--|
| **الوصف** | مصمم فواتير بصري drag & drop |
| **الملفات** | 8 Python · 5 XML · 1 JS |
| **Models** | `invoice_template_designer` · `invoice_template_element` · `sale_order_integration` |
| **Custom Deps** | ❌ none |
| **الفريق** | Invoice Design Team |

---

### ━━━ LAYER 2 — يعتمد على Layer 0 + 1 ━━━

---

#### `pos_perfume_custom` → **module-pos**

| | |
|--|--|
| **الوصف** | واجهة POS كاملة للعطور مع REST API خارجي شامل |
| **الملفات** | 21 Python · 22 XML · 11 JS · 2 SCSS — **أكبر frontend module** |
| **Models** | `pos_perfume_order` · `pos_perfume_order_line` · `pos_perfume_settings` · `product_extended` |
| **Controllers** | `api/products` · `api/orders` · `api/customers` · `api/auth` · `api/order_actions` |
| **API Routes** | `GET /api/pos_perfume/v1/products` · `/orders` · `/customers` · `/categories` |
| **UoM Filter** | `?uom=kg` (id=34) · `?uom=quarter` (id=33) |
| **Custom Deps** | `sap_integration` · `ultramsg_integration` |
| **الفريق** | POS Team |

---

#### `lugal_crm` → **module-crm**

| | |
|--|--|
| **الوصف** | نظام CRM كامل: عملاء 360°، تذاكر، تفاعلات، KPIs، مشتريات |
| **الملفات** | 51 Python · 3 XML |
| **Models** | customer · ticket · interaction · call · task · attendance · branch · shift · tag · kb_article · supply_po · employee_kpi · omnichannel · partner_extension · email_extension |
| **Controllers** | 23 controller (customer, ticket, call, supply, analytics, knowledge, branch, channel, delivery, qa, workforce, pos_bridge, upload, task...) |
| **API Routes** | `/api/lugal/crm/*` — أكثر من 80 endpoint |
| **Custom Deps** | `lugal_auth` · `lugal_email` · `lugal_supply` |
| **الفريق** | CRM Team |

---

### ━━━ LAYER 3 — يعتمد على Layer 0 + 1 + 2 ━━━

---

#### `repzo_integration` → **module-repzo**

| | |
|--|--|
| **الوصف** | تكامل مع منصة Repzo لفرق المبيعات الميداني |
| **الملفات** | 15 Python · 7 XML |
| **Models** | `repzo_backend` · `repzo_sync_log` · `repzo_client_mapping` · `repzo_order_mapping` |
| **Controllers** | `repzo_webhook_controller` · `repzo_cron_controller` |
| **API Routes** | `/api/repzo/*` (webhook receiver) |
| **Features** | مزامنة customers ↔ clients · products · orders · invoices · payments |
| **Custom Deps** | `lugal_auth` · `lugal_crm` |
| **الفريق** | Repzo Integration Team |

---

## 4. Frontend — تطبيقات React

### `crm-email` → **app-email**

| | |
|--|--|
| **الوصف** | تطبيق البريد الإلكتروني المدمج مع CRM |
| **التقنيات** | React 18 · TypeScript · Vite 6 · Zustand · Tailwind · Radix UI · Sonner |
| **الملفات** | 8 TSX · 7 TS = 15 ملف |
| **API** | `/api/lugal/email/*` |
| **الصفحات** | InboxPage · EmailDetailPage · ComposePage |
| **الـ Hooks** | `useEmailSync` · `useEmailForRecord` · `useEmailNotifications` |
| **الـ Store** | `emailStore` (Zustand) |

---

### `inv-front` → **app-inventory**

| | |
|--|--|
| **الوصف** | لوحة تحكم المخزون مع admin panel |
| **التقنيات** | React 18 · TypeScript · Vite 6 · MUI · Tailwind · react-router 7 · axios |
| **الملفات** | 67 TSX · 13 TS = 80 ملف |
| **API** | `/api/lugal/inventory/*` |
| **الصفحات** | Login · InventorySearch · WarehouseSelect · Reports · AdminDashboard |
| **Services** | authService · inventoryService · warehouseService · adminService |

---

### `44` → **app-pos**

| | |
|--|--|
| **الوصف** | واجهة POS العطور |
| **التقنيات** | React · TypeScript · Vite |
| **API** | `/api/pos_perfume/v1/*` |
| **Services** | `posPerfumeApi` |

---

### `crm-frontend` → **app-crm**

> نظام CRM الرئيسي (الواجهة الأمامية) — مرتبط بـ `/api/lugal/crm/*`

---

## 5. Infrastructure

### Odoo Server

```ini
[odoo_local.conf]
addons_path     = addons, odoo/addons
db_name         = lugal_local
db_user         = capo7amzah
http_port       = 8070
longpolling_port= 8072
workers         = 9
limit_memory_soft = 8 GB
limit_memory_hard = 10 GB
limit_time_real   = 1200000 s
data_dir        = ./filestore_local
server_wide_modules = base, web, nbs_archive
```

### Docker (Production Setup)

```yaml
services:
  postgres:    image: postgres:15
  redis:       image: redis:7-alpine
  opensearch:  image: opensearchproject/opensearch:2.11.0
  odoo:        image: odoo:19.0  (port 8069/8072)
  frontend:    build: ./nbs-archive-frontend
  nginx:       (reverse proxy)
```

### Python Dependencies الرئيسية

```
PyJWT          — lugal_auth + nbs_archive
opensearch-py  — nbs_archive (full-text search)
requests       — sap_integration + repzo + ultramsg
cachetools     — sap_integration
Pillow         — label designer + reports
lxml           — XML/HTML processing
psycopg2       — PostgreSQL
```

---

## 6. Dependency Map

```
                    ┌─────────────┐
                    │ lugal_auth  │  LAYER 0 (Foundation)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
       ┌────────────┐ ┌──────────┐ ┌──────────┐
       │lugal_email │ │lugal_crm │ │  repzo   │ LAYER 1/2/3
       └──────┬─────┘ └────┬─────┘ └──────────┘
              │             │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │  lugal_crm  │  LAYER 2
              └─────────────┘
                     ▲
              ┌──────┘
              │
       ┌──────────────┐
       │   repzo_int. │  LAYER 3
       └──────────────┘

──────────────────────────────────────────────────

  sap_integration  ──► lugal_inventory
                   ──► pos_perfume_custom
                   ──► product_label_designer

  lugal_supply     ──► lugal_crm

  ultramsg_integ.  ──► pos_perfume_custom

──────────────────────────────────────────────────

STANDALONE (no custom deps):
  nbs_archive · lugal_fragrantica · lugal_ai
  perfume_showcase_api · invoice_designer
  custom_pricelist_packaging
```

---

## 7. Teams & Permissions

```
┌─────────────────────┬───────────────────────────────────────────────┐
│  الفريق / الشخص     │  يملك صلاحية على هذه الـ Repos               │
├─────────────────────┼───────────────────────────────────────────────┤
│  Tech Lead          │  كل شيء ✅                                     │
│  DevOps             │  lugal-addons (umbrella) + lugal-infra        │
├─────────────────────┼───────────────────────────────────────────────┤
│  Auth & Security    │  module-auth                                  │
│  SAP Team           │  module-sap                                   │
│  Archive Team       │  module-archive                               │
│  CRM Team           │  module-crm + app-crm                         │
│  Email Team         │  module-email + app-email                     │
│  POS Team           │  module-pos + module-whatsapp + app-pos       │
│  Inventory Team     │  module-inventory + app-inventory             │
│  Supply Team        │  module-supply                                │
│  Repzo Team         │  module-repzo                                 │
│  AI Team            │  module-ai                                    │
│  Fragrantica Team   │  module-fragrantica                           │
│  Design Team        │  module-label-designer + module-invoice-design│
│  Showcase Team      │  module-showcase                              │
└─────────────────────┴───────────────────────────────────────────────┘
```

---

## 8. APIs

### Base URLs

| النظام | Base URL |
|--------|----------|
| Auth | `/lugal/auth/` |
| CRM | `/api/lugal/crm/` |
| Email | `/api/lugal/email/` |
| Inventory | `/api/lugal/inventory/` |
| POS | `/api/pos_perfume/v1/` |
| Archive | `/api/nbs/` |

### POS Products API — أمثلة

```
GET /api/pos_perfume/v1/products
    ?query=rose
    &limit=20
    &offset=0
    &pricelist_id=1
    &categ_id=8
    &uom=kg           ← NEW: filter by UoM (kg | quarter)
    &brand=givaudan
    &has_price_only=1
```

### Email API — Endpoints

```
GET    /api/lugal/email/accounts              ← قائمة حسابات المستخدم
POST   /api/lugal/email/accounts              ← إضافة حساب جديد
PATCH  /api/lugal/email/accounts/<id>         ← تعديل حساب
DELETE /api/lugal/email/accounts/<id>         ← حذف حساب
POST   /api/lugal/email/accounts/<id>/test    ← اختبار الاتصال
POST   /api/lugal/email/accounts/<id>/sync    ← مزامنة IMAP
POST   /api/lugal/email/accounts/<id>/set_default
GET    /api/lugal/email/messages              ← قائمة الرسائل
GET    /api/lugal/email/messages/<id>         ← تفاصيل رسالة
POST   /api/lugal/email/send                  ← إرسال بريد
POST   /api/lugal/email/messages/<id>/reply
POST   /api/lugal/email/messages/<id>/forward
POST   /api/lugal/email/messages/<id>/archive
POST   /api/lugal/email/messages/<id>/link    ← ربط بسجل CRM
GET    /api/lugal/email/notifications         ← عدد غير المقروء
```

### Auth API

```
POST /lugal/auth/login    → { access_token, refresh_token }
POST /lugal/auth/refresh  → { access_token }
POST /lugal/auth/logout   → revoke token
```

---

## 9. Third-Party Modules

| الموديول | المصدر | الوصف | الحالة |
|----------|--------|-------|--------|
| `muk_web_theme` + 5 | **MuK IT** | ثيم Odoo Backend | مشترى |
| `code_backend_theme` | **Cybrosys** | ثيم إضافي | مشترى |
| `invoice_design` | **Cybrosys** | تصميم فواتير جاهز | مشترى |
| `uom_in_pricelist` | **Cybrosys** | UoM في قوائم الأسعار | مشترى |
| `hrms_dashboard` | **OpenHRMS** | لوحة الموارد البشرية | مجتمع |
| `hr_*` (OpenHRMS) | **Cybrosys/OpenHRMS** | حزمة HR كاملة | مجتمع |
| `connector` / `connector-17.0` | **OCA** | إطار التكاملات | مجتمع |
| `svn_orbitpdf` | **Sveltware** | محرك PDF | مشترى |
| `ohrms_*` | **Cybrosys/OpenHRMS** | رواتب، قروض، سلف | مجتمع |

---

## الإحصائيات الإجمالية

| | العدد |
|-|-------|
| موديولات Odoo مخصصة (بنيناها) | **16** |
| موديولات Third-Party | **~25** |
| موديولات Odoo الرسمية | **~350+** |
| ملفات Python (custom) | **~430** |
| ملفات XML (custom) | **~150** |
| تطبيقات Frontend | **4** |
| ملفات TypeScript/TSX | **~100** |
| API Endpoints | **150+** |
| Repos مقترحة على GitHub | **22** |

---

*تم توليد هذا الملف بواسطة Cursor AI — مارس 2026*
