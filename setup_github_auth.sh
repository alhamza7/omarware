#!/bin/bash
# -*- coding: utf-8 -*-
# سكريبت لإعداد المصادقة مع GitHub والحصول على Token

echo "=========================================="
echo "إعداد المصادقة مع GitHub"
echo "=========================================="
echo ""

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# معلومات المستخدم
GITHUB_USERNAME="alhamza7"
GITHUB_PASSWORD="Promohammed99"
REPO_URL="https://github.com/alhamza7/Lugal-ai.git"

# التحقق من وجود GitHub CLI
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✅ تم العثور على GitHub CLI${NC}"
    echo ""
    
    # التحقق من حالة تسجيل الدخول
    if gh auth status &> /dev/null; then
        echo -e "${GREEN}✅ أنت مسجل الدخول بالفعل إلى GitHub${NC}"
        echo ""
        gh auth status
        echo ""
        
        # الحصول على Token
        echo "الحصول على Token..."
        TOKEN=$(gh auth token 2>/dev/null)
        if [ -n "$TOKEN" ]; then
            echo -e "${GREEN}✅ تم الحصول على Token بنجاح${NC}"
            setup_git_with_token "$TOKEN"
        else
            echo -e "${YELLOW}⚠️  لم يتم الحصول على Token، جرب تسجيل الدخول مرة أخرى${NC}"
            gh auth login
            TOKEN=$(gh auth token 2>/dev/null)
            if [ -n "$TOKEN" ]; then
                setup_git_with_token "$TOKEN"
            fi
        fi
    else
        echo "تسجيل الدخول إلى GitHub..."
        echo ""
        echo "سيتم فتح المتصفح لتسجيل الدخول..."
        echo "أو يمكنك استخدام:"
        echo "  - GitHub.com (افتراضي)"
        echo "  - GitHub Enterprise Server"
        echo ""
        
        # محاولة تسجيل الدخول
        if gh auth login --web 2>/dev/null; then
            echo -e "${GREEN}✅ تم تسجيل الدخول بنجاح${NC}"
            TOKEN=$(gh auth token 2>/dev/null)
            if [ -n "$TOKEN" ]; then
                setup_git_with_token "$TOKEN"
            fi
        else
            echo -e "${RED}❌ فشل تسجيل الدخول${NC}"
            echo ""
            manual_token_setup
        fi
    fi
else
    echo -e "${YELLOW}⚠️  GitHub CLI غير مثبت${NC}"
    echo ""
    echo "الخيارات المتاحة:"
    echo "1. تثبيت GitHub CLI (موصى به)"
    echo "2. إدخال Token يدوياً"
    echo ""
    read -p "اختر الخيار (1 أو 2): " choice
    
    case $choice in
        1)
            install_github_cli
            ;;
        2)
            manual_token_setup
            ;;
        *)
            echo -e "${RED}❌ خيار غير صحيح${NC}"
            manual_token_setup
            ;;
    esac
fi

function install_github_cli() {
    echo ""
    echo "تثبيت GitHub CLI..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            echo "تثبيت باستخدام apt..."
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh -y
        elif command -v yum &> /dev/null; then
            echo "تثبيت باستخدام yum..."
            sudo dnf install 'dnf-command(config-manager)' -y
            sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
            sudo dnf install gh -y
        else
            echo -e "${RED}❌ نظام غير مدعوم للتثبيت التلقائي${NC}"
            echo "يرجى تثبيت GitHub CLI يدوياً من: https://cli.github.com/"
            manual_token_setup
            return
        fi
        
        if command -v gh &> /dev/null; then
            echo -e "${GREEN}✅ تم تثبيت GitHub CLI بنجاح${NC}"
            echo ""
            echo "تسجيل الدخول..."
            gh auth login --web
            TOKEN=$(gh auth token 2>/dev/null)
            if [ -n "$TOKEN" ]; then
                setup_git_with_token "$TOKEN"
            fi
        else
            echo -e "${RED}❌ فشل التثبيت${NC}"
            manual_token_setup
        fi
    else
        echo -e "${RED}❌ نظام غير مدعوم${NC}"
        echo "يرجى تثبيت GitHub CLI يدوياً من: https://cli.github.com/"
        manual_token_setup
    fi
}

