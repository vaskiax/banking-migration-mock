# Portable Terraform Installer for Windows
# This script downloads Terraform and extracts it to the local directory.

$Version = "1.7.0"
$Url = "https://releases.hashicorp.com/terraform/$Version/terraform_${Version}_windows_amd64.zip"
$ZipFile = "terraform.zip"
$InstallDir = "terraform_bin"

Write-Host "--- Initiating Portable Terraform Installation ($Version) ---" -ForegroundColor Cyan

# 1. Download
Write-Host "[1/3] Downloading Terraform from HashiCorp..." -ForegroundColor Green
Invoke-WebRequest -Uri $Url -OutFile $ZipFile

# 2. Extract
Write-Host "[2/3] Extracting to $InstallDir..." -ForegroundColor Green
if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
Expand-Archive -Path $ZipFile -DestinationPath $InstallDir
Remove-Item $ZipFile

# 3. Path instructions
$FullPath = "$PWD\$InstallDir"
Write-Host "[3/3] Installation Complete!" -ForegroundColor Green
Write-Host "`nTo use terraform in this session, run:" -ForegroundColor Yellow
Write-Host "`$env:Path = `"$FullPath;`$env:Path`""

Write-Host "`nTo permanently add to PATH (Admin required):" -ForegroundColor Yellow
Write-Host "[Environment]::SetEnvironmentVariable('Path', `"`$env:Path;$FullPath`", 'User')"

Write-Host "`nVerify installation with: ./$InstallDir/terraform -version" -ForegroundColor Cyan
