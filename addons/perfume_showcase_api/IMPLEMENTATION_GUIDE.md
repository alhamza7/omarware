# دليل التنفيذ - Perfume Showcase API Module
# Implementation Guide

## ✅ ما تم إنجازه / What Was Completed

### 1. هيكل المودول / Module Structure
- ✅ `__manifest__.py` - ملف تعريف المودول
- ✅ `__init__.py` - ملفات التهيئة
- ✅ `models/` - الموديلات
- ✅ `controllers/` - API Controllers
- ✅ `views/` - واجهات المستخدم
- ✅ `security/` - قواعد الأمان
- ✅ `data/` - البيانات الأولية

### 2. الموديلات / Models

#### perfume.brand
- إدارة العلامات التجارية
- الحقول: name, code, country, perfumes

#### perfume.perfume
- إدارة العطور
- الحقول: name, code, brand_id, image, description, longevity, sillage
- علاقات: seasons, occasions, notes (top/middle/base)

#### perfume.note
- إدارة النوتات
- الحقول: name, category (top/middle/base)

#### perfume.season
- إدارة المواسم
- الحقول: name

#### perfume.occasion
- إدارة المناسبات
- الحقول: name

### 3. REST API Endpoints

جميع الـ endpoints متاحة للعامة (public) مع دعم CORS:

- `GET /api/perfume/brands` - الحصول على جميع العلامات التجارية
- `GET /api/perfume/brands/{code}` - الحصول على علامة تجارية محددة
- `GET /api/perfume/perfumes` - الحصول على جميع العطور
- `GET /api/perfume/perfumes/{code}` - الحصول على عطر محدد
- `GET /api/perfume/options` - الحصول على الخيارات (seasons, occasions, notes)

### 4. الواجهة الأمامية / Frontend

- ✅ تم إنشاء `src/services/api.ts` - خدمة API
- ✅ تم تحديث `App.tsx` لاستخدام API
- ✅ إضافة حالات التحميل والأخطاء
- ✅ دعم متعدد اللغات

## 📋 خطوات التثبيت / Installation Steps

### الخطوة 1: تثبيت المودول في Odoo

```bash
cd L:\Lugal-ai
venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070
```

ثم من واجهة Odoo:
1. Settings → Apps
2. Update Apps List
3. Search "Perfume Showcase"
4. Install

### الخطوة 2: إضافة البيانات

#### أ. إضافة علامات تجارية:
1. Perfume Showcase → Brands → Create
2. مثال:
   - Name: Louis Vuitton
   - Code: louis-vuitton
   - Country: France

#### ب. إضافة مواسم ومناسبات:
1. Perfume Showcase → Configuration → Seasons
2. أضف: Spring, Summer, Fall, Winter, All Seasons
3. Perfume Showcase → Configuration → Occasions
4. أضف: Daytime, Evening, Office, Casual, Special Events, etc.

#### ج. إضافة نوتات:
1. Perfume Showcase → Configuration → Notes
2. أضف النوتات مع تصنيفها (Top, Middle, Base)

#### د. إضافة عطور:
1. Perfume Showcase → Perfumes → Create
2. املأ جميع البيانات المطلوبة

### الخطوة 3: تكوين الواجهة الأمامية

في مجلد `Perfume Brand Showcase Page`:

1. أنشئ ملف `.env`:
```env
VITE_API_BASE_URL=http://localhost:8070
```

2. شغّل التطبيق:
```bash
cd "Perfume Brand Showcase Page"
npm install
npm run dev
```

## 🔧 التكوين / Configuration

### تغيير عنوان API

في ملف `.env`:
```env
VITE_API_BASE_URL=http://your-odoo-server:8070
```

### إعداد CORS

الـ API يدعم CORS بشكل افتراضي. إذا كنت تحتاج لتعديل الإعدادات، راجع:
`addons/perfume_showcase_api/controllers/perfume_api_controller.py`

## 📝 ملاحظات مهمة / Important Notes

1. **الكود الفريد**: تأكد من استخدام كود فريد لكل علامة تجارية وعطر
2. **الصور**: يمكنك رفع صورة أو إدخال رابط URL خارجي
3. **الترجمة**: جميع الحقول تدعم الترجمة (translate=True)
4. **الأمان**: الـ API متاح للعامة، لكن يمكنك تعديل الأذونات في `security/ir.model.access.csv`

## 🐛 استكشاف الأخطاء / Troubleshooting

### المشكلة: API لا يعمل
- تحقق من أن المودول مثبت
- تحقق من عنوان URL في `.env`
- تحقق من logs في Odoo

### المشكلة: CORS Error
- تأكد من أن الـ API يدعم CORS (مفعل افتراضياً)
- تحقق من إعدادات المتصفح

### المشكلة: البيانات لا تظهر
- تحقق من أن العلامات التجارية والعطور مفعلة (active=True)
- تحقق من console في المتصفح للأخطاء

## 📚 الملفات المهمة / Important Files

- `models/perfume_perfume.py` - موديل العطور
- `controllers/perfume_api_controller.py` - API Controller
- `views/perfume_perfume_views.xml` - واجهات العطور
- `src/services/api.ts` - خدمة API في React
- `src/App.tsx` - المكون الرئيسي

## 🎯 الخطوات التالية / Next Steps

1. ✅ تثبيت المودول
2. ✅ إضافة البيانات الأولية
3. ✅ اختبار API
4. ✅ تشغيل الواجهة الأمامية
5. ✅ إضافة المزيد من العطور والعلامات التجارية

## 📞 الدعم / Support

للمساعدة، راجع `README.md` أو تواصل مع فريق Lugal-AI.

