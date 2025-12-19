# Script to install Odoo as a new instance on Windows
# With PostgreSQL and password root

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installing Odoo as a new instance" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Database information
$DB_USER = "postgres"
$DB_PASSWORD = "root"
$DB_HOST = "localhost"
$DB_PORT = "5432"
$DB_NAME = "odoo_new"

Write-Host "Database information:" -ForegroundColor Yellow
Write-Host "   Host: $DB_HOST"
Write-Host "   Port: $DB_PORT"
Write-Host "   User: $DB_USER"
Write-Host "   Password: $DB_PASSWORD"
Write-Host "   Database: $DB_NAME"
Write-Host ""

# Check if PostgreSQL exists
Write-Host "1. Checking PostgreSQL installation..." -ForegroundColor Yellow
$psqlPath = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
if (-not (Test-Path $psqlPath)) {
    # Try to find it in common locations
    $possiblePaths = @(
        "C:\Program Files\PostgreSQL\*\bin\psql.exe",
        "C:\Program Files (x86)\PostgreSQL\*\bin\psql.exe"
    )
    $found = $false
    foreach ($path in $possiblePaths) {
        $matches = Get-ChildItem $path -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($matches) {
            $psqlPath = $matches.FullName
            $found = $true
            break
        }
    }
    if (-not $found) {
        Write-Host "   ERROR: PostgreSQL is not installed or not found" -ForegroundColor Red
        Write-Host "   Please install PostgreSQL first" -ForegroundColor Red
        Write-Host "   Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "   OK: PostgreSQL found at $psqlPath" -ForegroundColor Green
Write-Host ""

# Check PostgreSQL connection
Write-Host "2. Checking PostgreSQL connection..." -ForegroundColor Yellow
$env:PGPASSWORD = $DB_PASSWORD
$testConnection = & $psqlPath -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT version();" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR: Failed to connect to PostgreSQL" -ForegroundColor Red
    Write-Host "   Make sure:" -ForegroundColor Yellow
    Write-Host "   - PostgreSQL is running" -ForegroundColor Yellow
    Write-Host "   - The postgres user password is 'root'" -ForegroundColor Yellow
    Write-Host "   - PostgreSQL service is running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   You can change the password using:" -ForegroundColor Yellow
    Write-Host "   psql -U postgres -c `"ALTER USER postgres PASSWORD 'root';`"" -ForegroundColor Cyan
    exit 1
}
Write-Host "   OK: PostgreSQL connection successful" -ForegroundColor Green
Write-Host ""

# Check if database exists
Write-Host "3. Checking if database '$DB_NAME' exists..." -ForegroundColor Yellow
$dbExists = & $psqlPath -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>&1
if ($dbExists -eq "1") {
    Write-Host "   WARNING: Database '$DB_NAME' already exists" -ForegroundColor Yellow
    $response = Read-Host "   Do you want to delete it and create a new one? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "   Deleting old database..." -ForegroundColor Yellow
        & $psqlPath -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   OK: Old database deleted" -ForegroundColor Green
        } else {
            Write-Host "   ERROR: Failed to delete database" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "   Cancelled" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "   INFO: Database '$DB_NAME' does not exist" -ForegroundColor Cyan
}
Write-Host ""

# Create database
Write-Host "4. Creating database '$DB_NAME'..." -ForegroundColor Yellow
$createDbQuery = @"
CREATE DATABASE $DB_NAME
    WITH OWNER = $DB_USER
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_United States.1252'
    LC_CTYPE = 'English_United States.1252'
    TEMPLATE = template0;
"@

$createDbQuery | & $psqlPath -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "   OK: Database '$DB_NAME' created successfully" -ForegroundColor Green
} else {
    Write-Host "   ERROR: Failed to create database" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verify database
Write-Host "5. Verifying database..." -ForegroundColor Yellow
$testDb = & $psqlPath -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT version();" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   OK: Database '$DB_NAME' is working correctly" -ForegroundColor Green
} else {
    Write-Host "   ERROR: Failed to connect to database" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Update odoo.conf
Write-Host "6. Updating odoo.conf..." -ForegroundColor Yellow
if (Test-Path "odoo.conf") {
    $confContent = Get-Content "odoo.conf" -Raw
    $confContent = $confContent -replace "db_user = .*", "db_user = postgres"
    $confContent = $confContent -replace "db_password = .*", "db_password = root"
    $confContent = $confContent -replace "dbfilter = .*", "dbfilter = ^$DB_NAME`$"
    Set-Content "odoo.conf" -Value $confContent -NoNewline
    Write-Host "   OK: odoo.conf updated" -ForegroundColor Green
} else {
    Write-Host "   WARNING: odoo.conf file not found" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "OK: Database setup completed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Initialize the database:" -ForegroundColor White
Write-Host "   venv\Scripts\python.exe odoo-bin -c odoo.conf -d $DB_NAME --init=base --stop-after-init" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Run Odoo:" -ForegroundColor White
Write-Host "   venv\Scripts\python.exe odoo-bin -c odoo.conf -d $DB_NAME" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Access Odoo:" -ForegroundColor White
Write-Host "   Open browser at: http://localhost:8069" -ForegroundColor Cyan
Write-Host ""
