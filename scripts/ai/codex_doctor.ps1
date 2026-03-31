Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "codex_common.ps1")

$repoRoot = Get-CodexRepoRoot
$envPath = Get-CodexEnvPath -RepoRoot $repoRoot
$envValues = Get-CodexEnvValues -Path $envPath
$required = Get-CodexRequiredEnvDefaults -RepoRoot $repoRoot
$composeProject = Get-CodexComposeProjectName -RepoRoot $repoRoot

function Write-StatusLine {
    param(
        [string]$Label,
        [bool]$Ok,
        [string]$Detail
    )

    $status = if ($Ok) { "OK " } else { "FAIL" }
    Write-Host ("[{0}] {1}: {2}" -f $status, $Label, $Detail)
}

Write-Host ("Repo: {0}" -f $repoRoot)
Write-StatusLine -Label "compose-project" -Ok $true -Detail $composeProject
Write-StatusLine -Label ".env" -Ok (Test-Path $envPath) -Detail $envPath

foreach ($key in $required.Keys) {
    $hasValue = $envValues.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace($envValues[$key])
    Write-StatusLine -Label ("env:{0}" -f $key) -Ok $hasValue -Detail (
        $(if ($hasValue) { $envValues[$key] } else { "sin valor" })
    )
}

$dockerAvailable = Test-CodexDockerAvailable
Write-StatusLine -Label "docker" -Ok $dockerAvailable -Detail (
    $(if ($dockerAvailable) { "docker y docker compose disponibles" } else { "docker/compose no disponibles" })
)

if ($dockerAvailable) {
    try {
        Invoke-CodexCompose -RepoRoot $repoRoot -Arguments @("config", "-q")
        Write-StatusLine -Label "compose-config" -Ok $true -Detail "docker compose config -q"
    }
    catch {
        Write-StatusLine -Label "compose-config" -Ok $false -Detail $_.Exception.Message
    }

    try {
        $services = Get-CodexComposeServices -RepoRoot $repoRoot
        if ($services) {
            Write-StatusLine -Label "compose-ps" -Ok $true -Detail ($services -join ", ")
        }
        else {
            Write-StatusLine -Label "compose-ps" -Ok $true -Detail "sin servicios levantados"
        }
    }
    catch {
        Write-StatusLine -Label "compose-ps" -Ok $false -Detail $_.Exception.Message
    }
}
Write-StatusLine -Label "host-python" -Ok $true -Detail "ignorado a proposito: este repo usa Docker Compose para Django/pytest"
