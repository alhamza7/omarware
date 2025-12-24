# NBS Archive Backup Script
# Creates full backup of database and files

param(
    [string]$BackupDir = "D:\nbs_backups",
    [string]$DBName = "lugal",
    [string]$DBUser = "odoo_user",
    [string]$DBPassword = "root",
    [string]$DBHost = "localhost",
    [int]$DBPort = 5432
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupName = "nbs_archive_backup_$timestamp"
$backupPath = Join-Path $BackupDir $backupName

Write-Host "=== NBS Archive Backup Script ===" -ForegroundColor Cyan
Write-Host "Timestamp: $timestamp" -ForegroundColor Yellow
Write-Host ""

# Create backup directory
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "✅ Created backup directory: $BackupDir" -ForegroundColor Green
}

New-Item -ItemType Directory -Path $backupPath -Force | Out-Null

# 1. Backup PostgreSQL database
Write-Host "📦 Backing up database..." -ForegroundColor Yellow
$env:PGPASSWORD = $DBPassword
$dbBackupFile = Join-Path $backupPath "database.sql"

try {
    & "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" `
        -h $DBHost `
        -p $DBPort `
        -U $DBUser `
        -d $DBName `
        -F c `
        -f $dbBackupFile
    
    Write-Host "  ✅ Database backup completed: $dbBackupFile" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Database backup failed: $_" -ForegroundColor Red
    exit 1
}

# 2. Backup filestore (if exists)
$filestorePath = "C:\Users\$env:USERNAME\AppData\Local\OpenERP S.A.\Odoo\filestore\$DBName"
if (Test-Path $filestorePath) {
    Write-Host "📁 Backing up filestore..." -ForegroundColor Yellow
    $filestoreBackup = Join-Path $backupPath "filestore"
    
    try {
        Copy-Item -Path $filestorePath -Destination $filestoreBackup -Recurse -Force
        Write-Host "  ✅ Filestore backup completed" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️ Filestore backup failed: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ℹ️ No filestore found" -ForegroundColor Gray
}

# 3. Backup configuration
Write-Host "⚙️ Backing up configuration..." -ForegroundColor Yellow
Copy-Item "odoo_simple.conf" -Destination (Join-Path $backupPath "odoo_simple.conf") -Force
Write-Host "  ✅ Configuration backup completed" -ForegroundColor Green

# 4. Create backup manifest
$manifest = @{
    timestamp = $timestamp
    database = $DBName
    backup_date = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    version = "1.0"
} | ConvertTo-Json

$manifest | Out-File -FilePath (Join-Path $backupPath "manifest.json") -Encoding UTF8

Write-Host ""
Write-Host "✅ Backup completed successfully!" -ForegroundColor Green
Write-Host "Backup location: $backupPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "To restore, run: .\scripts\restore.ps1 -BackupPath '$backupPath'" -ForegroundColor Yellow









