# ⚡ خطوات سريعة لإصلاح الفاتورة

**المشكلة:** الحروف العربية تظهر كرموز غريبة  
**الحل:** 5 دقائق فقط!

---

## 🚀 الخطوات (نفذها بالترتيب)

### 1️⃣ على الخادم (192.168.116.211):

**انسخ والصق هذه الأوامر كلها:**

```bash
# تثبيت الخطوط العربية
sudo apt-get update && \
sudo apt-get install -y fonts-dejavu fonts-dejavu-core fonts-dejavu-extra && \
sudo apt-get install -y fonts-arabeyes && \
sudo fc-cache -f -v && \
sudo systemctl restart odoo

echo "✅ تم تثبيت الخطوط بنجاح!"
```

**الوقت المتوقع:** 2-3 دقائق

---

### 2️⃣ من المتصفح:

```
1. Apps → Developer Mode
2. ابحث: POS Perfume Custom  
3. Upgrade ⬆️
4. Ctrl + Shift + Delete (امسح كل شيء)
5. Ctrl + F5 (أعد تحميل)
```

---

### 3️⃣ رفع اللوجو (إذا لم يكن مرفوعاً):

```
Settings → Companies → اختر الشركة → Upload Logo
```

**مواصفات اللوجو:**
- صيغة: PNG (خلفية شفافة) أو JPG
- حجم: 400x150 بكسل
- حجم ملف: أقل من 500 KB

---

### 4️⃣ اختبار:

```
POS Perfume → طلب جديد → 💾 Save → 🖨️ Print
```

---

## ✅ النتيجة المتوقعة

### قبل:
```
❌ رموز غريبة بدل العربية
❌ 78,000.000 (أصفار زائدة)
❌ لوجو صغير
```

### بعد:
```
✅ نص عربي واضح
✅ 78,000 د.ع (نظيف)
✅ لوجو كبير وواضح
✅ رقم SAP: 2600006 (أخضر بارز)
```

---

## 🆘 إذا لم يعمل

### المشكلة: العربية ما زالت غير واضحة

**جرّب هذا:**

```bash
# مسح ذاكرة wkhtmltopdf
sudo rm -rf /tmp/wkhtmlto*

# إعادة تشغيل Odoo
sudo systemctl restart odoo
```

### المشكلة: خطأ عند تثبيت الخطوط

```bash
# إذا ظهر خطأ "unable to locate package"
sudo apt-get update
sudo apt-cache search fonts-dejavu

# ثم جرب التثبيت مرة أخرى
```

---

## 💡 تأكيد نجاح التثبيت

```bash
# التحقق من الخطوط المثبتة
fc-list | grep -i dejavu

# يجب أن ترى:
# DejaVu Sans
# DejaVu Sans Mono
# DejaVu Serif
```

---

## 📞 الدعم

**إذا لم تعمل أي طريقة:**

أرسل لي نتيجة هذا الأمر:
```bash
fc-list | grep -i dejavu && wkhtmltopdf --version
```

---

**الوقت الكلي:** 5 دقائق  
**الصعوبة:** ⭐ سهل  
**النتيجة:** ✅ فواتير عربية احترافية

---

**ابدأ الآن!** 🚀

