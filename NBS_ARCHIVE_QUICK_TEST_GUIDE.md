# 🚀 NBS Archive - دليل الاختبار السريع

## ⚡ Quick Start

### 1. الوصول إلى النظام
```bash
# Odoo running on:
http://localhost:8070

# Database: lugal_nbs
# Username: admin
# Password: admin
```

---

## 🧪 اختبار الـ APIs الجديدة

### المتطلبات:
1. JWT Token صالح
2. مستند موجود للاختبار
3. مرفق موجود للاختبار

---

## 📝 Test Scenarios

### Scenario 1: رفع عدة مرفقات لمستند واحد

```bash
# Step 1: إنشاء مستند جديد (أو استخدم موجود)
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "Test Document for Multiple Attachments",
        "department_id": 1,
        "document_type_id": 1
    },
    "id": 1
}'

# Step 2: رفع عدة مرفقات دفعة واحدة
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "object",
        "method": "execute",
        "args": ["nbs.document.attachment", "upload_multiple_attachments", 
            [DOCUMENT_ID], 
            {
                "attachments": [
                    {
                        "name": "Contract Page 1",
                        "file_name": "contract_p1.pdf",
                        "file_data": "base64_encoded_data_here...",
                        "description": "First page of contract"
                    },
                    {
                        "name": "Contract Page 2",
                        "file_name": "contract_p2.pdf",
                        "file_data": "base64_encoded_data_here...",
                        "description": "Second page of contract"
                    }
                ]
            }
        ]
    },
    "id": 2
}'
```

---

### Scenario 2: Soft Delete و Restore

```bash
# Step 1: نقل مرفق إلى سلة المحذوفات
curl -X DELETE 'http://localhost:8070/api/documents/1/attachments/5' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'

# Step 2: عرض المرفق (سيظهر is_deleted=true)
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {},
    "id": 3
}'

# Step 3: استعادة المرفق
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {},
    "id": 4
}'

# Step 4: نقل مستند كامل إلى سلة المحذوفات
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "reason": "تم إلغاء المشروع"
    },
    "id": 5
}'

# Step 5: عرض سلة المحذوفات
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {},
    "id": 6
}'
```

---

### Scenario 3: Bulk Upload

```bash
# Step 1: بدء عملية رفع جماعي
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "department_id": 1,
        "document_type_id": 1,
        "folder_id": null,
        "confidentiality_level": "internal",
        "auto_ocr": false
    },
    "id": 7
}'

# Response: { "job_id": "uuid-here", "id": 15 }

# Step 2: رفع الملفات
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "files": [
            {
                "file_name": "doc1.pdf",
                "file_data": "base64_data_1...",
                "name": "Document 1",
                "description": "First doc"
            },
            {
                "file_name": "doc2.pdf",
                "file_data": "base64_data_2...",
                "name": "Document 2",
                "description": "Second doc"
            }
        ]
    },
    "id": 8
}'

# Step 3: تتبع التقدم (كرر هذا الطلب للحصول على التحديثات)
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {},
    "id": 9
}'

# Step 4: عرض جميع عمليات الرفع
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "status": "completed",
        "limit": 10,
        "offset": 0
    },
    "id": 10
}'
```

---

### Scenario 4: تعديل مرفق

```bash
# تحديث اسم ووصف المرفق
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "Updated Name",
        "description": "Updated description"
    },
    "id": 11
}'

# تحديث الملف نفسه
curl -X POST 'http://localhost:8070/jsonrpc' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "file_data": "new_base64_encoded_data...",
        "file_name": "updated_file.pdf"
    },
    "id": 12
}'
```

---

## 🔍 التحقق من النتائج

### من خلال Odoo UI:
```
1. افتح http://localhost:8070
2. سجل الدخول
3. اذهب إلى: NBS Archive > Audit Logs
4. ابحث عن:
   - attachment_updated
   - attachment_deleted
   - document_soft_deleted
   - multiple_attachments_upload
```

