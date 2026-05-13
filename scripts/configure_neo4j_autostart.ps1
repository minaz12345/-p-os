# Configure Neo4j Auto-Start via Windows Scheduled Task
# This ensures Neo4j starts automatically on system boot without manual intervention.

$neo4jPath = "C:\Users\Pawel\.Neo4jDesktop2\Data\dbmss\dbms-55d14bc3-ef1c-4bac-a35a-297fb7f2b7f0"
$taskName = "P-OS Neo4j Auto-Start"

Write-Host "Configuring Neo4j Auto-Start..." -ForegroundColor Cyan

# Check if task already exists
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Write-Host "Task already exists. Updating..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Register new task to run at startup with highest privileges
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command `"& '$neo4jPath\bin\neo4j.bat' start`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Description "Automatically starts Neo4j instance for P-OS v7.5" | Out-Null

Write-Host "✅ Neo4j Auto-Start configured successfully." -ForegroundColor Green
Write-Host "   Task: $taskName"
Write-Host "   Target: $neo4jPath"
Write-Host "   Status: Will activate on next system reboot."
