# Paciolus Overnight Agent — Windows Task Scheduler Registration
#
# Run this script once from PowerShell (Admin) to register the overnight agent:
#   powershell -ExecutionPolicy Bypass -File D:\Dev\Paciolus\setup_scheduler.ps1
#
# To test immediately:
#   Start-ScheduledTask -TaskName "Paciolus-Overnight-Agent"
#
# To view last run info:
#   Get-ScheduledTaskInfo -TaskName "Paciolus-Overnight-Agent"
#
# To remove:
#   Unregister-ScheduledTask -TaskName "Paciolus-Overnight-Agent" -Confirm:$false

$TaskName = "Paciolus-Overnight-Agent"
$PythonExe = "D:\Dev\Paciolus\backend\venv\Scripts\python.exe"
$ScriptPath = "D:\Dev\Paciolus\scripts\overnight\orchestrator.py"
$WorkingDir = "D:\Dev\Paciolus"

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host ('Removing existing task ' + $TaskName + '...')
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Trigger: daily at 2:00 AM
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# Action: run orchestrator.py with the venv Python
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument $ScriptPath `
    -WorkingDirectory $WorkingDir

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -WakeToRun `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -MultipleInstances IgnoreNew

# Register using current user (no password prompt — runs only when logged on)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Trigger $Trigger `
    -Action $Action `
    -Settings $Settings `
    -Principal $Principal `
    -Description 'Paciolus overnight agent system - runs 5 agents between 2-4 AM and produces a morning briefing report.'

Write-Host ''
Write-Host ('Task ' + $TaskName + ' registered successfully.') -ForegroundColor Green
Write-Host ('  Trigger:  Daily at 2:00 AM')
Write-Host ('  Action:   ' + $PythonExe + ' ' + $ScriptPath)
Write-Host ('  WorkDir:  ' + $WorkingDir)
Write-Host ''
Write-Host ('To test now:  Start-ScheduledTask -TaskName ' + $TaskName)
Write-Host ('To view logs: Get-Content ' + $WorkingDir + '\reports\nightly\.run_log_' + (Get-Date -Format 'yyyy-MM-dd') + '.txt')
