# دليل التحكم الكامل بالملصقات 🎨

## ✅ **جميع عناصر التحكم المتاحة:**

---

## 1️⃣ **الاتجاه (Text Alignment)**

### في القالب → Display Options → Text Alignment:

```
Name Alignment:        ○ Left  ○ Center  ⦿ Right
Foreign Name Alignment: ⦿ Left  ○ Center  ○ Right
Code Alignment:        ○ Left  ⦿ Center  ○ Right
Price Alignment:       ○ Left  ⦿ Center  ○ Right
```

### أمثلة:

#### **Center (وسط):**
```
        عطر الورد الجوري
          Rose Perfume
            ADF-001
             99.99
```

#### **Right (يمين):**
```
عطر الورد الجوري
       Rose Perfume
            ADF-001
               99.99
```

#### **Left (يسار):**
```
عطر الورد الجوري
Rose Perfume
ADF-001
99.99
```

---

## 2️⃣ **سُمك الخط (Bold)**

### في القالب → Display Options → Font Weight:

```
☑ Name Bold              ← خط عريض
☐ Foreign Name Bold      ← خط عادي
☑ Code Bold              ← خط عريض
☑ Price Bold             ← خط عريض
```

### النتيجة:
```
**عطر الورد الجوري**      ← bold
Rose Perfume              ← normal
**ADF-001**               ← bold
**99.99**                 ← bold
```

---

## 3️⃣ **الخط المائل (Italic)**

### في القالب → Display Options → Font Style:

```
☐ Name Italic
☑ Foreign Name Italic     ← مائل
☐ Code Italic
☐ Price Italic
```

### النتيجة:
```
عطر الورد الجوري         ← عادي
Rose Perfume             ← مائل (italic)
ADF-001                  ← عادي
99.99                    ← عادي
```

---

## 4️⃣ **حجم الخط (Font Size)**

### في القالب → Display Options → Font Sizes:

```
Name: 16pt
Foreign Name: 12pt
Code: 32pt              ← كبير جداً
Price: 20pt
Barcode: 8pt
```

---

## 5️⃣ **رمز العملة**

### في القالب → Display Options → Price Display:

```
☐ Show Currency Symbol   ← معطّل = يظهر السعر فقط
```

**النتيجة:**
- معطّل: `99.99`
- مفعّل: `99.99 ريال`

---

## 6️⃣ **QR Code**

```
✅ بدون خلفية بيضاء
✅ شفاف تماماً
✅ واضح (crisp-edges)
```

---

## 🎨 **أمثلة تصاميم جاهزة:**

### مثال 1: ملصق كلاسيكي

```yaml
Text Alignment:
  Name: Center
  Foreign Name: Center
  Code: Center
  Price: Center

Font Weight:
  All: Bold ✓

Font Style:
  All: Normal

Result:
       عطر الورد الجوري
        Rose Perfume
          ADF-001
           99.99
```

---

### مثال 2: ملصق حديث

```yaml
Text Alignment:
  Name: Right
  Foreign Name: Left
  Code: Center
  Price: Center

Font Weight:
  Name: Bold ✓
  Foreign Name: Normal
  Code: Bold ✓
  Price: Bold ✓

Font Style:
  Foreign Name: Italic ✓

Result:
عطر الورد الجوري         (right, bold)
Rose Perfume             (left, italic)
      ADF-001            (center, bold)
       99.99             (center, bold)
```

---

### مثال 3: ملصق أنيق

```yaml
Text Alignment:
  Name: Center
  Foreign Name: Center
  Code: Center
  Price: Center

Font Sizes:
  Name: 18pt
  Foreign Name: 14pt
  Code: 36pt              ← كبير جداً
  Price: 24pt

Font Weight:
  Code: Bold ✓
  Price: Bold ✓
  Others: Normal

Font Style:
  All: Normal

Show Currency: No

Result:
    عطر الورد الجوري      18pt, normal
     Rose Perfume         14pt, normal
       ADF-001            36pt, bold
        99.99             24pt, bold (بدون ريال)
```

---

## 🎯 **كيفية الاستخدام:**

### الخطوة 1: افتح القالب
```
Label Templates → افتح قالبك → Display Options
```

### الخطوة 2: عدّل الإعدادات
```
Font Sizes:
- Name: 16
- Foreign Name: 12
- Code: 28
- Price: 20

Text Alignment:
- Name: Center         ← وسط
- Foreign Name: Center
- Code: Center
- Price: Center

Font Weight:
- Name: ✓ Bold
- Foreign Name: ☐ Normal
- Code: ✓ Bold
- Price: ✓ Bold

Font Style:
- Foreign Name: ✓ Italic  ← مائل
- Others: ☐ Normal

Price Display:
- Show Currency: ☐ معطّل
```

### الخطوة 3: احفظ
```
Save
```

### الخطوة 4: جرّب
```
Quick Print → Preview in Browser
→ شاهد التصميم!
```

---

## 📋 **ملخص عناصر التحكم:**

```
✅ 5 أحجام خطوط
✅ 4 اتجاهات نص (Left/Center/Right)
✅ 4 خيارات Bold (On/Off)
✅ 4 خيارات Italic (On/Off)
✅ رمز العملة (On/Off)
✅ QR شفاف (بدون خلفية)
✅ معاينة قبل الطباعة
✅ طباعة A4
```

**المجموع: 22 عنصر تحكم!** 🎉

---

## 🚀 **الآن:**

```
1. Upgrade الموديول
2. عدّل القالب:
   - Text Alignment: Center للكل
   - Font Weight: Bold للكود والسعر
   - Font Style: Italic للاسم الأجنبي
   - Show Currency: Off
3. Save
4. Preview → شاهد النتيجة!
```

---

**استمتع بالتحكم الكامل في التصميم!** 🎨✨

