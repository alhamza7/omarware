# اختبار PDF - تشخيص المشكلة

## 🔍 **المشكلة:**

PDF فارغ لكن Preview (HTML) يعمل.

---

## ✅ **الحل: اختبار بسيط**

أضفت تقرير اختبار بسيط جداً بدون أي تعقيدات.

### الخطوة 1: Upgrade

```
Apps → Product Label Designer → Upgrade
```

---

### الخطوة 2: جرّب التقرير البسيط

```
1. افتح أي منتج
2. Print → Simple Test
3. سيفتح PDF

إذا عمل:
→ المشكلة في التقرير المعقد

إذا لم يعمل:
→ المشكلة في wkhtmltopdf نفسه
```

---

### الخطوة 3: تفعيل Debug Mode

```
في odoo.conf أضف:
log_level = debug_rpc
workers = 0

أعد تشغيل Odoo
```

---

### الخطوة 4: جرّب مرة أخرى

```
Quick Print → Download PDF

ثم افحص السجل:
Get-Content .\odoo.log -Tail 500 | Select-String "wkhtmltopdf"
```

---

## 🐛 **الأسباب المحتملة:**

### 1. **صور كبيرة جداً**
```
الحل:
- صغّر صورة الخلفية/الشعار
- أقل من 500KB
```

### 2. **CSS معقد**
```
الحل:
- استخدم تقرير بسيط أولاً
- ثم أضف التعقيدات تدريجياً
```

### 3. **wkhtmltopdf timeout**
```
الحل:
في odoo.conf أضف:
limit_time_real = 300
```

### 4. **workers = 1**
```
الحل:
في odoo.conf:
workers = 0  (للتطوير)
أو
workers = 2  (للإنتاج)
```

---

## 📋 **الاختبار السريع:**

```
1. Upgrade
2. افتح منتج
3. Print → Simple Test
4. إذا عمل: المشكلة في قالبنا
5. إذا لم يعمل: المشكلة في wkhtmltopdf

أخبرني النتيجة!
```

---

**Upgrade الآن وجرّب Simple Test!** 🚀

