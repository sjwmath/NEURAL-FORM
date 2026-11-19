param(
    [switch]$Install,
    [int]$Images = 5,
    [int]$Permutations = 999
)
$ErrorActionPreference = 'Stop'
$Project = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Project

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    throw "Python 3.9–3.12 was not found. Install Python 3.12 from python.org, then reopen PowerShell."
}
$VersionText = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0) { throw "Could not start Python." }
if ($VersionText -notmatch '^3\.(9|10|11|12)$') {
    throw "Found Python $VersionText. FlyVis requires Python 3.9–3.12; install Python 3.12."
}

$VenvPython = Join-Path $Project '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) { & python -m venv (Join-Path $Project '.venv') }
if ($Install -or -not (Test-Path (Join-Path $Project '.venv\.neural_form_deps_ready'))) {
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
    & $VenvPython -m pip install -r (Join-Path $Project 'requirements.txt')
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed. FlyVis is officially tested on Linux. Try the WSL2 instructions in README.md."
    }
    New-Item -ItemType File -Force -Path (Join-Path $Project '.venv\.neural_form_deps_ready') | Out-Null
}
$ModelPath = & $VenvPython -c "import flyvis; print(flyvis.results_dir / 'flow/0000/000')" 2>$null
if ($LASTEXITCODE -ne 0) { throw "FlyVis import failed. On Windows, try the WSL2 path in README.md." }
if (-not (Test-Path $ModelPath)) {
    $FlyvisExe = Join-Path $Project '.venv\Scripts\flyvis.exe'
    if (-not (Test-Path $FlyvisExe)) { throw "FlyVis command not found in the virtual environment." }
    & $FlyvisExe download-pretrained
    if ($LASTEXITCODE -ne 0) { throw "FlyVis pretrained model download failed." }
}
& $VenvPython -m src.main --images $Images --permutations $Permutations
if ($LASTEXITCODE -ne 0) { throw "NEURAL FORM run failed. Read the error above; no RSA result is valid unless the run completes." }
