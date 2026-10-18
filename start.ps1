$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Create .venv and install requirements-lock.txt first; see README.md.'
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'frontend\node_modules'))) {
    throw 'Run npm.cmd ci --prefix frontend first.'
}
function Test-ProjectPort([int] $Port) {
    $connection = New-Object System.Net.Sockets.TcpClient
    try { $connection.Connect('127.0.0.1', $Port); return $true }
    catch { return $false }
    finally { $connection.Dispose() }
}
if (Test-ProjectPort 8888) { throw 'Port 8888 is already in use. Use the existing backend or stop it first.' }
if (Test-ProjectPort 3000) { throw 'Port 3000 is already in use. Use the existing frontend or stop it first.' }
$backendProcess = Start-Process -FilePath $projectPython -ArgumentList '-m','backend.main' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput 'backend.stdout.log' -RedirectStandardError 'backend.stderr.log'
$frontendProcess = Start-Process -FilePath 'npm.cmd' -ArgumentList 'run','dev','--prefix','frontend' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput 'frontend.stdout.log' -RedirectStandardError 'frontend.stderr.log'
Write-Output "Backend PID: $($backendProcess.Id); frontend launcher PID: $($frontendProcess.Id)"
Write-Output 'Open http://127.0.0.1:3000. Logs: backend.stderr.log and frontend.stdout.log.'
Write-Output 'If using Ollama, ensure it is running. See README.md for foreground commands and stopping servers.'
