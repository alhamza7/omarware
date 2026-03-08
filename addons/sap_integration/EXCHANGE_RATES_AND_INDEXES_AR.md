# Exchange Rates and Indexes في SAP — الاتصال عبر Service Layer

## أين توجد في SAP؟

شاشة **أسعار الصرف والفهارس (Exchange Rates and Indexes)** في SAP Business One:

- **Administration** → **Exchange Rates and Indexes**
- أو: **Administration** → **Setup** → **Company Details** → **Currencies** / **Exchange Rates**

هنا يتم تحديد **سعر الصرف لليوم** لكل عملة (مثلاً 1560 لـ IQD) بحيث تستخدم **الفواتير والأوامر الجديدة** هذا السعر.

الجدول في قاعدة البيانات: **ORTT** (ويُستخدم أيضاً للفهارس مع جدول OIDX).

---

## كيف الاتصال بها عبر Service Layer؟

### 1) قائمة العملات (بدون الأسعار اليومية)

**Endpoint:** `GET /b1s/v1/Currencies`

**مثال طلب من Odoo:**
```python
connection = backend.get_connection()
currencies = connection.get_currencies_list(top=50)
# النتيجة: قائمة فيها Code, Name, DocumentsCode, Decimals, ...
# مثال: [{"Code": "IQD", "Name": "Iraq Dinar", ...}, ...]
```

**ملاحظة:** الـ entity **Currencies** يعيد **البيانات الأساسية للعملات** فقط (الرمز، الاسم، الخ)، ولا يحتوي على حقل **سعر الصرف لليوم**. سعر اليوم مخزّن في جدول ORTT.

---

### 2) سعر الصرف لليوم (من جدول ORTT)

الطريقة الموثّقة في SAP لقراءة السعر لـ (عملة + تاريخ) هي:

- **DI API:** `GetCurrencyRate(Currency, Date)` — يقرأ من ORTT.
- **Service Layer:** يُفترض أن يكون متاحاً عبر **CompanyService_GetCurrencyRate** بنفس الفكرة.

**مثال استدعاء (عند دعم الـ endpoint):**
```python
# POST CompanyService_GetCurrencyRate
# Body: {"Currency": "IQD", "Date": "2026-03-06"}
rate = connection.get_exchange_rate_for_currency_and_date("IQD", "2026-03-06")
# أو لليوم الحالي:
rate = connection.get_exchange_rate_for_currency_and_date("IQD")
```

في الكود الحالي يتم تجربة هذا الـ endpoint أولاً في `get_iqd_exchange_rate()`. إذا كانت نسخة الـ Service Layer عندك تقبل payload مختلف (أسماء حقول أو بنية أخرى)، يمكن تعديل الـ payload حسب وثائق نسختك.

---

### 3) إن لم يعمل CompanyService_GetCurrencyRate

جرّبنا أسماء entities أخرى لجدول ORTT (مثل ExchangeRates, Currency_Rates, CurrencyCodes_Details، …) ولم تكن متاحة أو معرّفة بنفس الأسماء في بيئة الاختبار. لذلك الاعتماد الحالي هو:

1. **CompanyService_GetCurrencyRate** (إن قبلته نسختك).
2. ثم **DocRate** من أحدث مستند IQD **بتاريخ اليوم** (فاتورة أو أمر).
3. ثم **DocRate** من أحدث مستند IQD بأي تاريخ.

---

## الدوال المتوفرة في الكود

| الدالة | الوصف |
|--------|--------|
| `get_currencies_list(top=50)` | قائمة العملات من **Currencies** (بدون أسعار يومية). |
| `get_exchange_rate_for_currency_and_date(currency_code, rate_date=None)` | محاولة جلب سعر الصرف لـ (عملة + تاريخ) عبر **CompanyService_GetCurrencyRate**. |
| `get_iqd_exchange_rate()` | جلب سعر IQD/USD الحالي (CompanyService_GetCurrencyRate ثم entities أخرى ثم DocRate من المستندات). |

---

## خلاصة

- **Exchange Rates and Indexes** في SAP = إعداد أسعار الصرف (والفهارس) لليوم، والجدول الأساسي **ORTT**.
- **الاتصال:**
  - قائمة العملات: **GET Currencies** ← نستخدمها عبر `get_currencies_list()`.
  - سعر اليوم لـ (عملة + تاريخ): **CompanyService_GetCurrencyRate** (إن كان مدعوماً) ← نستخدمه في `get_exchange_rate_for_currency_and_date()` و `get_iqd_exchange_rate()`.
- إن لم يكن **CompanyService_GetCurrencyRate** يعمل في نسختك، يمكن الاعتماد على **DocRate** من المستندات (كما هو مُطبَّق الآن) أو مراجعة وثائق الـ Service Layer لنسختك لمعرفة الـ endpoint أو الـ payload الصحيح.
