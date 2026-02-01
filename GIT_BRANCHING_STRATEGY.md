# استراتيجية Git Branching للمشروع

## 🌳 هيكل الـ Branches

```
main (production)          ← السيرفر البعيد (الإنتاج)
  ↓
development (dev)          ← التطوير المحلي
  ↓
feature/feature-name       ← ميزات جديدة (اختياري)
```

---

## 📋 وصف الـ Branches

### 1️⃣ `main` - الإنتاج (Production)

```
✅ الاستخدام: السيرفر البعيد فقط
✅ الحالة: مستقر دائماً
✅ النشر: تلقائي على السيرفر
⚠️  لا تعمل عليه مباشرة!
```

**الخصائص:**
- كود مستقر ومختبر
- يعمل على السيرفر البعيد
- لا يحتوي على أخطاء
- تحديثات محدودة ومنظمة

**متى تحدثه؟**
- بعد اختبار كامل على `development`
- عند إصدار نسخة جديدة
- عند إصلاحات حرجة فقط

### 2️⃣ `development` - التطوير

```
✅ الاستخدام: التطوير المحلي
✅ الحالة: قيد التطوير
✅ الاختبار: جميع الميزات الجديدة
✅ العمل اليومي: هنا
```

**الخصائص:**
- التطوير اليومي
- الاختبار المحلي
- الميزات الجديدة
- الإصلاحات والتحسينات

**متى تستخدمه؟**
- ✅ أي تطوير جديد
- ✅ اختبار ميزات
- ✅ إصلاح أخطاء
- ✅ التجارب

---

## 🔄 سير العمل (Workflow)

### للتطوير اليومي:

```bash
# 1. تأكد أنك على branch development
git checkout development

# 2. اسحب آخر التحديثات
git pull origin development

# 3. اعمل على التعديلات
# ... تعديل الملفات ...

# 4. احفظ التغييرات
git add .
git commit -m "وصف التغييرات"

# 5. ارفع على development
git push origin development
```

### لنشر على الإنتاج (Production):

```bash
# 1. تأكد أن development مستقر ومختبر
git checkout development
./venv/bin/python odoo-bin -c odoo_local.conf -u all --stop-after-init

# 2. انتقل لـ main
git checkout main

# 3. ادمج من development
git merge development

# 4. ارفع على main (السيرفر)
git push origin main

# 5. ارجع لـ development للعمل
git checkout development
```

---

## 📝 قواعد مهمة

### ✅ افعل:

```bash
✅ اعمل دائماً على development
✅ اختبر كل شيء قبل الدمج في main
✅ اكتب رسائل commit واضحة
✅ اسحب التحديثات قبل البدء بالعمل
✅ ارفع تغييراتك بانتظام
```

### ❌ لا تفعل:

```bash
❌ لا تعمل مباشرة على main
❌ لا تدمج كود غير مختبر في main
❌ لا تعمل force push على main
❌ لا ترفع ملفات حساسة (.env, passwords)
❌ لا تنسى pull قبل push
```

---

## 🚀 أوامر سريعة

### التبديل بين Branches:

```bash
# الانتقال لـ development
git checkout development

# الانتقال لـ main
git checkout main

# معرفة أي branch أنت عليه
git branch

# معرفة الحالة
git status
```

### التحديث والمزامنة:

```bash
# سحب آخر تحديثات development
git checkout development
git pull origin development

# سحب آخر تحديثات main
git checkout main
git pull origin main
```

### إنشاء feature branch (اختياري):

```bash
# إذا أردت ميزة كبيرة منفصلة
git checkout development
git checkout -b feature/new-feature-name

# اعمل على الميزة
# ...

# ادمجها في development
git checkout development
git merge feature/new-feature-name

# احذف الـ feature branch
git branch -d feature/new-feature-name
```

---

## 🎯 سيناريوهات عملية

### سيناريو 1: إضافة ميزة جديدة

