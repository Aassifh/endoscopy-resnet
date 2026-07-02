# Move endoscopy-resnet data onto the Toshiba drive from Windows (NTFS writable).
# Run in PowerShell on a PC with the drive plugged in:
#   cd \\path\to\endoscopy-resnet
#   powershell -ExecutionPolicy Bypass -File scripts\migrate_to_toshiba_windows.ps1
#
# Or copy this script to the drive and run after copying data folders from the Mac.

param(
    [string]$DriveLetter = "",
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

function Find-ToshibaDrive {
    param([string]$Letter)
    if ($Letter) {
        return "${Letter}:"
    }
    Get-Volume | Where-Object {
        $_.FileSystemType -eq 'NTFS' -and $_.DriveLetter -and
        ($_.FileSystemLabel -match 'TOSHIBA' -or $_.FriendlyName -match 'TOSHIBA')
    } | Select-Object -First 1 -ExpandProperty DriveLetter | ForEach-Object { "${_}:" }
}

$drive = Find-ToshibaDrive -Letter $DriveLetter
if (-not $drive) {
    Write-Error "Toshiba NTFS drive not found. Pass -DriveLetter E"
}

$dest = Join-Path $drive "endoscopy-resnet-data"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Write-Host "Destination: $dest"

if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    if (-not (Test-Path (Join-Path $RepoRoot "scripts\prepare_colonoscopy_3class.py"))) {
        Write-Host "Copy data folders from your Mac repo into: $dest"
        Write-Host "  raw, kvasir, hyperkvasir, colonoscopy_3class, checkpoints, jepa_frames"
        Write-Host "Then on the Mac, create symlinks (see docs/setup-external-data.md)."
        exit 0
    }
}

$folders = @(
    @{ Src = Join-Path $RepoRoot "data\raw"; Name = "raw" },
    @{ Src = Join-Path $RepoRoot "data\kvasir"; Name = "kvasir" },
    @{ Src = Join-Path $RepoRoot "data\hyperkvasir"; Name = "hyperkvasir" },
    @{ Src = Join-Path $RepoRoot "data\colonoscopy_3class"; Name = "colonoscopy_3class" },
    @{ Src = Join-Path $RepoRoot "data\hyperkvasir_pathology"; Name = "hyperkvasir_pathology" },
    @{ Src = Join-Path $RepoRoot "data\jepa_frames"; Name = "jepa_frames" },
    @{ Src = Join-Path $RepoRoot "checkpoints"; Name = "checkpoints" }
)

foreach ($item in $folders) {
    $target = Join-Path $dest $item.Name
    if (-not (Test-Path $item.Src)) {
        Write-Host "Skip (missing): $($item.Src)"
        continue
    }
    if (Test-Path $target) {
        Write-Host "Already exists: $target"
        continue
    }
    Write-Host "Move: $($item.Src) -> $target"
    Move-Item -Path $item.Src -Destination $target
}

Write-Host ""
Write-Host "Done on Windows. On the Mac (drive plugged in):"
Write-Host @"

  cd $RepoRoot
  bash scripts/link_external_data.sh "/Volumes/TOSHIBA EXT"

"@
