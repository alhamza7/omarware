# الحل السريع - Quick Fix

## ❌ المشكلة
ميزة "حذف التكرارات" لا تظهر في قائمة SAP Integration

## ✅ الحل
تم إضافة الصلاحيات المفقودة

## 🚀 خطوة واحدة فقط!

### الطريقة الأسهل - من PowerShell:
```powershell
cd D:\capo_dev\Lugal-ai\addons\sap_integration
.\update_module.ps1
```

### أو يدوياً:
```powershell
cd D:\capo_dev\Lugal-ai
.\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal -u sap_integration --stop-after-init
.\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal
```

## 📍 الوصول للميزة
```
SAP Integration → Management Tools → حذف التكرارات
```

## 📚 للتفاصيل الكاملة
راجع ملف: `FIX_DUPLICATE_CLEANER_MENU_AR.md`

