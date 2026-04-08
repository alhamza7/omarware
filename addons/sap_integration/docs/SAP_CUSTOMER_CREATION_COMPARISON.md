# مقارنة: إنشاء العميل في SAP — الدليل vs التنفيذ الحالي

## الملخص السريع

| الجانب | **دليل التكامل (الطريقة الموصى بها)** | **التنفيذ الحالي في المشروع** |
|--------|--------------------------------------|--------------------------------|
| **CardCode** | ❌ لا يُرسل — SAP ينشئه من السلسلة (Series) | ✅ يُرسل — يُولَّد في Odoo (get_next_card_code أو IBG06666) |
| **Notes** | ✅ إلزامي (نص غير فارغ) | ❌ غير مُرسل |
| **Address** | ✅ إلزامي كنص بسيط (string) | ⚠️ يُرسل فقط إذا وُجد street؛ قد يكون فارغاً |
| **CardType** | `"cCustomer"` | `"C"` (صيغة مختصرة) |
| **Series** | ثابت: `72` | ديناميكي: من `get_ibg_series_number()` |
| **GroupCode** | موصى به: `100` | ❌ غير مُرسل |
| **تسلسل العملية** | Login → POST بدون CardCode → استخراج CardCode من الاستجابة → (اختياري) PATCH → Logout | Login → POST مع CardCode مُولَّد → حفظ CardCode المُرجَع في `ref` |

---

## 1. CardCode (كود العميل)

### الدليل (الطريقة الموصى بها)
- **لا ترسل** `CardCode` في طلب الإنشاء.
- SAP ينشئ الكود تلقائياً من **السلسلة الرقمية (Numbering Series)** ويُرجعها في الاستجابة.
- يقلل التعارضات ويضمن توافق الكود مع إعدادات SAP.

### التنفيذ الحالي
- **يُرسل** `CardCode` دائماً عند إنشاء عميل جديد.
- التوليد في `res_partner_sap.py` → `_prepare_partner_data_for_sap()`:
  - استدعاء `connection.get_next_card_code('IBG')` لآخر كود ثم +1.
  - أو استخدام افتراضي `"IBG06666"` إذا فشل الاستعلام.
- الكود يُرسل إلى SAP مع الطلب.

**الخلاصة:** الدليل يوصي بعدم الإرسال وترك SAP يولد الكود؛ المشروع يولد الكود في Odoo ويرسله. إذا كانت السلسلة في SAP (مثلاً 72) تُنتج تنسيقاً مثل `IBG05743`، فإرسال كود مُولَّد من Odoo قد يسبب تعارضاً أو خطأ -4002 (سلسلة غير معرفة) إذا لم يكن التنسيق مطابقاً.

---

## 2. Notes و Address (المفتاح الأساسي في الدليل)

### الدليل (الطريقة الموصى بها)
- **Notes** و **Address** إلزاميان **معاً** وقيمتهما غير فارغة.
- غالباً لحل مشكلة validation في SAP (مثل خطأ 203082023).
- يمكن أن تكون القيمة بسيطة (مثل المدينة): `"Notes": "بغداد"`, `"Address": "بغداد"`.

### التنفيذ الحالي
- **Notes:** غير موجود في `_prepare_partner_data_for_sap()` ولا في `map_odoo_partner_to_sap()`.
- **Address:**
  - في `res_partner_sap`: يُضاف `Address = partner.street` فقط إذا وُجد `partner.street`؛ قد يكون فارغاً للعملاء الجدد.
  - في `sap_data_mapper.map_odoo_partner_to_sap()`: يُرسل `Address` كـ **كائن** (object) وليس كنص:
    ```python
    sap_data['Address'] = {
        'Address': ...,
        'Address2': ...,
        'City': ...,
    }
    ```
  - لا يُضاف حقل **Notes** في أي من المسارين.

**الخلاصة:** عدم إرسال Notes وعدم ضمان Address كنص غير فارغ قد يكون سبب فشل إنشاء العميل في بعض بيئات SAP (حسب الدليل). الدليل يوصي بإرسالهما دائماً كنص غير فارغ.

---

## 3. CardType

### الدليل
- يستخدم: `"CardType": "cCustomer"`.

### التنفيذ الحالي
- في `res_partner_sap._prepare_partner_data_for_sap()`: `'CardType': 'C'`.
- في `sap_data_mapper.map_odoo_partner_to_sap()`: `'CardType': 'cCustomer'`.

**الخلاصة:** المشروع يستخدم مسارين: واجهة الـ partner (Odoo/POS) تستخدم `'C'`، والـ mapper يستخدم `'cCustomer'`. حسب إصدار SAP قد يقبل الاثنين؛ يفضّل توحيد استخدام `"cCustomer"` ليتوافق مع الدليل ومع باقي الكود (sap_binding، config).

---

## 4. Series و GroupCode

### الدليل
- **Series:** ثابت `72` (رقم سلسلة العملاء).
- **GroupCode:** موصى به `100` (مجموعة الشريك).

### التنفيذ الحالي
- **Series:** يُؤخذ ديناميكياً من `connection.get_ibg_series_number()` في `res_partner_sap` فقط؛ الـ mapper لا يضيف Series.
- **GroupCode:** غير مُرسل في `_prepare_partner_data_for_sap()` ولا في `map_odoo_partner_to_sap()`.

