Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "codex_common.ps1")

$repoRoot = Get-CodexRepoRoot
$envPath = Get-CodexEnvPath -RepoRoot $repoRoot
$envValues = Get-CodexEnvValues -Path $envPath
$required = Get-CodexRequiredEnvDefaults -RepoRoot $repoRoot

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
        $services = Invoke-CodexCompose -RepoRoot $repoRoot -Arguments @("ps", "--format", "json")
        if ($services) {
            Write-StatusLine -Label "compose-ps" -Ok $true -Detail "servicios consultados"
        }
        else {
            Write-StatusLine -Label "compose-ps" -Ok $true -Detail "sin servicios levantados"
        }
    }
    catch {
        Write-StatusLine -Label "compose-ps" -Ok $false -Detail $_.Exception.Message
    }
}

$pyAvailable = Test-CodexLocalPythonAvailable
Write-StatusLine -Label "py-launcher" -Ok $pyAvailable -Detail (
    $(if ($pyAvailable) { (& py -3 --version) } else { "py -3 no disponible" })
)

if ($pyAvailable) {
    try {
        $blackCheck = & py -3 -m black --version 2>&1
        Write-StatusLine -Label "host-black" -Ok $true -Detail $blackCheck[0]
    }
    catch {
        Write-StatusLine -Label "host-black" -Ok $false -Detail $_.Exception.Message
    }

    try {
        $pytestCheck = & py -3 -m pytest --version 2>&1
        Write-StatusLine -Label "host-pytest" -Ok $true -Detail $pytestCheck[0]
    }
    catch {
        Write-StatusLine -Label "host-pytest" -Ok $false -Detail $_.Exception.Message
    }
}