```bash
# 1. ابدأ من development
git checkout development
git pull origin development

# 2. اعمل على الميزة
# ... التطوير والاختبار محلياً ...

# 3. احفظ وارفع
git add .
git commit -m "Add: new feature description"
git push origin development

# 4. اختبر جيداً على development
# ... اختبار شامل ...

# 5. إذا نجح، انشر على main
git checkout main
git merge development
git push origin main
```

### سيناريو 2: إصلاح خطأ عاجل (Hotfix)

```bash
# 1. خطأ حرج على السيرفر؟
git checkout main
git pull origin main

# 2. أصلح الخطأ مباشرة
# ... إصلاح سريع ...

# 3. ارفع الإصلاح
git add .
git commit -m "Fix: critical bug description"
git push origin main

# 4. ادمج الإصلاح في development
git checkout development
git merge main
git push origin development
```

### سيناريو 3: تجربة فكرة جديدة

```bash
# 1. أنشئ feature branch
git checkout development
git checkout -b experiment/new-idea

# 2. جرب الفكرة
# ... تجارب ...

# 3. إذا نجحت
git checkout development
git merge experiment/new-idea
git branch -d experiment/new-idea

# 4. إذا فشلت
git checkout development
git branch -D experiment/new-idea  # احذفها
```

---

## 🔍 التحقق من الحالة

### معرفة أي branch تستخدم:

```bash
git branch
# * development  ← علامة النجمة تشير للـ branch الحالي
#   main
```

### معرفة الفروقات:

```bash
# الفرق بين development و main
git diff main..development

# الفرق بين local و remote
git diff development origin/development
```

### معرفة آخر التحديثات:

```bash
# آخر 10 commits على development
git log development --oneline -10

# آخر 10 commits على main
git log main --oneline -10
```

---

## 📊 الحالة المثالية

```
┌─────────────────────────────────────────────┐
│                                             │
│  main (production)                          │
│    ✅ مستقر                                 │
│    ✅ على السيرفر                           │
│    ✅ لا أخطاء                              │
│    ⬆️  تحديثات محدودة                       │
│                                             │
└─────────────────────────────────────────────┘
                    ⬆️ merge
┌─────────────────────────────────────────────┐
│                                             │
│  development                                │
│    🔨 التطوير اليومي                       │
│    🧪 الاختبار                             │
│    ✨ الميزات الجديدة                      │
│    🏠 محلي (localhost)                     │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🛡️ الحماية

### حماية main من الأخطاء:

```bash
# لا تسمح بـ force push على main
# يمكن إعداد هذا على GitHub:
# Settings → Branches → Branch protection rules
# ✅ Require pull request reviews
# ✅ Require status checks to pass
# ✅ Restrict who can push
```

---

## 📚 مصطلحات مهمة

```
main        = البرانش الرئيسي (الإنتاج)
development = برانش التطوير
feature     = برانش للميزات الجديدة
hotfix      = إصلاح سريع
merge       = دمج البرانشات
commit      = حفظ التغييرات
push        = رفع للسيرفر
pull        = سحب من السيرفر
checkout    = التبديل بين البرانشات
```

---

## 🎯 الخلاصة

```
✅ development: للعمل اليومي والتطوير (محلي)
✅ main: للإنتاج والسيرفر (بعيد)
✅ اختبر على development أولاً
✅ انشر على main بعد التأكد
✅ اعمل دائماً على development
```

---

## 🚀 البدء السريع

```bash
# الإعداد الأولي (مرة واحدة فقط)
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
git checkout -b development
git push -u origin development

# العمل اليومي
git checkout development
git pull origin development
# ... اعمل على الكود ...
git add .
git commit -m "وصف التغيير"
git push origin development

# النشر على الإنتاج
git checkout main
git merge development
git push origin main
git checkout development  # ارجع للتطوير
```

---

**📌 تذكر:**
- 🏠 `development` = بيتك (اعمل هنا)
- 🏢 `main` = المكتب (انشر هنا بعد التأكد)

---

**آخر تحديث:** 2026-02-01  
**الحالة:** ✅ جاهز للاستخدام
