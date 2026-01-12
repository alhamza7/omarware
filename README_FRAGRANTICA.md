# 🌸 Fragrantica Integration Module

مودول Odoo لربط منتجات العطور مع قاعدة بيانات Fragrantica الشاملة

---

## ⚠️ مهم: البيانات غير مُضمنة في Git

مجلدات البيانات التالية **لا تُرفع على Git** (حجمها ~3 GB):

```
❌ /fregran/                          # قاعدة البيانات + صور + سكريبتات
❌ /fragrantica_data_export/images/   # صور التصدير
❌ /fragrantica_data_export/perfumes.db  # قاعدة البيانات
```

**السبب:** الحجم الكبير (3+ GB) - تُنقل يدوياً للسيرفر

---

## 📦 ما هو مُضمن في Git

✅ **مودول Odoo الكامل:**
- `addons/lugal_fragrantica/` - المودول الرئيسي
  - Models, Views, Wizards, Security
  - CSS, Documentation
  - **لا يحتوي على البيانات/الصور**

✅ **سكريبتات وأدوات:**
- `fragrantica_data_export/prepare_export.py` - سكريبت التصدير
- `fragrantica_data_export/START_PREPARE_EXPORT.bat` - تشغيل سريع

✅ **دلائل شاملة:**
- `QUICK_START_DIRECT_FREGRAN.md` - بدء سريع (نقل fregran)
- `QUICK_START_FRAGRANTICA.md` - بدء سريع (التصدير)
- `addons/lugal_fragrantica/INSTALLATION_DIRECT_FREGRAN.md` - تثبيت كامل
- `addons/lugal_fragrantica/INSTALLATION_AR.md` - تثبيت كامل (طريقة التصدير)
- `FRAGRANTICA_MODULE_SUMMARY.md` - ملخص شامل

---

## 🚀 البدء السريع

### للمطورين الجدد (بعد Clone):

**خطوة 1: احصل على البيانات**

تواصل مع المطور الأصلي للحصول على:
- مجلد `fregran/` كاملاً (طريقة 1 - الأسهل)
- أو `perfumes.db` + `images/` (طريقة 2)

**خطوة 2: اتبع أحد الدليلين:**

- **الطريقة 1 (موصى بها):** `QUICK_START_DIRECT_FREGRAN.md`
- **الطريقة 2:** `QUICK_START_FRAGRANTICA.md`

---

## 📖 الوثائق الكاملة

| الملف | الوصف | متى تستخدمه |
|------|-------|-------------|
| `QUICK_START_DIRECT_FREGRAN.md` | دليل سريع (3 خطوات) | ✅ ابدأ هنا! |
| `addons/lugal_fragrantica/INSTALLATION_DIRECT_FREGRAN.md` | دليل كامل مفصل | للتفاصيل |
| `addons/lugal_fragrantica/DATA_SETUP.md` | إعداد البيانات | بعد clone |
| `FRAGRANTICA_MODULE_SUMMARY.md` | ملخص شامل | للمرجع |

---

## 🌟 المميزات

- ✅ 49,000+ عطر من Fragrantica
- ✅ معلومات تفصيلية (نوتات، توافقات، وصف، صور)
- ✅ بحث ذكي بالعربي والإنجليزي
- ✅ تاب مخصص في صفحة المنتج
- ✅ إمكانية التخصيص الكامل
- ✅ إدارة طلبات العطور الجديدة

---

## 🔧 التثبيت السريع

```bash
# 1. Clone المشروع
git clone <repo_url>
cd Lugal-ai

# 2. احصل على مجلد fregran من المطور الأصلي
# (أو استخدم طريقة التصدير)

# 3. انقل للسيرفر
scp -r fregran/ user@server:/opt/odoo/

# 4. على السيرفر
ssh user@server
sudo chown -R odoo:odoo /opt/odoo/fregran
sudo systemctl restart odoo

# 5. في Odoo
# Apps → Install "Fragrantica"
# Fragrantica → Import Data → Start
```

**للتفاصيل الكاملة:** `QUICK_START_DIRECT_FREGRAN.md`

---

## 📁 هيكل المشروع

```
Lugal-ai/
├── addons/
│   └── lugal_fragrantica/        ✅ المودول (في Git)
│       ├── models/
│       ├── views/
│       ├── wizards/
│       ├── static/
│       │   ├── src/css/          ✅ CSS (في Git)
│       │   ├── fragrantica_data/ ❌ البيانات (يدوي)
│       │   └── fregran/          ❌ البيانات (يدوي)
│       └── *.md                  ✅ دلائل (في Git)
│
├── fregran/                      ❌ لا يُرفع على Git
│   ├── perfumes.db               ❌ (3+ GB total)
│   └── static/images/            ❌
│
├── fragrantica_data_export/
│   ├── prepare_export.py         ✅ سكريبت (في Git)
│   ├── perfumes.db               ❌ لا يُرفع (كبير)
│   └── images/                   ❌ لا يُرفع (كبير)
│
└── *.md                          ✅ دلائل (في Git)
```

---

## 💾 حجم البيانات

| المكون | الحجم | مُضمن في Git؟ |
|--------|-------|---------------|
| المودول (كود) | ~500 KB | ✅ نعم |
| قاعدة البيانات | ~50 MB | ❌ لا |
| الصور | ~3 GB | ❌ لا |
| **الإجمالي** | **~3 GB** | **يُنقل يدوياً** |

---

## 🔐 `.gitignore`

تم إضافة القواعد التالية لـ `.gitignore`:

```gitignore
# Fragrantica data (كبيرة جداً - تُنقل يدوياً)
/fregran/
/fragrantica_data_export/perfumes.db
/fragrantica_data_export/images/

# تجاهل البيانات داخل المودول
addons/lugal_fragrantica/static/fragrantica_data/
addons/lugal_fragrantica/static/fregran/
```

---

## 🤝 للمساهمين

### إضافة ميزات جديدة:

1. Fork المشروع
2. أنشئ branch جديد
3. **لا تضف** ملفات البيانات الكبيرة
4. اختبر التغييرات
5. أنشئ Pull Request

### اختبار المودول:

```bash
# الكود فقط (بدون بيانات)
git clone <your-fork>
# ثم احصل على البيانات من المطور الأصلي
```

---

## 📞 الدعم

- **للتثبيت:** راجع `QUICK_START_DIRECT_FREGRAN.md`
- **للمشاكل:** راجع قسم "حل المشاكل" في دلائل التثبيت
- **للبيانات:** راجع `addons/lugal_fragrantica/DATA_SETUP.md`

---

## 📝 الترخيص

LGPL-3

---

## ✨ ملخص

**المودول كامل ✅** - جاهز للاستخدام

**البيانات منفصلة ❌** - تُنقل يدوياً (حجمها كبير)

**ابدأ من هنا 👉** `QUICK_START_DIRECT_FREGRAN.md`

---

صُنع بـ ❤️ من فريق Lugal





