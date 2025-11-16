# حل مشكلة Git Conflict

## المشكلة:
لديك تغييرات محلية في `fix_server.sh` تمنع سحب التحديثات

## الحلول:

### الحل 1: حفظ التغييرات المحلية (Stash) - موصى به

```bash
# حفظ التغييرات المحلية
git stash

# سحب التحديثات
git pull origin main

# استعادة التغييرات المحلية (اختياري)
git stash pop
```

### الحل 2: تجاهل التغييرات المحلية (إذا لم تكن مهمة)

```bash
# تجاهل التغييرات المحلية
git checkout -- fix_server.sh

# سحب التحديثات
git pull origin main
```

### الحل 3: حفظ التغييرات في commit منفصل

```bash
# إضافة التغييرات
git add fix_server.sh

# عمل commit
git commit -m "Local changes to fix_server.sh"

# سحب التحديثات (قد تحتاج إلى merge)
git pull origin main
```

## التوصية:
استخدم **الحل 1** (stash) لأنه يحفظ تغييراتك ويسمح بسحب التحديثات.

