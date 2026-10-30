# Builds the installer only: publishes to installer\stage (the live publish\CSpace folder is untouched), then compiles with Inno. Installs and runs nothing.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
Push-Location $root
try {
  Push-Location SpaceshipApp\SpaceshipUI; npm run build; if ($LASTEXITCODE) { throw "ui build failed" }; Pop-Location
  dotnet publish SpaceshipApp\ShipCore.App -p:PublishProfile=Folder "-p:PublishDir=$root\installer\stage\CSpace\"; if ($LASTEXITCODE) { throw "publish failed" }
  $iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $iscc) { throw "Inno Setup 6 not found" }
  & $iscc installer\CSpace.iss; if ($LASTEXITCODE) { throw "iscc failed" }
} finally { Pop-Location }
