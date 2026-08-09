# RAGChat Windows Installer Script (PowerShell)
# Installs RAGChat via Git clone or zip download, sets up Python venv, and registers global 'ragchat' command

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "          RAGChat Windows Installer               " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "[!] Python 3 is required but not installed." -ForegroundColor Red
    Write-Host "    Please install Python from https://www.python.org and run this script again." -ForegroundColor Red
    exit 1
}

Write-Host "[+] Detected Python" -ForegroundColor Green

# 2. Setup workspace directory
$installDir = Join-Path $Home ".ragchat"
$binDir = Join-Path $installDir "bin"
$repoUrl = "https://github.com/soumen888/Rag-Chatbot.git"

if (Test-Path $installDir) {
    Write-Host "[*] Updating existing RAGChat installation in $installDir..." -ForegroundColor Cyan
    Set-Location $installDir
    if (Test-Path ".git") {
        git pull --quiet
    }
} else {
    Write-Host "[*] Installing RAGChat to $installDir..." -ForegroundColor Cyan
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        git clone --quiet $repoUrl $installDir
    } else {
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
        $zipPath = Join-Path $env:TEMP "ragchat-main.zip"
        Invoke-WebRequest -Uri "https://github.com/soumen888/Rag-Chatbot/archive/refs/heads/main.zip" -OutFile $zipPath -UseBasicParsing
        Expand-Archive -Path $zipPath -DestinationPath $env:TEMP -Force
        Copy-Item -Path (Join-Path $env:TEMP "Rag-Chatbot-main\*") -Destination $installDir -Recurse -Force
    }
}

Set-Location $installDir

# 3. Create Virtual Environment
Write-Host "[*] Setting up Python virtual environment..." -ForegroundColor Cyan
& $pythonCmd.Source -m venv venv
$venvPython = Join-Path $installDir "venv\Scripts\python.exe"

# 4. Install Dependencies
Write-Host "[*] Installing required dependencies (LiteLLM, ChromaDB, etc.)..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements.txt --quiet

# 5. Playwright Browsers setup
Write-Host "[*] Setting up web crawler headless browser..." -ForegroundColor Cyan
try {
    & $venvPython -m playwright install chromium --quiet
} catch {
    # Ignore playwright install errors if browser already present
}

# 6. Create executable CMD launcher script
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
}

$cmdPath = Join-Path $binDir "ragchat.cmd"
$cmdContent = @"
@echo off
"$venvPython" "$installDir\main.py" %*
"@
Set-Content -Path $cmdPath -Value $cmdContent

# 7. Add bin directory to User PATH
Write-Host "[*] Registering 'ragchat' command in user PATH..." -ForegroundColor Cyan
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$binDir*") {
    [System.Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
    $env:Path = "$env:Path;$binDir"
}

Write-Host "==================================================" -ForegroundColor Green
Write-Host "[+] RAGChat has been installed successfully!      " -ForegroundColor Green
Write-Host "[+] Restart your terminal and run:  ragchat       " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