**الخلاصة:** الدليل يثبت Series ويرشّح GroupCode؛ المشروع يعتمد Series ديناميكي ولا يرسل GroupCode. إذا كانت السلسلة 72 هي المستخدمة لـ IBG في بيئتك، توحيد القيمة يقلل الالتباس.

---

## 5. تسلسل العملية

### الدليل
1. Login → الحصول على session/cookies.
2. **POST** `/BusinessPartners` مع: CardName, CardType, Notes, Address (بدون CardCode).
3. استخراج **CardCode** من استجابة SAP.
4. (اختياري) **PATCH** على نفس الشريك لتحديث حقول إضافية (Cellular, U_ST_BP02, ...).
5. Logout.

### التنفيذ الحالي
1. الاتصال عبر `backend.get_connection()` (Login داخلي).
2. **POST** `/BusinessPartners` مع بيانات من `_prepare_partner_data_for_sap()` أو `map_odoo_partner_to_sap()` (يتضمن CardCode في مسار res_partner).
3. من الاستجابة: `result.get('CardCode')` يُحفظ في `partner.ref` و `sap_synced = True`.
4. لا يوجد PATCH اختياري ممنهج بعد الإنشاء في الكود الحالي (فقط update عند التعديل لاحقاً).
5. الجلسة تُغلق أو تنتهي حسب إدارة الـ backend.

**الخلاصة:** التسلسل العام متشابه (Login → Create → حفظ CardCode)، لكن تفاصيل الـ payload (CardCode، Notes، Address) تختلف كما في الجداول أعلاه.

---

## 6. أين يُستخدم كل مسار؟

| المسار | الملف | متى يُستدعى |
|--------|------|-------------|
| إنشاء من واجهة الشريك (Odoo/POS) | `res_partner_sap.py` → `_send_to_sap()` → `_prepare_partner_data_for_sap()` | عند إنشاء `res.partner` جديد بدون `ref` (من create أو web_save). |
| مزامنة عميل إلى SAP | `sap_customer_service.py` → `sync_customer_to_sap()` → `map_odoo_partner_to_sap()` | عند استدعاء خدمة المزامنة (يدوياً أو من ويزارد/جدولة). |

كلا المسارين ينتهيان إلى:
- `sap_service_layer.py` → `create_business_partner(partner_data)` → POST إلى `/BusinessPartners`.

---

## 7. توصيات للتطابق مع الدليل

1. **عدم إرسال CardCode عند الإنشاء**
   - في `_prepare_partner_data_for_sap()`: عند إنشاء جديد (بدون `partner.ref` أو بدون `sap_synced`) لا تضف `CardCode` إلى `partner_data`.
   - الاعتماد على القيمة المُرجعة من SAP وحفظها في `partner.ref`.

2. **إرسال Notes و Address دائماً كنص غير فارغ**
   - في `_prepare_partner_data_for_sap()` و `map_odoo_partner_to_sap()`:
     - إضافة `Notes`: مثلاً `partner.city or partner.name or "—"`.
     - إضافة `Address` كـ **string**: مثلاً عنوان واحد مثل `partner.street or partner.city or partner.name or "—"`.
   - التأكد من عدم ترك أي منهما فارغاً عند إنشاء عميل جديد.

3. **توحيد CardType**
   - استخدام `"cCustomer"` في `res_partner_sap._prepare_partner_data_for_sap()` بدلاً من `"C"` ليتوافق مع الدليل وباقي الكود.

4. **إضافة GroupCode (اختياري لكن موصى به)**
   - إضافة `GroupCode: 100` (أو القيمة المناسبة لبيئتك) في payload الإنشاء في كلا المسارين.

5. **Series**
   - الإبقاء على القيمة من `get_ibg_series_number()` إذا كانت تُرجع 72 أو السلسلة الصحيحة لـ IBG؛ أو تثبيت 72 إذا أوصى الدليل بذلك لبيئة NBS_TEST.

6. **معالجة الأخطاء**
   - استخدام نفس رموز الأخطاء المذكورة في الدليل (مثل -4002، -1116 مع 203082023) في الـ logging والرسائل للمستخدم.

---

## 8. خلاصة المقارنة

- **الدليل** يعتمد على: عدم إرسال CardCode، وإرسال Notes + Address كنص غير فارغ، و CardType `cCustomer`، و Series/GroupCode واضحين.
- **المشروع الحالي** يولد CardCode ويرسله، ولا يرسل Notes، ولا يضمن Address كنص إلزامي، ويستخدم CardType `'C'` في مسار الـ partner.
- لجعل إنشاء العملاء في المشروع متوافقاً مع الدليل وتقليل أخطاء الـ validation في SAP، يُفضّل تطبيق التوصيات أعلاه (خصوصاً عدم إرسال CardCode عند الإنشاء، وإضافة Notes و Address إلزاميين).

---

*تم إعداد المقارنة بناءً على دليل التكامل (إنشاء عميل في SAP من برنامج آخر) والكود في `addons/sap_integration`.*
