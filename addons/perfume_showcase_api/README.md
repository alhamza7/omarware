# Perfume Showcase API Module

## نظرة عامة / Overview

هذا المودول يوفر إدارة ديناميكية لموقع عرض العطور من خلال Odoo مع REST API endpoints.

This module provides dynamic management for the perfume showcase website through Odoo with REST API endpoints.

## المميزات / Features

- ✅ إدارة العلامات التجارية (Brands Management)
- ✅ إدارة العطور (Perfumes Management)
- ✅ إدارة النوتات (Notes Management)
- ✅ إدارة المواسم والمناسبات (Seasons & Occasions Management)
- ✅ REST API للواجهة الأمامية (REST API for Frontend)
- ✅ دعم الصور (Image Support)
- ✅ دعم متعدد اللغات (Multi-language Support)

## التثبيت / Installation

### 1. تحديث قائمة التطبيقات / Update Apps List

```
Settings → Apps → Update Apps List
```

أو من سطر الأوامر / Or from command line:

```bash
cd L:\Lugal-ai
venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u perfume_showcase_api
```

### 2. تثبيت المودول / Install Module

```
Settings → Apps → Search "Perfume Showcase" → Install
```

## الاستخدام / Usage

### إضافة علامة تجارية / Adding a Brand

1. اذهب إلى **Perfume Showcase → Brands**
2. انقر على **Create**
3. املأ البيانات:
   - **Brand Name**: اسم العلامة التجارية (مثال: Louis Vuitton)
   - **Brand Code**: كود فريد للـ API (مثال: louis-vuitton)
   - **Country**: البلد (مثال: France)
4. احفظ

### إضافة عطر / Adding a Perfume

1. اذهب إلى **Perfume Showcase → Perfumes**
2. انقر على **Create**
3. املأ البيانات:
   - **Name**: اسم العطر
   - **Code**: كود فريد (مثال: lv-1)
   - **Brand**: اختر العلامة التجارية
   - **Image**: ارفع صورة أو أدخل رابط URL
   - **Description**: وصف العطر
   - **Longevity**: مدة البقاء (مثال: 8-10 hours)
   - **Sillage**: قوة الانتشار (مثال: Heavy)
   - **Seasons**: اختر المواسم المناسبة
   - **Occasions**: اختر المناسبات المناسبة
   - **Notes**: اختر النوتات (Top, Middle, Base)
4. احفظ

### إعداد النوتات والمواسم والمناسبات / Setting up Notes, Seasons & Occasions

1. اذهب إلى **Perfume Showcase → Configuration**
2. أضف:
   - **Notes**: النوتات (Top, Middle, Base)
   - **Seasons**: المواسم (Spring, Summer, Fall, Winter)
   - **Occasions**: المناسبات (Daytime, Evening, Office, etc.)

## API Endpoints

### Get All Brands
```
GET /api/perfume/brands
```

### Get Specific Brand
```
GET /api/perfume/brands/{brand_code}
```

### Get All Perfumes
```
GET /api/perfume/perfumes?brand_id={brand_code}
```

### Get Specific Perfume
```
GET /api/perfume/perfumes/{perfume_code}
```

### Get Options (Seasons, Occasions, Notes)
```
GET /api/perfume/options
```

## تكوين الواجهة الأمامية / Frontend Configuration

في مجلد `Perfume Brand Showcase Page`:

1. أنشئ ملف `.env`:
```env
VITE_API_BASE_URL=http://localhost:8070
```

2. شغّل التطبيق:
```bash
npm run dev
```

## استيراد البيانات الأولية / Import Initial Data

يمكنك استخدام واجهة Odoo لإضافة البيانات يدوياً، أو استخدام Data Import wizard:

1. اذهب إلى **Perfume Showcase → Brands**
2. انقر على **Import**
3. ارفع ملف CSV مع البيانات

## الدعم / Support

للمساعدة والدعم، يرجى التواصل مع فريق Lugal-AI.

For support, please contact Lugal-AI team.

