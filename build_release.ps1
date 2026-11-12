# ==============================================================================
# build_release.ps1 - Automated Release Packaging for Agy Session Manager
# Produces:
#   1. Portable ZIP (AgySessionManager-vX.Y.Z-windows-x64-portable.zip)
#   2. Inno Setup Installer (if iscc.exe available)
#   3. SHA256 checksums (SHA256SUMS.txt)
# ==============================================================================

param(
    [string]$Version = "1.0.0",
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Agy Session Manager - Release Packaging v$Version" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verification of icons
Write-Host "`n[1/6] Verifying application icons..." -ForegroundColor Yellow
if (-not (Test-Path "assets\icon.ico") -or -not (Test-Path "assets\icon.png")) {
    Write-Host "  Generating icons via scripts\generate_app_icon.py..."
    python scripts\generate_app_icon.py
}
Write-Host "  Icon assets verified: assets\icon.ico, assets\icon.png" -ForegroundColor Green

# 2. Run Test Suite
if (-not $SkipTests) {
    Write-Host "`n[2/6] Running automated test suites..." -ForegroundColor Yellow
    python tests\test_all.py
    if ($LASTEXITCODE -ne 0) { throw "test_all.py failed!" }
    python tests\test_ui_features.py
    if ($LASTEXITCODE -ne 0) { throw "test_ui_features.py failed!" }
    python tests\test_star_rename.py
    if ($LASTEXITCODE -ne 0) { throw "test_star_rename.py failed!" }
    python tests\test_fork_feature.py
    if ($LASTEXITCODE -ne 0) { throw "test_fork_feature.py failed!" }
    Write-Host "  All test suites passed!" -ForegroundColor Green
} else {
    Write-Host "`n[2/6] Skipping tests (-SkipTests flag passed)..." -ForegroundColor DarkGray
}

# 3. Clean Previous Build Artifacts
Write-Host "`n[3/6] Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\AgySessionManager") { Remove-Item -Recurse -Force "dist\AgySessionManager" }
if (-not (Test-Path "release")) { New-Item -ItemType Directory -Path "release" | Out-Null }
Write-Host "  Cleaned build/ and dist/ directories." -ForegroundColor Green

# 4. Compile with PyInstaller
Write-Host "`n[4/6] Building binary with PyInstaller..." -ForegroundColor Yellow
pyinstaller --clean --noconfirm AgySessionManager.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed!" }

if (-not (Test-Path "dist\AgySessionManager\AgySessionManager.exe")) {
    throw "Executable dist\AgySessionManager\AgySessionManager.exe not found after build!"
}
Write-Host "  PyInstaller build successful: dist\AgySessionManager\AgySessionManager.exe" -ForegroundColor Green

# 5. Package Portable ZIP
Write-Host "`n[5/6] Creating Portable ZIP package..." -ForegroundColor Yellow
$ZipFilename = "AgySessionManager-v$Version-windows-x64-portable.zip"
$ZipPath = Join-Path "release" $ZipFilename

if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }

# Compress dist/AgySessionManager to zip
Compress-Archive -Path "dist\AgySessionManager\*" -DestinationPath $ZipPath -CompressionLevel Optimal
$ZipSize = [math]::Round((Get-Item $ZipPath).Length / 1MB, 2)
Write-Host "  Portable ZIP created: $ZipPath ($ZipSize MB)" -ForegroundColor Green

# 6. Check & Build Inno Setup Installer
Write-Host "`n[6/6] Checking for Inno Setup compiler (iscc.exe)..." -ForegroundColor Yellow
$Iscc = Get-Command "iscc" -ErrorAction SilentlyContinue
if (-not $Iscc) {
    # Check default install locations
    $PossiblePaths = @(
        "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        "C:\Program Files\Inno Setup 6\iscc.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\iscc.exe"
    )
    foreach ($p in $PossiblePaths) {
        if (Test-Path $p) {
            $Iscc = $p
            break
        }
    }
}

if ($Iscc) {
    Write-Host "  Found Inno Setup at: $Iscc" -ForegroundColor Green
    Write-Host "  Compiling installer..." -ForegroundColor Yellow
    & $Iscc "installer\setup.iss"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Installer created in release/ directory!" -ForegroundColor Green
    } else {
        Write-Host "  Inno Setup compilation failed with code $LASTEXITCODE" -ForegroundColor Red
    }
} else {
    Write-Host "  Note: iscc.exe (Inno Setup) not found locally." -ForegroundColor DarkYellow
    Write-Host "  (Installer will automatically be built by GitHub Actions on push tag)." -ForegroundColor DarkGray
}

# 7. Generate SHA-256 Checksums
Write-Host "`n[+] Generating SHA-256 checksums..." -ForegroundColor Yellow
$ReleaseFiles = Get-ChildItem -Path "release" -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" }
$ChecksumLines = @()
foreach ($file in $ReleaseFiles) {
    $hash = (Get-FileHash -Path $file.FullName -Algorithm SHA256).Hash.ToLower()
    $line = "$hash  $($file.Name)"
    $ChecksumLines += $line
    Write-Host "  $line" -ForegroundColor DarkCyan
}
$ChecksumLines | Out-File -FilePath "release\SHA256SUMS.txt" -Encoding ascii -Force
Write-Host "  Checksums written to release\SHA256SUMS.txt" -ForegroundColor Green

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  BUILD & PACKAGING COMPLETE!" -ForegroundColor Green
Write-Host "  Release artifacts located in: $(Resolve-Path release)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
