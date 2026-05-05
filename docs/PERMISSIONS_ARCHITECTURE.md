# نظام الصلاحيات — Permission System Architecture
## Lugal ERP — Complete Reference

---

## 1. بنية النظام (System Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LUGAL ERP — PERMISSION RESOLUTION ENGINE                  │
│                                                                              │
│  كل طلب API يمر عبر 3 طبقات (Layers) لحساب الصلاحيات الفعلية               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 3 — Individual User Override  (أعلى أولوية / WINS)            │  │
│  │  Model: lugal.crm.user.permission                                    │  │
│  │  يخزن فقط الفروقات (delta) عن الـ template                          │  │
│  └─────────────────────┬────────────────────────────────────────────────┘  │
│                         ↑ deep_merge (overrides win)                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 2 — Job-Title Template                                        │  │
│  │  Model: lugal.crm.permission.template                                │  │
│  │  مرتبط بـ res.partner.function (المسمى الوظيفي)                     │  │
│  │  يحدد الصلاحيات الافتراضية لكل مسمى وظيفي                          │  │
│  └─────────────────────┬────────────────────────────────────────────────┘  │
│                         ↑ deep_merge                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 1 — CRM Role Baseline  (أدنى أولوية)                         │  │
│  │  Odoo Groups: agent/supervisor/manager/general_manager/qa_*          │  │
│  │  يُعطى تلقائياً بناءً على مجموعة المستخدم في Odoo                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  النتيجة: effective_permissions = merge(layer1, layer2, layer3)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. هرمية الأدوار (Role Hierarchy)

```
                        ┌─────────────────────────────┐
                        │      GENERAL MANAGER         │
                        │   المدير العام / Full Access  │
                        │   admin.permissions = true    │
                        └──────────┬──────────┬────────┘
                                   │          │
                    ┌──────────────┘          └──────────────┐
                    ▼                                         ▼
           ┌─────────────────┐                    ┌──────────────────────┐
           │    MANAGER       │                    │    QA SUPERVISOR     │
           │   المدير         │                    │  مشرف مدققي الجودة  │
           └────────┬─────────┘                    └──────────┬───────────┘
                    │                                          │
                    ▼                                          ▼
           ┌─────────────────┐                    ┌──────────────────────┐
           │   SUPERVISOR     │                    │    QA AUDITOR        │
           │     المشرف       │                    │   مدقق الجودة       │
           └────────┬─────────┘                    └──────────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │     AGENT        │
           │     الموظف       │
           └─────────────────┘

           كل مستوى يرث صلاحيات المستوى الأدنى منه
```

---

## 3. شجرة الصلاحيات الكاملة (Full Permission Tree)

### 3.1 — Supply Chain / سلسلة التوريد

```
supply_chain/
├── containers/            الحاويات
│   ├── list              عرض القائمة
│   ├── view              فتح تفاصيل حاوية
│   ├── create            إضافة حاوية جديدة
│   ├── edit              تعديل بيانات الحاوية
│   ├── delete            حذف الحاوية (GM فقط)
│   ├── assign_driver     تعيين سائق
│   ├── mark_arrived      تأكيد وصول الحاوية للميناء
│   ├── clearance_delivered  تسليم مستندات الجمارك
│   ├── set_reminder      ضبط تذكير
│   ├── upload_attachment رفع مرفق
│   ├── delete_attachment حذف مرفق
│   ├── add_comment       إضافة تعليق
│   ├── delete_comment    حذف تعليق
│   ├── add_penalty       إضافة غرامة
│   └── delete_penalty    حذف غرامة
│
├── vendors/               الموردون
│   ├── list | view | create | edit | delete
│
├── po/                    طلبات الشراء
│   ├── list | view | create | edit | delete
│   ├── submit            إرسال للموافقة
│   ├── confirm           موافقة المشرف (المرحلة الأولى)
│   ├── ship              تأكيد الشحن (المدير)
│   ├── receive           استلام البضاعة (المدير)
│   ├── cancel | reopen
│   ├── add_line | edit_line | delete_line
│   ├── upload_attachment | delete_attachment
│   ├── add_comment | delete_comment
│   └── export_pdf
│
├── negotiations/          المفاوضات مع الموردين
│   ├── list | view | create | edit | delete
│   └── add_comment | delete_comment
│
├── item_requests/         طلبات التجديد
│   ├── list | view | create | edit | delete
│   ├── approve | reject   (المشرف)
│   └── fulfill            (المدير)
│
├── clearance_companies/   شركات التخليص الجمركي
│   ├── list | view
│   ├── create | edit      (المدير)
│   └── delete             (GM فقط)
│
├── tracking/              تتبع الحاويات
│   ├── view
│   └── update             (المشرف)
│
├── minmax/                حدود المخزون
│   ├── list
│   ├── edit               (المدير)
│   └── delete             (المدير)
│
├── penalties/             الغرامات
│   ├── list
│   ├── add                (المدير)
│   └── delete             (المدير)
│
├── notifications/         الإشعارات
│   ├── list | mark_read | delete
│
├── chat/                  المحادثة
│   ├── view | send
│   └── delete_message     (المشرف)
│
└── stories/               القصص / Updates
    ├── list | view | create
    └── delete             (المشرف)
```

