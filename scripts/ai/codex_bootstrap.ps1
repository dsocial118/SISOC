param(
    [switch]$NoStart,
    [switch]$StartDjango
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

if (Test-CodexDockerAvailable) {
    $composeProject = Get-CodexComposeProjectName -RepoRoot $repoRoot
    Write-Host ("Modo principal: Docker aislado (project={0})" -f $composeProject)
    Invoke-CodexCompose -RepoRoot $repoRoot -Arguments @("config", "-q")
    if (-not $NoStart) {
        $servicesToStart = @("mysql")
        if ($StartDjango) {
            $servicesToStart += "django"
        }
        Invoke-CodexCompose -RepoRoot $repoRoot -Arguments (@("up", "-d") + $servicesToStart)
    }
    exit 0
}

throw "Docker no esta disponible. En este repo Codex debe ejecutar Django y pytest dentro de Docker Compose."

