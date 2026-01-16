# NBS Archive Restore Script
# Restores database and files from backup

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupPath,
    [string]$DBName = "lugal",
    [string]$DBUser = "odoo_user",
    [string]$DBPassword = "root",
    [string]$DBHost = "localhost",
    [int]$DBPort = 5432
)

Write-Host "=== NBS Archive Restore Script ===" -ForegroundColor Cyan
Write-Host ""

# Verify backup exists
if (-not (Test-Path $BackupPath)) {
    Write-Host "❌ Backup path does not exist: $BackupPath" -ForegroundColor Red
    exit 1
}

# Check manifest
$manifestPath = Join-Path $BackupPath "manifest.json"
if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath | ConvertFrom-Json
    Write-Host "Backup info:" -ForegroundColor Yellow
    Write-Host "  Date: $($manifest.backup_date)"
    Write-Host "  Database: $($manifest.database)"
    Write-Host ""
}

# Confirm
$confirm = Read-Host "⚠️ This will REPLACE the current database. Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Restore cancelled." -ForegroundColor Yellow
    exit 0
}

$env:PGPASSWORD = $DBPassword

# 1. Drop and recreate database
Write-Host "🗑️ Dropping existing database..." -ForegroundColor Yellow
try {
    & "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
        -h $DBHost `
        -p $DBPort `
        -U postgres `
        -c "DROP DATABASE IF EXISTS $DBName;"
    
    Write-Host "  ✅ Database dropped" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ Could not drop database: $_" -ForegroundColor Yellow
}

Write-Host "➕ Creating new database..." -ForegroundColor Yellow
try {
    & "C:\Program Files\PostgreSQL\18\bin\psql.exe" `
        -h $DBHost `
        -p $DBPort `
        -U postgres `
        -c "CREATE DATABASE $DBName WITH OWNER = $DBUser ENCODING = 'UTF8';"
    
    Write-Host "  ✅ Database created" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Failed to create database: $_" -ForegroundColor Red
    exit 1
}

# 2. Restore database
Write-Host "📥 Restoring database..." -ForegroundColor Yellow
$dbBackupFile = Join-Path $BackupPath "database.sql"

if (Test-Path $dbBackupFile) {
    try {
        & "C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" `
            -h $DBHost `
            -p $DBPort `
            -U $DBUser `
            -d $DBName `
            -F c `
            $dbBackupFile
        
        Write-Host "  ✅ Database restored" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Database restore failed: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ❌ Database backup file not found!" -ForegroundColor Red
    exit 1
}

# 3. Restore filestore
$filestoreBackup = Join-Path $BackupPath "filestore"
$filestorePath = "C:\Users\$env:USERNAME\AppData\Local\OpenERP S.A.\Odoo\filestore\$DBName"

if (Test-Path $filestoreBackup) {
    Write-Host "📁 Restoring filestore..." -ForegroundColor Yellow
    
    try {
        # Remove existing filestore
        if (Test-Path $filestorePath) {
            Remove-Item $filestorePath -Recurse -Force
        }
        
        # Copy backup
        Copy-Item -Path $filestoreBackup -Destination $filestorePath -Recurse -Force
        Write-Host "  ✅ Filestore restored" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Filestore restore failed: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ℹ️ No filestore in backup" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Restore completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️ Please restart Odoo server to load the restored database" -ForegroundColor Yellow





















