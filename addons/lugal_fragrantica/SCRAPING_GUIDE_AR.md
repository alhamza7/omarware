# 🕷️ دليل Scraping العطور الجديدة

عندما يطلب مستخدم عطراً غير موجود في قاعدة البيانات

---

## 📋 السيناريو

1. المستخدم يفتح منتجاً في Odoo
2. يبحث عن عطر في تاب Fragrantica لكن لا يجده
3. يضع رابط Fragrantica في حقل "Fragrantica URL (Pending)"
4. يضغط "Create Request"
5. يتم إنشاء **Pending Request**

**الآن دورك كمدير:**
- جلب بيانات العطر من Fragrantica
- إضافته لقاعدة البيانات
- تحديث السيرفر

---

## 🔍 عرض الطلبات المعلقة

### في Odoo:

اذهب إلى: **Fragrantica → Pending Requests**

ستجد قائمة بجميع الطلبات، مثلاً:
```
- https://www.fragrantica.com/perfume/Dior/Sauvage-31861.html
- https://www.fragrantica.com/perfume/Chanel/Bleu-de-Chanel-9099.html
```

---

## 🛠️ جلب البيانات

### الطريقة 1: استخدام السكريبت الموجود

في مجلد `fregran/`، لديك عدة سكريبتات:

#### أ) ScrapingBee (الأسهل - لكن مدفوع)

```bash
cd /d/capo_dev/Lugal-ai/fregran

# تعديل ملف لإضافة الروابط المطلوبة
# افتح ملف Excel أو أنشئ ملف جديد بالروابط

# شغّل السكريبت
python scrapingbee_auto.py
```

**ملاحظة:** يحتاج API key من ScrapingBee

#### ب) Selenium (مجاني)

**المتطلبات:**
```bash
pip install selenium webdriver-manager
```

**الاستخدام:**
1. أنشئ ملف `pending_urls.txt` واكتب فيه الروابط (رابط في كل سطر)
2. شغّل سكريبت مخصص أو عدّل السكريبت الموجود

**مثال سكريبت بسيط:**

```python
# fregran/scrape_pending.py
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# قراءة الروابط من ملف
with open('pending_urls.txt', 'r') as f:
    urls = [line.strip() for line in f if line.strip()]

# إعداد Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('perfumes.db')
cursor = conn.cursor()

for url in urls:
    print(f"جلب: {url}")
    
    driver.get(url)
    time.sleep(5)  # انتظار تحميل الصفحة
    
    try:
        # جلب البيانات (مثال)
        name = driver.find_element(By.CSS_SELECTOR, 'h1').text
        # ... جلب باقي البيانات
        
        # حفظ في قاعدة البيانات
        cursor.execute("""
            INSERT INTO perfumes (url, name, ...)
            VALUES (?, ?, ...)
        """, (url, name, ...))
        conn.commit()
        
        print(f"✓ تم: {name}")
    except Exception as e:
        print(f"✗ خطأ: {e}")
    
    time.sleep(7)  # تأخير بين الطلبات

driver.quit()
conn.close()
```

---

## 📤 تحديث السيرفر

بعد إضافة العطور الجديدة:

### 1. تجهيز التصدير

```bash
cd /d/capo_dev/Lugal-ai/fragrantica_data_export
python prepare_export.py
```

### 2. نقل قاعدة البيانات المحدثة فقط

```bash
# نقل قاعدة البيانات الجديدة للسيرفر
scp perfumes.db user@server:/tmp/perfumes_updated.db
```

### 3. على السيرفر

```bash
# استبدال قاعدة البيانات
sudo cp /tmp/perfumes_updated.db \
  /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db

sudo chown odoo:odoo \
  /opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db
```

### 4. استيراد العطور الجديدة في Odoo

في Odoo:
1. اذهب إلى: **Fragrantica → Configuration → Import Data**
2. **لا تفعّل** "Import Images" إذا كنت تريد السرعة
3. اضغط **Start Import**

