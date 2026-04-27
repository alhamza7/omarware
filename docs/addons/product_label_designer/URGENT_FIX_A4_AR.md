# إصلاح A4 العاجل! 🚨

## المشكلة: إعدادات A4 موجودة لكن ما زال يطبع كل ملصق في صفحة

---

## ✅ **السبب:**

لم يتم **Upgrade** الموديول بعد التعديلات الأخيرة!

---

## 🔥 **الحل (5 خطوات فقط):**

### 1️⃣ **Uninstall الموديول:**

```
Apps → Product Label Designer → Uninstall
→ تأكيد الحذف
→ انتظر
```

---

### 2️⃣ **أعد تشغيل Odoo:**

```
في PowerShell:
Get-Process -Name python | Stop-Process -Force
Start-Sleep -Seconds 3
$env:PATH += ';C:\Program Files\wkhtmltopdf\bin'
.\venv\Scripts\python.exe .\odoo-bin -c .\odoo.conf --http-port=8070
```

انتظر 30 ثانية

---

### 3️⃣ **Install من جديد:**

```
http://localhost:8070
Apps → Update Apps List
ابحث: Product Label Designer
Install
```

---

### 4️⃣ **أنشئ قالب جديد:**

```
Label Templates → Create

Name: A4 Template
Width: 80mm
Height: 60mm

تبويب "Display Options":
☑ Show Name
☑ Show Foreign Name
☑ Show Code
☑ Show QR

تبويب "A4 Layout":
Labels per Row: 2
Labels per Column: 4
Margin: 2mm

Save
```

---

### 5️⃣ **جرّب:**

```
Select Products → اختر منتجات
Action → Print Labels

في المعالج:
- Template: A4 Template  ← القالب الجديد
- Print Mode: A4 Sheet
- Print PDF

→ سيعمل! ✅
```

---

## 🎯 **البديل السريع:**

### استخدم Preview ثم Ctrl+P:

```
1. Select Products
2. Print Labels
3. Print Mode: A4 Sheet
4. Preview in Browser  ← افتح HTML
5. في التبويب الجديد: Ctrl+P
6. Save as PDF
7. ✅ جاهز!
```

---

**جرّب البديل السريع الآن (Ctrl+P من Preview)!** 🚀