### 3.2 — CRM

```
crm/
├── customers/             العملاء
│   ├── list | view | create | edit
│   ├── delete             (GM فقط)
│   ├── export             (المدير)
│   ├── import             (المدير)
│   └── merge              (GM فقط)
│
├── calls/                 المكالمات
│   ├── list | view | create | edit
│   ├── delete             (المدير)
│   └── listen_recording   (المدير+QA)
│
├── tickets/               التذاكر
│   ├── list | view | create | edit
│   ├── assign | escalate  (المشرف)
│   ├── close              (المدير)
│   └── delete             (GM فقط)
│
├── tasks/                 المهام
│   ├── list | view | create | edit
│   ├── assign             (المشرف)
│   ├── close              (المدير)
│   └── delete             (GM فقط)
│
├── analytics/             التحليلات
│   ├── view
│   ├── view_team_data     (المشرف)
│   └── export             (المدير)
│
├── config/                الإعدادات
│   ├── view               (المدير)
│   └── edit               (GM فقط)
│
├── branches/              الفروع
│   ├── list | view
│   ├── edit               (المشرف)
│   ├── create             (المدير)
│   └── delete             (GM فقط)
│
├── knowledge/             قاعدة المعرفة
│   ├── list | view | create | edit
│   └── delete             (المدير)
│
├── omnichannel/           القنوات المتعددة
│   ├── view | reply
│   └── assign             (المشرف)
│
└── shifts/                الورديات
    ├── view
    └── manage             (المشرف)
```

### 3.3 — QA / ضمان الجودة

```
qa/
├── reviews/               مراجعات الجودة
│   ├── list | view | create | score
│   ├── delete             (QA Supervisor)
│   └── export             (QA Supervisor)
│
├── management/            إدارة فريق QA
│   ├── view
│   ├── manage             (QA Supervisor)
│   └── assign_reviewer    (QA Supervisor)
│
└── reports/               تقارير الجودة
    ├── view
    └── export             (QA Supervisor)
```

### 3.4 — POS / نقطة البيع

```
pos/
├── sessions/              الجلسات
│   ├── list | view
│   ├── open | close       (الموظف+)
│
├── orders/                الطلبات
│   ├── list | view | create
│   ├── edit               (المدير)
│   ├── delete             (GM فقط)
│   ├── refund             (GM فقط)
│   └── export_pdf
│
├── products/              المنتجات
│   ├── list | view
│   ├── create | edit      (المدير)
│   ├── delete             (GM فقط)
│   ├── set_price          (المدير)
│   └── set_discount       (المدير)
│
├── customers/             عملاء POS
│   ├── list | view | create
│   └── edit               (المشرف)
│
├── payments/              المدفوعات
│   ├── view | process
│   └── refund             (المشرف)
│
├── reports/               التقارير
│   ├── view               (المشرف)
│   ├── export             (المدير)
│   └── z_report           (المدير)
│
└── config/                الإعدادات
    ├── view               (المدير)
    └── edit               (GM فقط)
```

### 3.5 — HR / الموارد البشرية

