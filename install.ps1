# RAG Chat Windows Installer Script (PowerShell)
# Installs global 'ragchat' command on Windows in seconds

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "          RAG Chat Windows Installer              " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Setup workspace directory
$installDir = Join-Path $Home ".ragchat\bin"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

$exePath = Join-Path $installDir "ragchat.exe"
$downloadUrl = "https://github.com/soumen888/homebrew-ragchat/releases/latest/download/ragchat-windows-x64.exe"

# 2. Download executable
Write-Host "[*] Downloading standalone RAG Chat binary..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $exePath -UseBasicParsing
} catch {
    Write-Host "[!] Failed to download binary from releases. Please check your internet connection or verify a release exists." -ForegroundColor Red
    exit 1
}

# 3. Add to User PATH variable
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
