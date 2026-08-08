# RAG Chat Windows Installer Script (PowerShell)
# Exposes a global 'ragchat' command for Windows

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "          RAG Chat Windows Installer              " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check for Python
$pythonInstalled = $false
try {
    $ver = python --version 2>$null
    if ($ver) { $pythonInstalled = $true }
} catch {}

if (-not $pythonInstalled) {
    Write-Host "[*] Python not found. Installing Python via Winget..." -ForegroundColor Yellow
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    # Refresh env paths
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "[+] Python is already installed." -ForegroundColor Green
}

# 2. Check for Git
$gitInstalled = $false
try {
    $ver = git --version 2>$null
    if ($ver) { $gitInstalled = $true }
} catch {}

if (-not $gitInstalled) {
    Write-Host "[*] Git not found. Installing Git via Winget..." -ForegroundColor Yellow
    winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "[+] Git is already installed." -ForegroundColor Green
}

# 3. Setup workspace directories
$installDir = Join-Path $Home ".ragchat"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}

# 4. Clone or copy code
if (Test-Path "core") {
    Write-Host "[*] Copying local codebase files..." -ForegroundColor Cyan
    Copy-Item -Path ".*", "*" -Destination $installDir -Recurse -Force
} else {
    Write-Host "[*] Cloning RAG Chat repository..." -ForegroundColor Cyan
    git clone https://github.com/soumen888/Rag-Chatbot.git $installDir
}

# 5. Create Virtual Environment & Install requirements
Write-Host "[*] Creating virtual environment..." -ForegroundColor Cyan
Set-Location $installDir
python -m venv venv
& .\venv\Scripts\python.exe -m pip install --upgrade pip
Write-Host "[*] Installing dependencies..." -ForegroundColor Cyan
& .\venv\Scripts\pip.exe install -r requirements.txt

# 6. Create global batch command runner
Write-Host "[*] Creating global execution wrapper..." -ForegroundColor Cyan
$batContent = @"
@echo off
cd /d "$installDir"
.\venv\Scripts\python.exe main.py %*
"@
$batContent | Out-File -FilePath (Join-Path $installDir "ragchat.bat") -Encoding ASCII

# 7. Add to User Path variable
Write-Host "[*] Registering 'ragchat' command in system PATH..." -ForegroundColor Cyan
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$installDir*") {
    [System.Environment]::SetEnvironmentVariable("PATH", "$userPath;$installDir", "User")
    $env:Path = "$env:Path;$installDir"
}

Write-Host "==================================================" -ForegroundColor Green
Write-Host "[+] RAG Chat has been installed successfully!     " -ForegroundColor Green
Write-Host "[+] Restart your terminal and run:  ragchat       " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