```
hr/
├── employees/             الموظفون
│   ├── list | view | create | edit
│   ├── delete             (GM فقط)
│   ├── view_salary        (GM فقط)
│   ├── view_private       (GM فقط)
│   └── export             (المدير)
│
├── attendance/            الحضور
│   ├── view_own           (الكل)
│   ├── view_all           (المشرف)
│   ├── edit               (المدير)
│   └── export             (المدير)
│
├── leaves/                الإجازات
│   ├── view_own | request  (الكل)
│   ├── view_all           (المشرف)
│   ├── approve | refuse   (المشرف)
│   └── manage_allocation  (المدير)
│
├── payroll/               الرواتب
│   ├── view_own           (الكل)
│   ├── view_all           (المدير)
│   ├── compute | validate (GM فقط)
│   └── export             (GM فقط)
│
├── recruitment/           التوظيف
│   ├── view | create      (المدير)
│   ├── manage             (المدير)
│   └── delete             (GM فقط)
│
├── kpi/                   مؤشرات الأداء
│   ├── view_own           (الكل)
│   ├── view_all           (المشرف)
│   ├── set                (المدير)
│   └── export             (المدير)
│
├── shifts/                الجداول الزمنية
│   ├── view_own           (الكل)
│   ├── view_all           (المشرف)
│   └── manage             (المشرف)
│
├── org_chart/             الهيكل التنظيمي
│   └── view               (المشرف+)
│
└── config/
    ├── view | edit        (GM فقط)
```

### 3.6 — Inventory / المخزون

```
inventory/
├── products/              المنتجات
│   ├── list | view | create | edit
│   ├── delete             (GM فقط)
│   ├── set_price          (GM فقط)
│   ├── import | export    (المدير)
│
├── stock/                 المخزون
│   ├── view               (المشرف+)
│   ├── adjust             (المدير)
│   ├── transfer           (المدير)
│   ├── scrap              (GM فقط)
│   └── view_valuation     (GM فقط)
│
├── transfers/             التحويلات
│   ├── list | view | create
│   ├── validate           (المشرف+)
│   ├── cancel             (المدير)
│   └── delete             (GM فقط)
│
├── warehouses/            المستودعات
│   ├── view               (المشرف+)
│   ├── create | edit      (GM فقط)
│   └── delete             (GM فقط)
│
├── locations/             المواقع
│   ├── view               (المشرف+)
│   └── create | edit | delete  (GM فقط)
│
├── lots_serials/          الأرقام التسلسلية
│   ├── view | create      (المدير+)
│   └── edit               (GM فقط)
│
├── reports/               التقارير
│   ├── view               (المدير+)
│   └── export             (المدير+)
│
└── config/                الإعدادات
    └── view | edit        (GM فقط)
```

### 3.7 — Finance / المالية والمحاسبة

```
finance/
├── invoices/              الفواتير
│   ├── list | view        (المدير+)
│   ├── create | edit      (المدير+)
│   ├── delete             (GM فقط)
│   ├── confirm | cancel   (GM فقط)
│   ├── register_payment   (GM فقط)
│   └── export_pdf
│
├── bills/                 فواتير الموردين
│   ├── list | view        (المدير+)
│   ├── create | edit | delete | confirm | cancel | register_payment (GM فقط)
│
├── payments/              المدفوعات
│   ├── list | view        (المدير+)
│   ├── create | validate | cancel  (GM فقط)
│
├── journals/              دفاتر اليومية
│   └── view | create | edit | delete  (GM فقط)
│
├── accounts/              الحسابات
│   └── view | create | edit  (GM فقط)
│
├── reports/               التقارير المالية
│   ├── profit_loss        (المدير+)
│   ├── balance_sheet      (GM فقط)
│   ├── cash_flow          (GM فقط)
│   ├── tax_report         (GM فقط)
│   └── export             (المدير+)
│
├── bank_statements/       كشوف البنك
│   ├── view               (GM فقط)
│   ├── import             (GM فقط)
│   └── reconcile          (GM فقط)
│
└── config/
    └── view | edit        (GM فقط)
```

### 3.8 — Analytics / التحليلات

