# تعليمات الترقية - Upgrade Instructions

## المشكلة / Problem
المودول مثبت لكن القوائم لا تظهر / Module is installed but menus don't appear

## الحل / Solution

### الطريقة 1: Upgrade من سطر الأوامر (موصى بها)

```bash
cd L:\Lugal-ai
venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u perfume_showcase_api
```

### الطريقة 2: إلغاء التثبيت وإعادة التثبيت

1. من واجهة Odoo:
   - Settings → Apps
   - ابحث عن "Perfume Showcase API"
   - انقر على "Uninstall"

2. ثم:
   - Settings → Apps
   - ابحث عن "Perfume Showcase API"
   - انقر على "Install"

### الطريقة 3: تحديث قائمة التطبيقات أولاً

1. Settings → Apps
2. انقر على "Update Apps List" (في القائمة المنسدلة)
3. ثم ابحث عن المودول وقم بالترقية

## بعد الترقية / After Upgrade

بعد الترقية، يجب أن تظهر القائمة الجانبية:

```
Perfume Showcase
├── Brands
├── Perfumes
└── Configuration
    ├── Notes
    ├── Seasons
    └── Occasions
```

## إذا لم تظهر القائمة / If Menu Still Doesn't Appear

1. تأكد من تفعيل Developer Mode:
   - Settings → General Settings → Developer Tools → Activate developer mode

2. تحقق من القوائم يدوياً:
   - Settings → Technical → User Interface → Menu Items
   - ابحث عن "Perfume Showcase"

3. إذا كانت موجودة لكن غير مرئية:
   - تحقق من Groups (يجب أن تكون base.group_user)
   - تحقق من Active (يجب أن تكون True)

4. إعادة تحميل الصفحة (Ctrl+F5)

