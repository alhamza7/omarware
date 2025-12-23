# ============================================
# تحديث مودل SAP Integration
# Update SAP Integration Module
# ============================================

Write-Host "================================" -ForegroundColor Cyan
Write-Host "تحديث مودل SAP Integration" -ForegroundColor Cyan
Write-Host "SAP Integration Module Update" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# المسار إلى مجلد المشروع
$PROJECT_PATH = "D:\capo_dev\Lugal-ai"
$PYTHON_PATH = "$PROJECT_PATH\venv\Scripts\python.exe"
$ODOO_BIN = "$PROJECT_PATH\odoo-bin"
$CONFIG_FILE = "$PROJECT_PATH\odoo_simple.conf"
$DATABASE = "lugal"

# التحقق من وجود الملفات
Write-Host "التحقق من الملفات..." -ForegroundColor Yellow
if (-not (Test-Path $PYTHON_PATH)) {
    Write-Host "❌ خطأ: Python غير موجود في: $PYTHON_PATH" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $ODOO_BIN)) {
    Write-Host "❌ خطأ: odoo-bin غير موجود في: $ODOO_BIN" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $CONFIG_FILE)) {
    Write-Host "❌ خطأ: ملف الإعدادات غير موجود في: $CONFIG_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "✅ جميع الملفات موجودة" -ForegroundColor Green
Write-Host ""

# الانتقال إلى مجلد المشروع
Write-Host "الانتقال إلى مجلد المشروع..." -ForegroundColor Yellow
Set-Location $PROJECT_PATH

# تحديث المودل
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "بدء التحديث..." -ForegroundColor Yellow
Write-Host "Updating module..." -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ قد يستغرق هذا بضع دقائق..." -ForegroundColor Yellow
Write-Host ""

# تنفيذ التحديث
& $PYTHON_PATH $ODOO_BIN -c $CONFIG_FILE -d $DATABASE -u sap_integration --stop-after-init

# التحقق من نجاح التحديث
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Green
    Write-Host "✅ تم التحديث بنجاح!" -ForegroundColor Green
    Write-Host "✅ Update completed successfully!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "الخطوات التالية:" -ForegroundColor Cyan
    Write-Host "1. شغّل Odoo: .\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal" -ForegroundColor White
    Write-Host "2. افتح المتصفح: http://localhost:8070" -ForegroundColor White
    Write-Host "3. اذهب إلى: SAP Integration → Management Tools → حذف التكرارات" -ForegroundColor White
    Write-Host ""
    
    # سؤال المستخدم إذا كان يريد تشغيل Odoo
    $response = Read-Host "هل تريد تشغيل Odoo الآن؟ (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host ""
        Write-Host "🚀 تشغيل Odoo..." -ForegroundColor Green
        Write-Host "اضغط Ctrl+C لإيقاف Odoo" -ForegroundColor Yellow
        Write-Host ""
        & $PYTHON_PATH $ODOO_BIN -c $CONFIG_FILE -d $DATABASE
    } else {
        Write-Host "يمكنك تشغيل Odoo يدوياً باستخدام:" -ForegroundColor Cyan
        Write-Host ".\venv\Scripts\python.exe odoo-bin -c odoo_simple.conf -d lugal" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Red
    Write-Host "❌ فشل التحديث!" -ForegroundColor Red
    Write-Host "❌ Update failed!" -ForegroundColor Red
    Write-Host "================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "راجع الأخطاء أعلاه للمزيد من التفاصيل" -ForegroundColor Yellow
    Write-Host "Check the errors above for details" -ForegroundColor Yellow
    exit 1
}