**ملاحظة:** العطور الموجودة مسبقاً لن تتكرر بفضل `fragrantica_id` unique constraint.

### 5. تحديث حالة الطلبات

في Odoo:
1. اذهب إلى: **Fragrantica → Pending Requests**
2. افتح كل طلب تم إنجازه
3. اضغط **Mark as Completed**

---

## 🔄 طريقة أسهل: Import Incremental

بدلاً من إعادة استيراد كل شيء:

```python
# في Odoo → Settings → Technical → Python Code

import sqlite3

# فتح قاعدة البيانات الجديدة
db_path = '/opt/odoo/addons/lugal_fragrantica/static/fragrantica_data/perfumes.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# جلب العطور الجديدة فقط (مثلاً آخر 10)
cursor.execute("SELECT * FROM perfumes ORDER BY id DESC LIMIT 10")

Perfume = env['fragrantica.perfume']

for row in cursor:
    # تحقق إذا كان موجوداً
    existing = Perfume.search([('fragrantica_id', '=', row['id'])], limit=1)
    if existing:
        continue
    
    # إضافة العطر الجديد
    perfume = Perfume.create({
        'fragrantica_id': row['id'],
        'name': row['name'] or 'Unknown',
        'arabic_name': row['arabic_name'],
        'brand_name': row['brand_name'],
        'year': row['year'],
        'url': row['url'],
        'description_full': row['description_full'],
        # ... باقي الحقول
    })
    
    print(f"✓ Added: {perfume.name}")

conn.close()
```

---

## 📊 متابعة الطلبات

### عرض إحصائيات:

```python
# في Python Console في Odoo

# عدد الطلبات المعلقة
pending = env['fragrantica.pending.request'].search_count([('state', '=', 'pending')])
print(f"Pending requests: {pending}")

# عرض آخر 5 طلبات
requests = env['fragrantica.pending.request'].search([], limit=5, order='create_date desc')
for req in requests:
    print(f"{req.state}: {req.fragrantica_url}")
```

---

## 🎯 Best Practices

### ✅ افعل:
- احفظ نسخة احتياطية من `perfumes.db` قبل التعديل
- اختبر السكريبت على عطر واحد أولاً
- استخدم تأخير 5-10 ثوانٍ بين كل طلب
- راقب Pending Requests بانتظام

### ❌ لا تفعل:
- لا تشغّل Scraping بسرعة (تجنب الحظر)
- لا تستخدم ScrapingBee بدون API key
- لا تحذف قاعدة البيانات القديمة قبل التأكد من الجديدة

---

## 🐛 حل المشاكل

### المشكلة: السكريبت يُحظر من Fragrantica

**الحل:**
- استخدم ScrapingBee أو خدمة proxy
- زِد التأخير بين الطلبات
- استخدم User-Agent مختلف

### المشكلة: بيانات ناقصة

**الحل:**
- تحقق من HTML structure في Fragrantica
- قد يكونوا غيّروا التصميم
- عدّل CSS selectors في السكريبت

### المشكلة: صور العطور الجديدة لا تظهر

**الحل:**
- بعد إضافة العطر، شغّل:
  ```python
  perfume = env['fragrantica.perfume'].browse(PERFUME_ID)
  perfume.load_image_from_static()
  ```

---

## 🔗 روابط مفيدة

- **Fragrantica:** https://www.fragrantica.com
- **ScrapingBee:** https://www.scrapingbee.com
- **Selenium Docs:** https://selenium-python.readthedocs.io/

---

## 📝 ملاحظات

- Fragrantica لديه حماية ضد scraping
- استخدم هذا بمسؤولية واحترم شروط الاستخدام
- للاستخدام الشخصي/التجاري المحدود فقط

---

**💡 نصيحة:** أسهل طريقة هي جمع كل الطلبات لمدة أسبوع، ثم جلبها دفعة واحدة بدلاً من واحد واحد.







