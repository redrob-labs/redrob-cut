<#
.SYNOPSIS
  Build and package Redrob Film for Windows.

.DESCRIPTION
  Produces, in $env:DIST (default: dist/release), for Windows x64 (the only Windows release target;
  Redrob Launcher and the in-app updater, apps/redrob-film-app/src/update.rs, look for exactly these names):
    redrob-film-<version>-windows-x64.msi            per-machine installer (WiX v5)
    redrob-film-<version>-windows-x64-portable.zip   redrob-film.exe + redrob-film-cli.exe + portable.txt

  The binaries link the C runtime statically (+crt-static), so neither the MSI nor the portable
  zip needs the Visual C++ redistributable. This script does not sign: the release workflow signs
  the staged executables (after -BuildOnly) and the MSI (after -SkipBuild) with the shared
  redrob-labs/.github/actions/sign-windows action, so the portable zip carries signed executables
  and the installer is signed last. A local run produces unsigned packages.

  Needs: Rust (MSVC toolchain + the target), the Windows SDK (rc.exe, signtool.exe),
  and WiX v5: dotnet tool install --global wix --version 5.0.2

.EXAMPLE
  pwsh packaging/windows/package.ps1 -Arch x64
  pwsh packaging/windows/package.ps1 -Arch x64 -BuildOnly  # CI: build first, log in to Azure, then -SkipBuild
  pwsh packaging/windows/package.ps1 -Arch x64 -SkipBuild
#>
param(
  [ValidateSet('x64')] [string] $Arch = 'x64',
  [switch] $SkipBuild,
  [switch] $BuildOnly
)
if ($SkipBuild -and $BuildOnly) { throw '-SkipBuild and -BuildOnly exclude each other' }
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

function Invoke-Native([string] $What, [scriptblock] $Block) {
  Write-Output "==> $What"
  & $Block
  if ($LASTEXITCODE -ne 0) { throw "$What failed with exit code $LASTEXITCODE" }
}

# The version lives in one place: [workspace.package] version in the root Cargo.toml.
$Version = $env:FILMCRAFT_VERSION
if (-not $Version) {
  $inPkg = $false
  foreach ($line in Get-Content (Join-Path $Root 'Cargo.toml')) {
    if ($line -match '^\s*\[') { $inPkg = ($line.Trim() -eq '[workspace.package]'); continue }
    if ($inPkg -and $line -match '^\s*version\s*=\s*"([^"]+)"') { $Version = $Matches[1]; break }
  }
}
if (-not $Version) { throw 'could not read [workspace.package] version from Cargo.toml' }
# MSI ProductVersion is numeric (major.minor.build); pre-release tags are dropped there.
$MsiVersion = ($Version -split '-')[0]

$Target = 'x86_64-pc-windows-msvc'
$Dist = if ($env:DIST) { $env:DIST } else { Join-Path $Root 'dist\release' }
$TargetDir = if ($env:CARGO_TARGET_DIR) { $env:CARGO_TARGET_DIR } else { Join-Path $Root 'target' }
New-Item -ItemType Directory -Force -Path $Dist | Out-Null