### من خلال PostgreSQL:
```bash
psql -d lugal_nbs -c "SELECT * FROM nbs_audit_log ORDER BY create_date DESC LIMIT 20;"

psql -d lugal_nbs -c "SELECT * FROM nbs_bulk_upload_job ORDER BY create_date DESC;"

psql -d lugal_nbs -c "SELECT id, name, is_deleted, deleted_at FROM nbs_document WHERE is_deleted = true;"
```

---

## 🐛 استكشاف الأخطاء

### لا يمكن الاتصال بـ API:
```bash
# تحقق من أن Odoo يعمل
ps aux | grep odoo-bin

# تحقق من المنفذ
netstat -tlnp | grep 8070

# اقرأ آخر 50 سطر من الـ log
tail -50 /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/odoo_local.log
```

### أخطاء JWT:
```bash
# تأكد من أن JWT token صالح
# يجب أن يحتوي على: user_id في payload
# يجب أن يكون غير منتهي الصلاحية
```

### أخطاء الصلاحيات:
```bash
# تحقق من مجموعة المستخدم:
psql -d lugal_nbs -c "SELECT u.login, g.name FROM res_users u 
    JOIN res_groups_users_rel r ON u.id = r.uid 
    JOIN res_groups g ON r.gid = g.id 
    WHERE u.login = 'your_username';"
```

---

## 📊 Monitoring

### Real-time Log Monitoring:
```bash
# مراقبة الـ log مباشرة
tail -f /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/odoo_local.log | grep -E "(ERROR|nbs_archive|bulk_upload)"
```

### Database Stats:
```bash
# عدد المستندات في سلة المحذوفات
psql -d lugal_nbs -c "SELECT COUNT(*) FROM nbs_document WHERE is_deleted = true;"

# عدد عمليات الرفع الجماعي
psql -d lugal_nbs -c "SELECT status, COUNT(*) FROM nbs_bulk_upload_job GROUP BY status;"

# أحدث 10 عمليات audit
psql -d lugal_nbs -c "SELECT action, metadata, create_date FROM nbs_audit_log ORDER BY create_date DESC LIMIT 10;"
```

---

## ✅ Checklist للاختبار

### Attachments:
- [ ] رفع مرفق واحد
- [ ] رفع عدة مرفقات دفعة واحدة
- [ ] تعديل اسم مرفق
- [ ] تعديل ملف موجود
- [ ] حذف مرفق (soft delete)
- [ ] استعادة مرفق من سلة المحذوفات
- [ ] حذف مرفق نهائياً (كـ admin)

### Documents:
- [ ] نقل مستند إلى سلة المحذوفات
- [ ] عرض سلة المحذوفات
- [ ] استعادة مستند
- [ ] حذف مستند نهائياً (كـ admin)
- [ ] التحقق من restore_deadline

### Bulk Upload:
- [ ] بدء عملية رفع جماعي
- [ ] رفع 10 ملفات
- [ ] تتبع التقدم أثناء الرفع
- [ ] معالجة ملف فاشل (اختبار partial success)
- [ ] إلغاء عملية رفع
- [ ] عرض قائمة عمليات الرفع

### Audit & Security:
- [ ] التحقق من تسجيل جميع العمليات في audit log
- [ ] اختبار الصلاحيات (user عادي لا يستطيع الحذف النهائي)
- [ ] اختبار JWT authentication

---

## 🎯 Expected Results

### ✅ نجاح العملية:
```json
{
    "success": true,
    "message": "تم بنجاح...",
    "data": { ... }
}
```

### ❌ فشل العملية:
```json
{
    "success": false,
    "error": "رسالة الخطأ هنا"
}
```

---

## 📞 الدعم

إذا واجهت أي مشاكل:
1. تحقق من الـ log: `odoo_local.log`
2. راجع التوثيق الكامل: `NBS_ARCHIVE_WEEK1_IMPLEMENTATION_COMPLETE.md`
3. تحقق من الـ database: `lugal_nbs`

---

## 🚀 الخطوة التالية

بعد إكمال الاختبار، يمكنك:
1. البدء في تطوير الـ frontend
2. الانتقال إلى Week 2 features (حسب خطة التطوير)
3. تكامل النظام مع أنظمة خارجية

**Happy Testing! 🎉**
