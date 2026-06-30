$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = "C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"
$targetScript = Join-Path $scriptDir "ai_news_daily.py"
$logDir = Join-Path $scriptDir "logs"
$logPath = Join-Path $logDir ("ai_news_daily_{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "未找到 Python: $pythonPath"
}

New-Item -ItemType Directory -Path $logDir -Force | Out-Null

Push-Location $scriptDir
try {
    & $pythonPath $targetScript *>&1 | Tee-Object -FilePath $logPath -Append
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