if (-not $env:FILMCRAFT_BUILD_SHA) { $env:FILMCRAFT_BUILD_SHA = (git -C $Root rev-parse HEAD 2>$null) }
if (-not $env:FILMCRAFT_BUILD_DATE) { $env:FILMCRAFT_BUILD_DATE = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd') }

Write-Output "Redrob Film $Version for Windows $Arch ($Target)"

if (-not $SkipBuild) {
  # Static CRT: no VC++ redistributable needed. Scoped to the target so host build scripts and
  # proc-macros are unaffected.
  $flagVar = 'CARGO_TARGET_' + ($Target.ToUpper() -replace '-', '_') + '_RUSTFLAGS'
  [Environment]::SetEnvironmentVariable($flagVar, '-C target-feature=+crt-static')
  # Fail the build (rather than warn) if the icon/VERSIONINFO can't be embedded.
  $env:FILMCRAFT_REQUIRE_WINRES = '1'
  Invoke-Native "cargo build ($Target)" { cargo build --release --locked -p redrob-film-app -p redrob-film-cli --target $Target }
}
$Bin = Join-Path $TargetDir "$Target\release"
$Stage = Join-Path $TargetDir "windows-package\$Arch"

# The release workflow builds and stages first, signs the staged executables, then packages in a
# second invocation, so the short-lived OpenID Connect login happens right before signing instead
# of expiring during a long build. The stage is therefore filled in the build phase and only read
# in the package phase.
if (-not $SkipBuild) {
  Remove-Item -Recurse -Force $Stage -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path $Stage | Out-Null
  Copy-Item (Join-Path $Bin 'redrob-film.exe'), (Join-Path $Bin 'redrob-film-cli.exe') $Stage
}
if ($BuildOnly) { exit 0 }

# Check both binaries' PE headers before packaging. Machine (COFF header) must be x64 (0x8664), so
# nothing else can ever ship under the x64 name. Subsystem (optional header): 2 = Windows GUI, 3 = console.
# The app must be GUI (no console window opens with it); the CLI must stay console so its output
# reaches the terminal.
function Get-PeHeader([string] $Path) {
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  $pe = [BitConverter]::ToInt32($bytes, 0x3C)
  return @{ Machine = [BitConverter]::ToUInt16($bytes, $pe + 4); Subsystem = [BitConverter]::ToUInt16($bytes, $pe + 0x5C) }
}
$Machine = 0x8664
foreach ($check in @(@('redrob-film.exe', 2), @('redrob-film-cli.exe', 3))) {
  if (-not (Test-Path (Join-Path $Stage $check[0]))) { throw "$($check[0]) is not staged in $Stage; run with -BuildOnly first" }
  $h = Get-PeHeader (Join-Path $Stage $check[0])
  if ($h.Machine -ne $Machine) { throw "$($check[0]) is for machine 0x$('{0:X}' -f $h.Machine), expected 0x$('{0:X}' -f $Machine) ($Arch)" }
  if ($h.Subsystem -ne $check[1]) { throw "$($check[0]) has PE subsystem $($h.Subsystem), expected $($check[1])" }
  Write-Output "ok $($check[0]): $Arch, PE subsystem $($h.Subsystem)"
}
# ---- MSI ---------------------------------------------------------------------------------------
$Msi = Join-Path $Dist "redrob-film-$Version-windows-$Arch.msi"
Invoke-Native 'wix build' {
  wix build (Join-Path $PSScriptRoot 'redrob-film.wxs') -arch $Arch `
    -d "Version=$MsiVersion" -d "BinDir=$Stage" -d "IconPath=$(Join-Path $Root 'assets\app-icon\redrob-film.ico')" `
    -o $Msi
}
# wix writes its debug symbols (.wixpdb) next to the MSI; keep them out of the release assets.
Remove-Item -Force -ErrorAction SilentlyContinue ([IO.Path]::ChangeExtension($Msi, '.wixpdb'))

# ---- portable zip ------------------------------------------------------------------------------
$Portable = Join-Path $TargetDir "windows-package\redrob-film-$Version-windows-$Arch-portable"
Remove-Item -Recurse -Force $Portable -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Portable | Out-Null
Copy-Item (Join-Path $Stage '*.exe') $Portable
# The marker that makes Redrob Film keep its data in .\data next to the exe instead of %APPDATA% (#139).
Set-Content -Encoding ascii -Path (Join-Path $Portable 'portable.txt') -Value @(
  'Redrob Film portable: preferences, presets, logs and crash recovery are kept in the data folder',
  'next to redrob-film.exe. Delete this file to use %APPDATA%\Redrob Film instead.'
)
foreach ($f in 'README.md', 'LICENSE', 'LICENSE-MIT', 'LICENSE-APACHE') {
  $p = Join-Path $Root $f
  if (Test-Path $p) { Copy-Item $p $Portable }
}
# Licences of the embedded craft-fonts fonts (builds with CRAFT_FONTS_DIR) as OFL-<family>.txt.
if ($env:CRAFT_FONTS_DIR) {
  foreach ($lic in Get-ChildItem -Path (Join-Path $env:CRAFT_FONTS_DIR 'fonts\*\OFL.txt') -ErrorAction SilentlyContinue) {
    Copy-Item $lic.FullName (Join-Path $Portable "OFL-$($lic.Directory.Name).txt")
  }
}
$Zip = Join-Path $Dist "redrob-film-$Version-windows-$Arch-portable.zip"
Remove-Item -Force $Zip -ErrorAction SilentlyContinue
Compress-Archive -Path $Portable -DestinationPath $Zip

# Smoke-test the CLI.
Invoke-Native 'redrob-film-cli --version' { & (Join-Path $Stage 'redrob-film-cli.exe') --version }
Get-Item $Msi, $Zip | Format-Table Name, Length
