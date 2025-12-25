# 🧪 أوامر الاختبار السريعة

## 🚀 اختبارات SAP

### 1. اختبار الاتصال الأساسي
```bash
node test_sap_connection.js
```
**يختبر:**
- تسجيل الدخول
- جلب المخازن
- جلب الأصناف
- جلب الكميات
- البحث بالباركود

---

### 2. اختبار الأصناف الحقيقية
```bash
node test_real_items.js
```
**يختبر:**
- أصناف محددة من SAP
- الباركودات الفعلية
- عرض أول 10 أصناف بباركود

---

## 📱 اختبار التطبيق

### بناء APK
```bash
cd mobile_app_runner
flutter clean
flutter build apk --release
```

**الملف:** `build/app/outputs/flutter-apk/app-release.apk`

---

## 🌐 اختبار APIs

### حالة SAP
```bash
curl http://localhost:3000/api/sap/status
```

### تسجيل الدخول
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

### جلب كمية بالكود
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:3000/api/sap/item-quantity/S00737
```

### جلب كمية بالباركود
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:3000/api/sap/item-by-barcode/100527
```

---

## 📦 باركودات تجريبية

استخدم هذه للاختبار:

| الباركود | الكود | الاسم |
|----------|------|-------|
| `100527` | S00737 | S-527 |
| `3700082500128` | DY00043 | معطر شاليز |
| `6136` | G00907 | انفني روز |
| `6099` | G01350 | 9 صبح - افنان |
| `4600220220` | ALC00017 | كحول اماراتي |

---

**تم بحمد الله ✨**






