@echo off
setlocal

echo Stopping Roughness GA Optimizer API on port 30092...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$port = 30092; " ^
  "$procIds = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; " ^
  "if (-not $procIds) { Write-Host 'No listening process found on port' $port; exit 0 }; " ^
  "foreach ($procId in $procIds) { Write-Host 'Stopping PID' $procId; Stop-Process -Id $procId -Force }"
