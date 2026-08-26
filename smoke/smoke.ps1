# Phase 0 smoke test: prove the headless render path is alive end to end.
# Renders a known bundled Material Maker example and asserts a non-empty PNG appears.
# Exits 0 on success, non-zero with a reason on failure.

$ErrorActionPreference = "Stop"

# --- Resolve config: .env if present, else known machine defaults ---
$root = Split-Path -Parent $PSScriptRoot
$godot   = $env:MM_GODOT_BINARY
$project = $env:MM_PROJECT_PATH
$envFile = Join-Path $root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $name = $matches[1].Trim(); $val = $matches[2].Trim()
            if ($name -eq "MM_GODOT_BINARY") { $godot = $val }
            if ($name -eq "MM_PROJECT_PATH") { $project = $val }
        }
    }
}
if (-not $godot)   { $godot   = "C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64.exe" }
if (-not $project) { $project = "C:\Projects-local\z-Git\material-maker" }

# Prefer the _console.exe variant so stdout/stderr are captured. The GUI exe on
# Windows does not attach to the console, so its logs come back empty.
$console = $godot -replace '\.exe$', '_console.exe'
if (Test-Path $console) { $godot = $console }

Write-Host "Godot:   $godot"
Write-Host "Project: $project"

if (-not (Test-Path $godot))   { Write-Error "Godot binary not found: $godot"; exit 2 }
if (-not (Test-Path $project)) { Write-Error "MM project not found: $project"; exit 2 }

$example = Join-Path $project "material_maker\examples\bricks.ptex"
if (-not (Test-Path $example)) { Write-Error "Example not found: $example"; exit 2 }

$outdir = Join-Path $env:TEMP ("mm_smoke_" + [System.Guid]::NewGuid().ToString("N").Substring(0,8))
New-Item -ItemType Directory -Path $outdir | Out-Null

# NOTE: Godot 4 reserves --export as an engine flag; Material Maker's app-level
# flag is --export-material. parse_args.tscn is the project main scene, so it must
# NOT be passed as an argument (it would be treated as a material file to load).
Write-Host "Rendering bricks.ptex -> $outdir ..."
& $godot --path $project --export-material $example -t "Godot/Godot 4 Standard" -o $outdir --size 256 *> (Join-Path $outdir "render.log")

$pngs = Get-ChildItem -Path $outdir -Filter *.png -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 0 }
if ($pngs.Count -gt 0) {
    Write-Host "SMOKE PASS: produced $($pngs.Count) PNG(s):"
    $pngs | ForEach-Object { Write-Host ("  " + $_.Name + " (" + $_.Length + " bytes)") }
    exit 0
} else {
    Write-Error "SMOKE FAIL: no non-empty PNG produced. See $outdir\render.log"
    exit 1
}
