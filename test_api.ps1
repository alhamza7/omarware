Write-Host "=== Testing NBS Archive API ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: OPTIONS for CORS preflight
Write-Host "Test 1: OPTIONS /api/auth/login (CORS Preflight)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8070/api/auth/login" `
        -Method OPTIONS `
        -Headers @{"Origin"="http://localhost:5173"} `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Host "  ✅ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  ✅ CORS Header: $($response.Headers['Access-Control-Allow-Origin'])" -ForegroundColor Green
    Write-Host "  ✅ Allowed Methods: $($response.Headers['Access-Control-Allow-Methods'])" -ForegroundColor Green
} catch {
    Write-Host "  ❌ FAILED - Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: POST Login
Write-Host "Test 2: POST /api/auth/login (Login Request)" -ForegroundColor Yellow
try {
    $body = @{
        username = "admin"
        password = "admin"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:8070/api/auth/login" `
        -Method POST `
        -Headers @{
            "Origin"="http://localhost:5173"
            "Content-Type"="application/json"
        } `
        -Body $body `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Host "  ✅ Status: $($response.StatusCode)" -ForegroundColor Green
    
    $json = $response.Content | ConvertFrom-Json
    if ($json.success) {
        Write-Host "  ✅ Login Successful!" -ForegroundColor Green
        Write-Host "  ✅ User: $($json.user.name)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Login Failed: $($json.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ FAILED - Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan




