function manual_token_setup() {
    echo ""
    echo "=========================================="
    echo "إعداد Token يدوياً"
    echo "=========================================="
    echo ""
    echo "اتبع الخطوات التالية:"
    echo ""
    echo "1. افتح المتصفح واذهب إلى:"
    echo -e "   ${GREEN}https://github.com/settings/tokens${NC}"
    echo ""
    echo "2. انقر على: ${YELLOW}Generate new token${NC} → ${YELLOW}Generate new token (classic)${NC}"
    echo ""
    echo "3. أدخل اسم للـ Token (مثل: Lugal-ai-push)"
    echo ""
    echo "4. اختر الصلاحيات:"
    echo "   ✅ ${GREEN}repo${NC} (Full control of private repositories)"
    echo ""
    echo "5. انقر ${YELLOW}Generate token${NC}"
    echo ""
    echo "6. ${RED}انسخ الـ Token فوراً${NC} (لن تتمكن من رؤيته مرة أخرى!)"
    echo ""
    read -p "الصق الـ Token هنا: " TOKEN
    
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}❌ لم يتم إدخال Token${NC}"
        exit 1
    fi
    
    # التحقق من صحة الـ Token
    echo ""
    echo "التحقق من صحة الـ Token..."
    response=$(curl -s -H "Authorization: token $TOKEN" https://api.github.com/user)
    
    if echo "$response" | grep -q '"login"'; then
        echo -e "${GREEN}✅ Token صحيح${NC}"
        setup_git_with_token "$TOKEN"
    else
        echo -e "${RED}❌ Token غير صحيح${NC}"
        echo "يرجى التحقق من الـ Token والمحاولة مرة أخرى"
        exit 1
    fi
}

function setup_git_with_token() {
    local TOKEN=$1
    
    echo ""
    echo "=========================================="
    echo "إعداد Git مع Token"
    echo "=========================================="
    echo ""
    
    # حفظ الـ Token بشكل آمن
    echo "حفظ الـ Token..."
    
    # إنشاء مجلد .git-credentials إذا لم يكن موجوداً
    mkdir -p ~/.config/git
    
    # حفظ الـ Token
    echo "https://${GITHUB_USERNAME}:${TOKEN}@github.com" > ~/.git-credentials
    chmod 600 ~/.git-credentials
    
    # إعداد Git credential helper
    git config --global credential.helper store
    
    # إعداد remote URL
    cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai 2>/dev/null || cd "$(dirname "$0")"
    git remote set-url origin "https://${GITHUB_USERNAME}:${TOKEN}@github.com/alhamza7/Lugal-ai.git"
    
    echo -e "${GREEN}✅ تم إعداد Git بنجاح${NC}"
    echo ""
    
    # اختبار الاتصال
    echo "اختبار الاتصال مع GitHub..."
    if git ls-remote origin &> /dev/null; then
        echo -e "${GREEN}✅ الاتصال ناجح${NC}"
        echo ""
        echo "=========================================="
        echo -e "${GREEN}✅ تم إعداد المصادقة بنجاح!${NC}"
        echo "=========================================="
        echo ""
        echo "يمكنك الآن رفع التغييرات باستخدام:"
        echo -e "${GREEN}git push origin main${NC}"
        echo ""
        
        # محاولة الـ push تلقائياً
        read -p "هل تريد رفع التغييرات الآن؟ (y/n): " push_now
        if [[ "$push_now" == "y" || "$push_now" == "Y" ]]; then
            echo ""
            echo "رفع التغييرات..."
            git push origin main
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ تم رفع التغييرات بنجاح!${NC}"
            else
                echo -e "${RED}❌ فشل رفع التغييرات${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ فشل الاتصال${NC}"
        echo "يرجى التحقق من الـ Token"
    fi
}

# تشغيل السكريبت
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    # السكريبت يعمل مباشرة
    true
fi
