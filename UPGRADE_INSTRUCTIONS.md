# 📋 تعليمات الترقية - SAP Integration Module

## ✅ **الخطوات:**

### **1. من المتصفح:**
```
1. افتح: http://localhost:8069
2. سجل دخول: admin / admin
3. Settings → Activate Developer Mode
4. Apps → أزل فلتر "Apps"
5. ابحث عن: SAP Integration
6. اضغط: Upgrade ⬆️
7. انتظر (~1 دقيقة)
```

### **2. أو من Terminal:**
```batch
# في PowerShell:
cd L:\Lugal-ai

# أوقف Odoo من Task Manager أولاً

# ثم نفذ:
python odoo-bin -c odoo.conf -d lugal -u sap_integration --stop-after-init

# انتظر حتى ترى "Modules loaded" ثم:
.\restart_odoo_safe.bat
```

---

## 🎯 **بعد الترقية - التحقق:**

```batch
python check_current_data.py
```

**يجب أن ترى:**
- sap.uom.group: 0 records (جاهز للاستخدام)
- لا أخطاء

---

## 🚀 **بعدها - استيراد UOM Groups:**

```batch
python simple_uom_check.py
```

**ثم قل لي النتيجة!**

---

## ⚠️ **إذا حدث خطأ:**

أرسل لي:
1. نص الخطأ
2. آخر 50 سطر من odoo.log


