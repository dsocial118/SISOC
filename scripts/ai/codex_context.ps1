param(
    [string]$TargetPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "codex_common.ps1")

$repoRoot = Get-CodexRepoRoot
$scriptPath = Join-Path $repoRoot "scripts/ai/context_memory.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    $command = @("-3", $scriptPath, "preflight")
    if ($TargetPath) {
        $command += @("--target", $TargetPath)
    }
    & py @command
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    $command = @($scriptPath, "preflight")
    if ($TargetPath) {
        $command += @("--target", $TargetPath)
    }
    & python @command
    exit $LASTEXITCODE
}

throw "No se encontro un interprete de Python para ejecutar scripts/ai/context_memory.py."
