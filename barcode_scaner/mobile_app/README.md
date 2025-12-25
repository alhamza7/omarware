## Flutter APK (Inventory Scan-first)

### 1) إنشاء مشروع Flutter (مرة واحدة)
افتح Terminal على جهازك (حيث Flutter مثبت) داخل مجلد `barcode_scaner` ثم نفّذ:

```bash
flutter create mobile_app_runner
```

ثم انسخ محتويات `mobile_app/` إلى داخل مشروعك الجديد:
- انسخ `mobile_app/lib` إلى `mobile_app_runner/lib`
- انسخ `mobile_app/pubspec.yaml` (استبدل الموجود)

### 2) ضبط عنوان السيرفر
في `mobile_app_runner/lib/config.dart` غيّر `baseUrl` إلى IP جهاز الكمبيوتر داخل الشبكة:
مثال:
- `http://192.168.116.204:3000`

### 3) تشغيل التطبيق
```bash
cd mobile_app_runner
flutter pub get
flutter run
```

### 4) APIs المستخدمة
- `POST /api/auth/login` -> يرجع token
- `GET /api/me` -> يرجع warehouse_id
- `POST /api/me/warehouse` -> تغيير المخزن
- `GET /api/items/by-code/:code` -> جلب صنف من الباركود
- `POST /api/counts` -> حفظ الجرد