```
analytics/
├── dashboards/            لوحات البيانات
│   ├── view               (المشرف+)
│   ├── create | edit      (المدير+)
│   ├── delete | share     (GM فقط)
│
├── reports/               التقارير المخصصة
│   ├── view               (المشرف+)
│   ├── create             (المدير+)
│   └── export             (المدير+)
│
├── kpi/                   مؤشرات الأداء الرئيسية
│   ├── view               (المدير+)
│   └── manage             (GM فقط)
│
└── spreadsheets/          الجداول الإلكترونية
    ├── view               (المدير+)
    ├── create | edit      (المدير+)
    └── delete             (GM فقط)
```

### 3.9 — Settings / الإعدادات

```
settings/                  (GM فقط)
├── general/               view | edit
├── users_companies/       view | manage
├── integrations/          view | manage
├── email/                 view | configure
└── sap_integration/       view | sync | configure
```

### 3.10 — Admin Panel / لوحة الإدارة

```
admin/                     (GM فقط)
├── users/                 list | view | create | assign_role | deactivate | activate
├── permissions/           view | set_job_title_defaults | set_user_overrides
├── audit_logs/            view | export | delete
└── modules/               view | install | upgrade
```

---

## 4. جدول الصلاحيات الإجمالي (Permission Matrix)

| الموديول / القسم | None | Agent | Supervisor | Manager | GM | QA Auditor | QA Supervisor |
|-----------------|:----:|:-----:|:----------:|:-------:|:--:|:----------:|:-------------:|
| **Supply Chain — العرض** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Supply Chain — الإنشاء والتعديل** | ❌ | جزئي | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Supply Chain — الحذف** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **CRM — العملاء والتذاكر** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **CRM — الحذف والدمج** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **QA — المراجعة والتقييم** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| **QA — إدارة الفريق** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| **POS — العمليات** | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **POS — الإعدادات** | ❌ | ❌ | ❌ | جزئي | ✅ | ❌ | ❌ |
| **HR — الحضور (بيانات شخصية)** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **HR — بيانات الفريق** | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **HR — الرواتب** | ❌ | عرض فقط | عرض فقط | عرض فريق | ✅ | ❌ | ❌ |
| **Inventory — العرض** | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Inventory — التعديل والنقل** | ❌ | ❌ | جزئي | ✅ | ✅ | ❌ | ❌ |
| **Finance — الفواتير** | ❌ | ❌ | ❌ | عرض | ✅ | ❌ | ❌ |
| **Finance — التقارير المالية** | ❌ | ❌ | ❌ | جزئي | ✅ | ❌ | ❌ |
| **Analytics — الداشبورد** | ❌ | عرض | عرض | ✅ | ✅ | عرض | عرض |
| **Settings** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Admin Panel** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |

---

## 5. API Endpoints — مرجع سريع

### للمستخدم الحالي

| Endpoint | الوصف |
|----------|-------|
| `POST /api/crm/me/permissions` | الصلاحيات الكاملة للمستخدم المسجّل |

### للأدمن فقط (General Manager)

| Endpoint | الوصف |
|----------|-------|
| `POST /api/crm/admin/permissions/schema` | شجرة الصلاحيات الكاملة + baselines لكل role |
| `POST /api/crm/admin/permissions/job_titles/list` | قائمة جميع templates المسميات الوظيفية |
| `POST /api/crm/admin/permissions/job_titles/upsert` | إنشاء/تعديل permissions لمسمى وظيفي |
| `POST /api/crm/admin/permissions/job_titles/delete` | حذف template |
| `POST /api/crm/admin/users/list` | قائمة المستخدمين + أدوارهم |
| `POST /api/crm/admin/users/<id>/get` | تفاصيل مستخدم + permissions |
| `POST /api/crm/admin/users/<id>/permissions/get` | التفصيل الكامل للـ 3 layers |
| `POST /api/crm/admin/users/<id>/permissions/set` | **منح/تقييد صلاحيات مستخدم محدد** |
| `POST /api/crm/admin/users/<id>/permissions/reset` | إزالة الاستثناءات الفردية |
| `POST /api/crm/admin/users/assign_role` | تعيين دور بالـ email |
| `POST /api/crm/admin/users/bulk_assign` | تعيين أدوار لمجموعة |
| `POST /api/crm/admin/users/<id>/deactivate` | تعطيل مستخدم |
| `POST /api/crm/admin/users/<id>/activate` | تفعيل مستخدم |
| `POST /api/crm/users/<id>/permissions` | permissions مستخدم بعينه |

