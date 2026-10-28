# TAQA Water & Electricity Bill API Agent
# Supports both interactive console output and MCP-style JSON output.

param(
    [string]$ApiUrl = "https://api.taqa.ae/gateway/ADDC_TAMM_WaterElectricityBill/1.0/MyBusinessGetWaterElectricityBillList",
    [string]$TradeLicense = "CN-1094694",
    [string]$ShowAllAccounts = "true",
    [string]$ShowTotalOutStanding = "true",
    [string]$ShowGrandTotalOutStanding = "true",
    [string]$AccountID = "",
    [string]$PremiseID = "",
    [string]$IdentityType = "TID",
    [string[]]$EmiratesIDNumbers = @(),
    [string]$Username = "usrDED.prod",
    [string]$Password = "Iwe@_987a",
    [switch]$McpMode
)

function Get-TaqaRequestPayload {
    return @{
        MyBusinessGetWaterElectricityBillListRequest = @{
            AccountID = $AccountID
            EmiratesIDNumbers = $EmiratesIDNumbers
            IdentityType = $IdentityType
            PremiseID = $PremiseID
            TradeLicenseNumbers = @($TradeLicense)
            ShowAllAccounts = $ShowAllAccounts
            ShowTotalOutStanding = $ShowTotalOutStanding
            ShowGrandTotalOutStanding = $ShowGrandTotalOutStanding
        }
        UserAuthentication = @{
            Username = $Username
            Password = $Password
        }
    }
}

function Invoke-TaqaBillsApi {
    param(
        [hashtable]$Payload
    )

    $requestBody = $Payload | ConvertTo-Json -Depth 12

    return Invoke-RestMethod -Uri $ApiUrl `
        -Method Post `
        -ContentType "application/json" `
        -Body $requestBody `
        -ErrorAction Stop
}

function Write-InteractiveSummary {
    param(
        [object]$Response
    )

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "TAQA Water & Electricity Bill API Agent" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Executing API call to TAQA endpoint..." -ForegroundColor Yellow
    Write-Host "Trade License: $TradeLicense" -ForegroundColor Gray
    Write-Host ""
    Write-Host "=== SUMMARY ===" -ForegroundColor Green
    Write-Host ""

    if ($Response.GrandTotalOutStanding -ne $null -and $Response.GrandTotalOutStanding -ne "") {
        Write-Host "Grand Total Outstanding: AED $($Response.GrandTotalOutStanding)" -ForegroundColor Magenta
    }

    if ($Response.TradeLicenseBalances) {
        Write-Host ""
        Write-Host "Trade License Balances:" -ForegroundColor Green
        foreach ($balance in $Response.TradeLicenseBalances) {
            Write-Host "  License: $($balance.TradeLicenseNumber)" -ForegroundColor White
            Write-Host "  Outstanding: AED $($balance.TotalOutStanding)" -ForegroundColor Yellow
        }
    }

    $billList = @()
    if ($Response.WaterElectricityBillList) {
        $billList = @($Response.WaterElectricityBillList)
    }

    Write-Host ""
    Write-Host "=== WATER & ELECTRICITY BILLS ===" -ForegroundColor Green
    Write-Host "Total Accounts Found: $($billList.Count)" -ForegroundColor Cyan
    Write-Host ""

    $activeCount = 0
    $inactiveCount = 0
    $totalBalance = [decimal]0

    foreach ($bill in $billList) {
        $status = "$($bill.AccountStatus)"
        if ($status.ToLowerInvariant() -eq "active") {
            $activeCount++
            $statusColor = "Green"
        } else {
            $inactiveCount++
            $statusColor = "Red"
        }

        Write-Host "-------------------------------------" -ForegroundColor Gray
        Write-Host "Account ID: $($bill.AccountID)" -ForegroundColor White
        Write-Host "Status: $status" -ForegroundColor $statusColor
        Write-Host "Premise Address: $($bill.PremiseAddress)" -ForegroundColor White
        Write-Host "Zone/District: $($bill.ZoneDistrictCode)" -ForegroundColor Gray

        if ($bill.CurrentBalance -ne $null -and $bill.CurrentBalance -ne "") {
            $currentBalance = [decimal]$bill.CurrentBalance
            $balanceColor = "Green"
            if ($currentBalance -gt 0) {
                $balanceColor = "Red"
            }
            Write-Host "Current Balance: AED $($bill.CurrentBalance)" -ForegroundColor $balanceColor
            $totalBalance += $currentBalance
        }

        Write-Host "Bill Due Date: $($bill.BillDueDate)" -ForegroundColor Gray
        Write-Host "Bill ID: $($bill.BillID)" -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "=== ACCOUNT STATISTICS ===" -ForegroundColor Green
    Write-Host "Active Accounts: $activeCount" -ForegroundColor Green
    Write-Host "Inactive Accounts: $inactiveCount" -ForegroundColor Red
    Write-Host "Total Current Balance (All Accounts): AED $totalBalance" -ForegroundColor Yellow

    if ($Response.Fault) {
        Write-Host ""
        Write-Host "WARNING: $($Response.Fault)" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "API Call Completed Successfully" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

$payload = Get-TaqaRequestPayload

try {
    $response = Invoke-TaqaBillsApi -Payload $payload

    if ($McpMode) {
        $result = [ordered]@{
            success = $true
            endpoint = $ApiUrl
            requestedAt = (Get-Date).ToString("o")
            request = @{
                MyBusinessGetWaterElectricityBillListRequest = $payload.MyBusinessGetWaterElectricityBillListRequest
            }
            response = $response
        }

        $result | ConvertTo-Json -Depth 20
        exit 0
    }

    Write-InteractiveSummary -Response $response
    return $response
} catch {
    $statusCode = $null
    $statusDescription = $null
    $responseBody = $null

    if ($_.Exception.Response) {
        try {
            $statusCode = [int]$_.Exception.Response.StatusCode
            $statusDescription = "$($_.Exception.Response.StatusDescription)"
        } catch {
            $statusDescription = "$($_.Exception.Message)"
        }

        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
        } catch {
            $responseBody = $null
        }
    }

    if ($McpMode) {
        $errorResult = [ordered]@{
            success = $false
            endpoint = $ApiUrl
            requestedAt = (Get-Date).ToString("o")
            error = @{
                message = "$($_.Exception.Message)"
                statusCode = $statusCode
                statusDescription = $statusDescription
                responseBody = $responseBody
            }
        }

        $errorResult | ConvertTo-Json -Depth 10
        exit 1
    }

    Write-Host ""
    Write-Host "ERROR: API Call Failed" -ForegroundColor Red
    Write-Host "Error Details: $($_.Exception.Message)" -ForegroundColor Red
    if ($statusCode -ne $null) {
        Write-Host "Response Status Code: $statusCode" -ForegroundColor Red
    }
    if ($statusDescription) {
        Write-Host "Status Description: $statusDescription" -ForegroundColor Red
    }
    if ($responseBody) {
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
    Write-Host ""

    return $null
}
