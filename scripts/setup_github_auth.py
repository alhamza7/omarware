#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت Python لإعداد المصادقة مع GitHub والحصول على Token
"""

import os
import sys
import subprocess
import json
import urllib.request
import urllib.error
import getpass
import base64

GITHUB_USERNAME = "alhamza7"
GITHUB_PASSWORD = "Promohammed99"
REPO_URL = "https://github.com/alhamza7/Lugal-ai.git"

def print_success(msg):
    print(f"\033[0;32m✅ {msg}\033[0m")

def print_error(msg):
    print(f"\033[0;31m❌ {msg}\033[0m")

def print_warning(msg):
    print(f"\033[1;33m⚠️  {msg}\033[0m")

def print_info(msg):
    print(f"\033[0;36mℹ️  {msg}\033[0m")

def check_github_cli():
    """التحقق من وجود GitHub CLI"""
    try:
        result = subprocess.run(['gh', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def login_with_github_cli():
    """تسجيل الدخول باستخدام GitHub CLI"""
    print("\n" + "="*50)
    print("تسجيل الدخول باستخدام GitHub CLI")
    print("="*50 + "\n")
    
    # التحقق من حالة تسجيل الدخول
    try:
        result = subprocess.run(['gh', 'auth', 'status'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        if result.returncode == 0:
            print_success("أنت مسجل الدخول بالفعل إلى GitHub")
            print(result.stdout)
            
            # الحصول على Token
            token_result = subprocess.run(['gh', 'auth', 'token'], 
                                        capture_output=True, 
                                        text=True, 
                                        timeout=5)
            if token_result.returncode == 0:
                token = token_result.stdout.strip()
                if token:
                    print_success("تم الحصول على Token بنجاح")
                    return token
        else:
            print_info("تسجيل الدخول...")
            print("سيتم فتح المتصفح لتسجيل الدخول...")
            
            # تسجيل الدخول
            login_result = subprocess.run(['gh', 'auth', 'login', '--web'], 
                                        timeout=120)
            if login_result.returncode == 0:
                print_success("تم تسجيل الدخول بنجاح")
                
                # الحصول على Token
                token_result = subprocess.run(['gh', 'auth', 'token'], 
                                            capture_output=True, 
                                            text=True, 
                                            timeout=5)
                if token_result.returncode == 0:
                    token = token_result.stdout.strip()
                    if token:
                        return token
    except subprocess.TimeoutExpired:
        print_error("انتهت مهلة الاتصال")
    except Exception as e:
        print_error(f"خطأ: {e}")
    
    return None

def install_github_cli():
    """تثبيت GitHub CLI"""
    print("\n" + "="*50)
    print("تثبيت GitHub CLI")
    print("="*50 + "\n")
    
    try:
        # التحقق من النظام
        if os.path.exists('/etc/debian_version'):
            print_info("تثبيت على Debian/Ubuntu...")
            commands = [
                'curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg',
                'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null',
                'sudo apt update',
                'sudo apt install gh -y'
            ]
            
            for cmd in commands:
                print(f"تنفيذ: {cmd}")
                result = subprocess.run(cmd, shell=True, check=True)
            
            if check_github_cli():
                print_success("تم تثبيت GitHub CLI بنجاح")
                return True
            else:
                print_error("فشل التثبيت")
                return False
        else:
            print_warning("نظام غير مدعوم للتثبيت التلقائي")
            print("يرجى تثبيت GitHub CLI يدوياً من: https://cli.github.com/")
            return False
    except subprocess.CalledProcessError as e:
        print_error(f"فشل التثبيت: {e}")
        return False
    except Exception as e:
        print_error(f"خطأ: {e}")
        return False

def verify_token(token):
    """التحقق من صحة Token"""
    try:
        req = urllib.request.Request('https://api.github.com/user')
        req.add_header('Authorization', f'token {token}')
        req.add_header('User-Agent', 'Lugal-ai-Setup')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if 'login' in data:
                print_success(f"Token صحيح - المستخدم: {data['login']}")
                return True
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print_error("Token غير صحيح أو منتهي الصلاحية")
        else:
            print_error(f"خطأ في التحقق: {e.code}")
    except Exception as e:
        print_error(f"خطأ في الاتصال: {e}")
    
    return False

def manual_token_setup():
    """إعداد Token يدوياً"""
    print("\n" + "="*50)
    print("إعداد Token يدوياً")
    print("="*50 + "\n")
    
    print("اتبع الخطوات التالية:\n")
    print("1. افتح المتصفح واذهب إلى:")
    print("   \033[0;32mhttps://github.com/settings/tokens\033[0m\n")
    print("2. انقر على: Generate new token → Generate new token (classic)\n")
    print("3. أدخل اسم للـ Token (مثل: Lugal-ai-push)\n")
    print("4. اختر الصلاحيات:")
    print("   ✅ \033[0;32mrepo\033[0m (Full control of private repositories)\n")
    print("5. انقر Generate token\n")
    print("6. \033[0;31mانسخ الـ Token فوراً\033[0m (لن تتمكن من رؤيته مرة أخرى!)\n")
    
    token = getpass.getpass("الصق الـ Token هنا: ")
    
    if not token:
        print_error("لم يتم إدخال Token")
        return None
    
    # التحقق من صحة الـ Token
    print("\nالتحقق من صحة الـ Token...")
    if verify_token(token):
        return token
    else:
        return None

def setup_git_with_token(token):
    """إعداد Git مع Token"""
    print("\n" + "="*50)
    print("إعداد Git مع Token")
    print("="*50 + "\n")
    
    try:
        # حفظ الـ Token بشكل آمن
        print_info("حفظ الـ Token...")
        
        # إنشاء مجلد .git-credentials إذا لم يكن موجوداً
        creds_dir = os.path.expanduser('~/.config/git')
        os.makedirs(creds_dir, exist_ok=True)
        
        # حفظ الـ Token
        creds_file = os.path.expanduser('~/.git-credentials')
        with open(creds_file, 'w') as f:
            f.write(f"https://{GITHUB_USERNAME}:{token}@github.com\n")
        
        os.chmod(creds_file, 0o600)
        
        # إعداد Git credential helper
        subprocess.run(['git', 'config', '--global', 'credential.helper', 'store'], 
                      check=True)
        
        # إعداد remote URL
        repo_path = '/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai'
        if not os.path.exists(repo_path):
            repo_path = os.path.dirname(os.path.abspath(__file__))
        
        os.chdir(repo_path)
        subprocess.run(['git', 'remote', 'set-url', 'origin', 
                       f'https://{GITHUB_USERNAME}:{token}@github.com/alhamza7/Lugal-ai.git'], 
                      check=True)
        
        print_success("تم إعداد Git بنجاح")
        
        # اختبار الاتصال
        print("\nاختبار الاتصال مع GitHub...")
        result = subprocess.run(['git', 'ls-remote', 'origin'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        
        if result.returncode == 0:
            print_success("الاتصال ناجح")
            print("\n" + "="*50)
            print_success("تم إعداد المصادقة بنجاح!")
            print("="*50 + "\n")
            print("يمكنك الآن رفع التغييرات باستخدام:")
            print("\033[0;32mgit push origin main\033[0m\n")
            
            # محاولة الـ push تلقائياً
            push_now = input("هل تريد رفع التغييرات الآن؟ (y/n): ").strip().lower()
            if push_now == 'y':
                print("\nرفع التغييرات...")
                push_result = subprocess.run(['git', 'push', 'origin', 'main'], 
                                           timeout=60)
                if push_result.returncode == 0:
                    print_success("تم رفع التغييرات بنجاح!")
                else:
                    print_error("فشل رفع التغييرات")
            return True
        else:
            print_error("فشل الاتصال")
            print(result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print_error(f"خطأ في إعداد Git: {e}")
        return False
    except Exception as e:
        print_error(f"خطأ: {e}")
        return False

def main():
    print("="*50)
    print("إعداد المصادقة مع GitHub")
    print("="*50)
    
    # التحقق من وجود GitHub CLI
    if check_github_cli():
        print_success("تم العثور على GitHub CLI")
        token = login_with_github_cli()
        if token:
            setup_git_with_token(token)
            return
    else:
        print_warning("GitHub CLI غير مثبت")
        print("\nالخيارات المتاحة:")
        print("1. تثبيت GitHub CLI (موصى به)")
        print("2. إدخال Token يدوياً")
        
        choice = input("\nاختر الخيار (1 أو 2): ").strip()
        
        if choice == '1':
            if install_github_cli():
                token = login_with_github_cli()
                if token:
                    setup_git_with_token(token)
                    return
            # إذا فشل التثبيت، انتقل إلى الإعداد اليدوي
            print_warning("الانتقال إلى الإعداد اليدوي...")
        
        # الإعداد اليدوي
        token = manual_token_setup()
        if token:
            setup_git_with_token(token)
        else:
            print_error("فشل إعداد المصادقة")
            sys.exit(1)

if __name__ == '__main__':
    main()
