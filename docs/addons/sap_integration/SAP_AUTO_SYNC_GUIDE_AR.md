# 🔄 التحديث التلقائي اليومي من SAP

## 📋 **الخطوات:**

### 1️⃣ **تفعيل Module (مرة واحدة فقط)**

```bash
cd ~/Lugal-ai
./venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u sap_integration
```

---

### 2️⃣ **إعداد Auto Sync**

1. اذهب إلى: `SAP → Configuration → Auto Sync`
2. اضغط **Create**
3. املأ المعلومات:
   - **Name**: "Daily SAP Sync"
   - **SAP Backend**: اختر الـ Backend
   - **Batch Size**: `100` (افتراضي)
   - **Product Limit**: `0` (بدون حد)
   
4. فعّل الخيارات المطلوبة:
   - ✅ **Sync Products** ← المنتجات
   - ✅ **Sync Pricelists** ← الأسعار
   - ☐ **Sync UoM Groups** ← وحدات القياس (فقط عند الحاجة)
   - ☐ **Sync Warehouse** ← المستودعات (فقط عند الحاجة)

5. **Save**

---

### 3️⃣ **التحديث التلقائي**

✅ **النظام سيعمل تلقائياً كل يوم** في الساعة **2:00 صباحاً**!

---

### 4️⃣ **تحديث يدوي (اختياري)**

إذا أردت التحديث الآن:

1. افتح تكوين Auto Sync
2. اضغط **🔄 Sync Now**
3. انتظر حتى ينتهي
4. تحقق من الـ Status: ✅ **Success**

---

## 📊 **مراقبة التحديثات:**

### من الواجهة:
```
SAP → Configuration → Auto Sync
```

ستجد:
- ✅ **Last Sync Date** ← آخر تحديث
- ✅ **Last Sync Status** ← الحالة (Success/Failed)
- ✅ **Total Synced** ← إجمالي ما تم تحديثه
- ✅ **Total Errors** ← إجمالي الأخطاء
- 📄 **Last Sync Log** ← سجل التفاصيل

### من Logs:
```bash
tail -f ~/Lugal-ai/odoo.log | grep "SAP Daily Auto-Sync"
```

---

## ⚙️ **تعديل وقت التحديث:**

إذا أردت تغيير الوقت من 2:00 صباحاً:

1. اذهب إلى: `Settings → Technical → Automation → Scheduled Actions`
2. ابحث عن: **"SAP Daily Auto-Sync"**
3. غيّر:
   - **Next Execution Date** ← التاريخ/الوقت التالي
   - **Interval Number** ← العدد (1)
   - **Interval Unit** ← الوحدة (Days, Hours, Minutes)

---

## 🎯 **مثال: تحديث كل 6 ساعات:**

```
Interval Number: 6
Interval Unit: Hours
```

---

## 📝 **ملاحظات:**

✅ **يدعم Update (لا يكرر المنتجات)**  
✅ **Batch Processing (معالجة دفعات)**  
✅ **Error Handling (معالجة الأخطاء)**  
✅ **Detailed Logging (سجل تفصيلي)**  
✅ **Manual Trigger (تشغيل يدوي)**  

---

## 🆘 **استكشاف الأخطاء:**

### إذا فشل التحديث:

1. افتح Auto Sync Configuration
2. اقرأ **Last Sync Log**
3. ابحث عن الأخطاء (`❌`)
4. تحقق من:
   - اتصال SAP Backend
   - صلاحيات المستخدم
   - مساحة القرص

### تحقق من Cron Job:

```bash
# تحقق من أن Cron Job نشط
cd ~/Lugal-ai
./venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai
```

في الـ shell:
```python
cron = env['ir.cron'].search([('name', '=', 'SAP Daily Auto-Sync')])
print(f"Active: {cron.active}")
print(f"Next Call: {cron.nextcall}")
```

---

## 🚀 **الآن جاهز!**

النظام سيحدث من SAP **تلقائياً كل يوم** دون أي تدخل! ✨

