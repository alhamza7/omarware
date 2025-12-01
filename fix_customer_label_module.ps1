# Fix Customer Label Module
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "إصلاح موديول Customer Label" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop Odoo if running
Write-Host "إيقاف Odoo..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*odoo*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Update module
Write-Host "تحديث الموديول..." -ForegroundColor Yellow
cd L:\Lugal-ai
venv\Scripts\python.exe odoo-bin -c odoo.conf -d lugal --http-port=8070 -u product_label_designer --stop-after-init

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ تم التحديث بنجاح!" -ForegroundColor Green
} else {
    Write-Host "❌ فشل التحديث!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "الآن يجب عليك:" -ForegroundColor Yellow
Write-Host "1. فتح Odoo في المتصفح" -ForegroundColor White
Write-Host "2. الذهاب إلى Apps" -ForegroundColor White
Write-Host "3. البحث عن Product Label Designer" -ForegroundColor White
Write-Host "4. الضغط على Uninstall ثم Install" -ForegroundColor White
Write-Host "5. إعادة تشغيل Odoo" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan



