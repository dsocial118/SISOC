param(
    [switch]$NoStart,
    [switch]$PreferLocalFallback,
    [switch]$ExposePorts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "codex_common.ps1")

$repoRoot = Get-CodexRepoRoot
$envResult = Ensure-CodexEnvFile -RepoRoot $repoRoot

Write-Host ("Repo: {0}" -f $repoRoot)
Write-Host ("Env: {0}" -f $envResult.Path)
if ($envResult.Created) {
    Write-Host "Se creo .env desde .env.example"
}
if ($envResult.UpdatedKeys.Count -gt 0) {
    Write-Host ("Se completaron defaults: {0}" -f ($envResult.UpdatedKeys -join ", "))
}

if (-not $PreferLocalFallback -and (Test-CodexDockerAvailable)) {
    Write-Host "Modo principal: Docker"
    Invoke-CodexCompose -RepoRoot $repoRoot -Arguments @("config", "-q") -ExposePorts:$ExposePorts
    if (-not $NoStart) {
        Invoke-CodexCompose -RepoRoot $repoRoot -Arguments @("up", "-d", "mysql", "django") -ExposePorts:$ExposePorts
    }
    exit 0
}

if (-not (Test-CodexLocalPythonAvailable)) {
    throw "No hay Docker disponible y tampoco se encontro 'py -3' para el fallback local."
}

Write-Warning "Docker no esta disponible. Se usara fallback local con .venv."
$venv = Ensure-CodexLocalDependencies -RepoRoot $repoRoot
Write-Host ("Venv listo: {0}" -f $venv.Path)

