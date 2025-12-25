# 🚀 البدء السريع - التكامل مع SAP

## ⚡ الإعداد في 3 خطوات

### 1️⃣ تثبيت الحزمة المطلوبة

```bash
npm install
```

### 2️⃣ تكوين SAP

انسخ ملف النموذج وعدله:

```bash
cp env.example .env
```

ثم عدل الملف `.env`:

```env
SAP_ENABLED=true
SAP_SERVICE_LAYER_URL=https://your-sap-server:50000/b1s/v1
SAP_COMPANY_DB=YOUR_COMPANY_DB
SAP_USERNAME=manager
SAP_PASSWORD=your_password
```

### 3️⃣ تشغيل السيرفر

```bash
npm run dev
```

---

## ✅ اختبار الاتصال

افتح المتصفح أو استخدم `curl`:

```bash
curl http://localhost:3000/api/sap/status
```

إذا رأيت:
```json
{
  "enabled": true,
  "connected": true
}
```

**مبروك! 🎉 التكامل يعمل بنجاح**

---

## 📱 بناء تطبيق الموبايل

```bash
cd mobile_app_runner
flutter clean
flutter build apk --release
```

الملف سيكون في: `build/app/outputs/flutter-apk/app-release.apk`

---

## 📚 التوثيق الكامل

راجع الملف: **[دليل_التكامل_مع_SAP.md](دليل_التكامل_مع_SAP.md)**

---

## 🆘 مشاكل شائعة

### المشكلة: SAP غير متصل

```bash
# تأكد من:
1. SAP_ENABLED=true في .env
2. عنوان Service Layer صحيح
3. بيانات الدخول صحيحة
```

### المشكلة: SSL Certificate Error

```bash
# للتطوير فقط - الكود الحالي يتجاهل شهادات SSL
# للإنتاج - راجع دليل التكامل الكامل
```

---

**تم بحمد الله ✨**






