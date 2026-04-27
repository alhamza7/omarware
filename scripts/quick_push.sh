#!/bin/bash
# سكريبت سريع للـ push مع Token

echo "=========================================="
echo "رفع التغييرات إلى GitHub"
echo "=========================================="
echo ""

# التحقق من وجود commits للرفع
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai

if ! git log origin/main..HEAD --oneline &> /dev/null; then
    echo "⚠️  لا توجد تغييرات للرفع"
    exit 0
fi

echo "الـ Commits الجاهزة للرفع:"
git log origin/main..HEAD --oneline
echo ""

# طلب Token
echo "=========================================="
echo "إدخال Personal Access Token"
echo "=========================================="
echo ""
echo "إذا لم يكن لديك Token:"
echo "1. افتح: https://github.com/settings/tokens"
echo "2. Generate new token (classic)"
echo "3. اختر صلاحية: repo"
echo "4. انسخ الـ Token"
echo ""

read -sp "الصق الـ Token هنا: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ لم يتم إدخال Token"
    exit 1
fi

# التحقق من صحة Token
echo ""
echo "التحقق من صحة الـ Token..."
response=$(curl -s -H "Authorization: token $TOKEN" https://api.github.com/user)

if ! echo "$response" | grep -q '"login"'; then
    echo "❌ Token غير صحيح"
    exit 1
fi

echo "✅ Token صحيح"
echo ""

# إعداد Git مع Token
echo "إعداد Git..."
git remote set-url origin "https://alhamza7:${TOKEN}@github.com/alhamza7/Lugal-ai.git"

# عمل Push
echo ""
echo "رفع التغييرات..."
if git push origin main; then
    echo ""
    echo "=========================================="
    echo "✅ تم رفع التغييرات بنجاح!"
    echo "=========================================="
    
    # تنظيف Token من URL (لأسباب أمنية)
    git remote set-url origin "https://github.com/alhamza7/Lugal-ai.git"
else
    echo ""
    echo "❌ فشل رفع التغييرات"
    exit 1
fi
