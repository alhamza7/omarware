# ============================================
# PowerShell Script to Clear Products and Orders
# ============================================

# Database connection parameters
$dbHost = "localhost"
$dbPort = "5432"
$dbName = "lugal"
$dbUser = "odoo_user"
$dbPassword = "root"

# SQL commands to execute
$sqlCommands = @"
-- Stop Odoo first (important!)
-- أوقف Odoo أولاً (مهم!)

BEGIN;

-- Delete Sale Order Lines
DELETE FROM sale_order_line;
SELECT setval('sale_order_line_id_seq', 1, false);

-- Delete Sale Orders
DELETE FROM sale_order;
SELECT setval('sale_order_id_seq', 1, false);

-- Delete POS Perfume Order Lines
DELETE FROM pos_perfume_order_line;
SELECT setval('pos_perfume_order_line_id_seq', 1, false);

-- Delete POS Perfume Orders
DELETE FROM pos_perfume_order;
SELECT setval('pos_perfume_order_id_seq', 1, false);

-- Delete Invoice Lines
DELETE FROM account_move_line WHERE move_id IN (SELECT id FROM account_move WHERE move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'));
SELECT setval('account_move_line_id_seq', 1, false);

-- Delete Invoices
DELETE FROM account_move WHERE move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund');
SELECT setval('account_move_id_seq', 1, false);

-- Delete Product Variants
DELETE FROM product_product;
SELECT setval('product_product_id_seq', 1, false);

-- Delete Product Templates
DELETE FROM product_template;
SELECT setval('product_template_id_seq', 1, false);

-- Delete Stock Moves
DELETE FROM stock_move;
SELECT setval('stock_move_id_seq', 1, false);

-- Delete Stock Quant
DELETE FROM stock_quant;
SELECT setval('stock_quant_id_seq', 1, false);

-- Delete Stock Picking
DELETE FROM stock_picking;
SELECT setval('stock_picking_id_seq', 1, false);

COMMIT;
"@

Write-Host "============================================" -ForegroundColor Yellow
Write-Host "Clear Products and Orders Script" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  WARNING: This will DELETE ALL products and orders!" -ForegroundColor Red
Write-Host "⚠️  Make sure to backup your database first!" -ForegroundColor Red
Write-Host ""
$confirmation = Read-Host "Are you sure you want to continue? (yes/no)"

if ($confirmation -eq "yes") {
    Write-Host ""
    Write-Host "Connecting to database..." -ForegroundColor Cyan
    
    # Set PGPASSWORD environment variable
    $env:PGPASSWORD = $dbPassword
    
    # Execute SQL commands
    $sqlCommands | & "C:\Program Files\PostgreSQL\*\bin\psql.exe" -h $dbHost -p $dbPort -U $dbUser -d $dbName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Database cleared successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Error clearing database!" -ForegroundColor Red
        Write-Host "Make sure PostgreSQL is installed and psql is in PATH" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Operation cancelled." -ForegroundColor Yellow
}