---

## 6. سيناريوهات الاستخدام (Use Cases)

### سيناريو 1: موظف جديد بمسمى "مشرف المبيعات"

```
1. المدير يفتح: POST /api/crm/admin/permissions/job_titles/upsert
   {
     "job_title": "مشرف المبيعات",
     "crm_role": "supervisor",
     "permissions": { ...تفاصيل الصلاحيات... }
   }

2. المدير يعيّن الدور: POST /api/crm/admin/users/assign_role
   { "email": "ahmed@company.com", "role": "supervisor" }

3. عند تسجيل الدخول: GET /api/crm/me/permissions
   → يعود النظام بالصلاحيات المدمجة تلقائياً
```

### سيناريو 2: منح موظف صلاحية استثنائية

```
POST /api/crm/admin/users/5/permissions/set
{
  "permissions": {
    "supply_chain": { "containers": { "delete": true } },
    "finance": { "invoices": { "list": true, "view": true } }
  },
  "notes": "صلاحية مؤقتة لمراجعة الفترة الربعية"
}
```

### سيناريو 3: تطبيق تغيير على جميع موظفي مسمى معين

```
POST /api/crm/admin/users/5/permissions/set
{
  "permissions": {
    "inventory": { "stock": { "view": true, "adjust": true } }
  },
  "apply_to_all_same_job_title": true,
  "notes": "تحديث مايو 2026 — صلاحية المستودع لمشرفي المبيعات"
}
```

### سيناريو 4: إعطاء موظف صلاحيات مسمى وظيفي مختلف

```
POST /api/crm/admin/users/5/permissions/set
{
  "job_title_override": "مدير المستودع",
  "permissions": {},
  "notes": "يقوم بمهام مدير المستودع خلال إجازته"
}
```

---

## 7. تدفق الـ API في الـ Frontend

```
App Start
    │
    ▼
POST /api/crm/me/permissions
    │
    ├── Store permissions in Redux/Context
    │     permissions = response.data.permissions
    │
    ▼
For each UI component:
    if (can('supply_chain.containers.create')) → show "New Container" button
    if (can('admin.users.assign_role'))        → show admin menu
    if (can('finance.invoices.view'))          → show Finance section
    if (can('pos.sessions.open'))              → show POS launcher
    ...

Admin Screen:
    │
    ├── POST /api/crm/admin/permissions/schema
    │     → render permission checkboxes dynamically
    │
    ├── POST /api/crm/admin/users/list
    │     → show all users with roles
    │
    ├── Click on user → POST /api/crm/admin/users/<id>/permissions/get
    │     → show 3 layers: role_baseline + template + individual_overrides
    │
    └── Admin edits → POST /api/crm/admin/users/<id>/permissions/set
          { permissions: {...delta...}, apply_to_all_same_job_title: bool }
```

---

## 8. هيكل الملفات (File Structure)

```
addons/lugal_crm/
├── controllers/
│   ├── admin_controller.py        ← PERMISSION ENGINE + all admin APIs
│   ├── _permissions.py            ← require_group() helpers
│   ├── supply_chain_controller.py ← role guards on write routes
│   └── supply_extended_controller.py ← role guards on write routes
│
├── models/
│   ├── crm_permission_template.py ← Job-title defaults (Layer 2)
│   └── crm_user_permission.py     ← Per-user overrides (Layer 3)
│
└── security/
    ├── groups.xml                 ← CRM role definitions
    └── ir.model.access.csv        ← Model-level access rules
```

---

## 9. قاموس المصطلحات

| مصطلح | المعنى |
|-------|--------|
| `role` | الدور في Odoo (agent/supervisor/manager/general_manager/qa_*) |
| `job_title` | المسمى الوظيفي (مخزّن في `res.partner.function`) |
| `template` | صلاحيات افتراضية مرتبطة بمسمى وظيفي |
| `override` | استثناء فردي لمستخدم بعينه |
| `deep_merge` | دمج الطبقات — القيم الأعلى تلغي الأدنى |
| `effective_permissions` | النتيجة النهائية بعد دمج الـ 3 طبقات |
| `apply_to_all_same_job_title` | حفظ التغيير كـ template يطبق على كل الذين لديهم نفس المسمى |
