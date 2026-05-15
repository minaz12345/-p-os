while ($true) {
    # Check if gateway is already running on port 8443
    $existing = Get-NetTCPConnection -LocalPort 8443 -ErrorAction SilentlyContinue
    
    if ($existing) {
        # Gateway already running, wait and check again
        Start-Sleep -Seconds 10
        continue
    }
    
    try {
        Set-Location D:\pos7
        python -m uvicorn gateway_mvp:app `
            --host 0.0.0.0 `
            --port 8443 `
            --ssl-keyfile D:\pos7\certs\key.pem `
            --ssl-certfile D:\pos7\certs\cert.pem
    } catch {
        Add-Content D:\pos7\gateway_restart.log "$(Get-Date) Gateway crashed: $_"
    }
    Start-Sleep -Seconds 5
}
