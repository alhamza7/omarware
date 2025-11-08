# حل مشكلة عدم ظهور المنتجات في POS للمستخدم الجديد

## المشكلة:
عند إضافة مستخدم جديد، لا تظهر له المنتجات في POS.

## الأسباب المحتملة:

### 1. المستخدم ليس لديه صلاحيات POS
**الحل:**
- اذهب إلى: **Settings** → **Users & Companies** → **Users**
- افتح المستخدم الجديد
- في تبويب **Access Rights**:
  - تأكد من تحديد **Point of Sale / User** أو **Point of Sale / Manager**
  - تأكد من تحديد **Sales / User** (لرؤية المنتجات)

### 2. المنتجات غير متاحة في POS
**الحل:**
- اذهب إلى: **Inventory** → **Products** → **Products**
- افتح المنتج
- في تبويب **Sales**:
  - تأكد من تحديد **Can be Sold**
  - تأكد من تحديد **Available in Point of Sale** (إن وجد)

### 3. صلاحيات قراءة المنتجات
**الحل:**
- اذهب إلى: **Settings** → **Users & Companies** → **Users**
- افتح المستخدم الجديد
- في تبويب **Access Rights**:
  - تأكد من وجود **Product / User** أو **Product / Manager**

### 4. إعدادات POS Config
**الحل:**
- اذهب إلى: **Point of Sale** → **Configuration** → **Point of Sale**
- افتح إعدادات POS
- في تبويب **Products**:
  - تأكد من عدم وجود قيود على المنتجات
  - تأكد من أن **Available Product Categories** فارغ أو يحتوي على الفئات المطلوبة

## أوامر SQL للتحقق:

```sql
-- التحقق من صلاحيات المستخدم
SELECT 
    u.login,
    g.name as group_name
FROM res_users u
JOIN res_groups_users_rel gur ON u.id = gur.uid
JOIN res_groups g ON gur.gid = g.id
WHERE u.login = 'username_here';

-- التحقق من صلاحيات المنتجات
SELECT 
    ima.name,
    ima.perm_read,
    ima.perm_write,
    g.name as group_name
FROM ir_model_access ima
JOIN res_groups g ON ima.group_id = g.id
WHERE ima.model_id = (SELECT id FROM ir_model WHERE model = 'product.product')
AND g.id IN (
    SELECT gid FROM res_groups_users_rel WHERE uid = (SELECT id FROM res_users WHERE login = 'username_here')
);
```

## الحل السريع:

1. **إضافة صلاحيات POS للمستخدم:**
   - Settings → Users → اختر المستخدم
   - Access Rights → أضف "Point of Sale / User"

2. **التحقق من المنتجات:**
   - Inventory → Products
   - تأكد من أن المنتجات مفعلة ويمكن بيعها

3. **تحديث الوحدة:**
   ```bash
   python3 odoo-bin -c odoo.conf -d lugal --http-port=8070 -u pos_perfume_custom --dev=reload
   ```

