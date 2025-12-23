# الحل السريع - Quick Fix

## ❌ المشكلة 1
ميزة "حذف التكرارات" لا تظهر في قائمة SAP Integration

## ✅ الحل 1
تم إضافة الصلاحيات المفقودة

---

## ❌ المشكلة 2
خطأ عند تشغيل الميزة:
```
psycopg2.errors.UndefinedFunction: operator does not exist: jsonb ~~ unknown
```

## ✅ الحل 2
تم إصلاح استعلامات SQL للتعامل مع حقول JSONB (الترجمة)

---

## 🚀 خطوة واحدة فقط!

### من Terminal (Linux/Server):
```bash
cd /home/lugalai/Lugal-ai
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal -u sap_integration --stop-after-init
./venv/bin/python3 odoo-bin -c odoo_simple.conf -d lugal
```

### من PowerShell (Windows):
```powershell
cd D:\capo_dev\Lugal-ai\addons\sap_integration
.\update_module.ps1
```

---

## 📍 الوصول للميزة
```
SAP Integration → Management Tools → حذف التكرارات
```

---

## 📚 للتفاصيل الكاملة
- **الصلاحيات:** `FIX_DUPLICATE_CLEANER_MENU_AR.md`
- **خطأ JSONB:** `FIX_JSONB_ERROR_AR.md`

