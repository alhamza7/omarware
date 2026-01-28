# دليل رفع التغييرات إلى GitHub

## المشكلة
GitHub لم يعد يدعم كلمات المرور العادية للـ push. يجب استخدام **Personal Access Token**.

## الحل السريع

### الخطوة 1: إنشاء Personal Access Token

1. اذهب إلى: https://github.com/settings/tokens
2. انقر على: **"Generate new token"** → **"Generate new token (classic)"**
3. أدخل اسم للـ Token (مثل: `Lugal-ai-push`)
4. اختر الصلاحيات:
   - ✅ **repo** (Full control of private repositories)
5. انقر **"Generate token"**
6. **انسخ الـ Token فوراً** (لن تتمكن من رؤيته مرة أخرى!)

### الخطوة 2: استخدام الـ Token للـ Push

#### الطريقة 1: استخدام الـ Token مباشرة في الأمر

```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
git push https://alhamza7:YOUR_TOKEN_HERE@github.com/alhamza7/Lugal-ai.git main
```

استبدل `YOUR_TOKEN_HERE` بالـ Token الذي نسخته.

#### الطريقة 2: حفظ الـ Token في Git Credential Helper

```bash
# حفظ الـ Token
git config --global credential.helper store
echo "https://alhamza7:YOUR_TOKEN_HERE@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# ثم الـ push العادي
git push origin main
```

#### الطريقة 3: استخدام SSH (أكثر أماناً)

```bash
# 1. إنشاء SSH key (إذا لم يكن موجوداً)
ssh-keygen -t rsa -b 4096 -C "alhamza7@github.com"

# 2. عرض المفتاح العام
cat ~/.ssh/id_rsa.pub

# 3. نسخ المفتاح وإضافته إلى GitHub:
#    - اذهب إلى: https://github.com/settings/keys
#    - انقر "New SSH key"
#    - الصق المفتاح

# 4. تغيير remote إلى SSH
git remote set-url origin git@github.com:alhamza7/Lugal-ai.git

# 5. الـ push
git push origin main
```

## الحالة الحالية

✅ **تم إنشاء Commit بنجاح!**
- الملفات المضافة:
  - `fix_assets_loading_error.sh`
  - `fix_assets_error.py`
  - `FIX_ASSETS_LOADING_ERROR.md`
  - `clear_cache_from_db.py` (محدث)

⏳ **في انتظار الـ Push** - يحتاج إلى Personal Access Token

## ملاحظات أمنية

- **لا تشارك الـ Token مع أحد**
- **لا ترفع الـ Token إلى GitHub**
- **استخدم SSH إذا أمكن** (أكثر أماناً)
- يمكنك حذف الـ Token من: https://github.com/settings/tokens
