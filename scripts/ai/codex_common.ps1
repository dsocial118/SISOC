Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-CodexRepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Get-CodexEnvPath {
    param(
        [string]$RepoRoot
    )

    return Join-Path $RepoRoot ".env"
}

function Get-CodexEnvExamplePath {
    param(
        [string]$RepoRoot
    )

    return Join-Path $RepoRoot ".env.example"
}

function Get-CodexRequiredEnvDefaults {
    param(
        [string]$RepoRoot
    )

    $repoName = Split-Path $RepoRoot -Leaf
    $worktreeName = Split-Path (Split-Path $RepoRoot -Parent) -Leaf
    $projectName = "{0}-{1}" -f $repoName.ToLowerInvariant(), $worktreeName.ToLowerInvariant()
    $projectName = $projectName -replace "[^a-z0-9_-]", "-"

    return [ordered]@{
        "DATABASE_PASSWORD" = "root1-password2"
        "DATABASE_NAME" = "sisoc-local"
        "DOCKER_MYSQL_PORT_FORWARD" = "3307"
        "DOCKER_MYSQL_PORT" = "3306"
        "DOCKER_DJANGO_PORT_FORWARD" = "8001"
        "DOCKER_DJANGO_PORT" = "8000"
        "DOCKER_DEBUGGER_PORT_FORWARD" = "3000"
        "DOCKER_DEBUGGER_PORT" = "3000"
        "RUN_UID" = "0"
        "RUN_GID" = "0"
        "COMPOSE_PROJECT_NAME" = $projectName
    }
}

function Test-CodexTcpPortAvailable {
    param(
        [int]$Port
    )

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        return $true
    }
    catch {
        return $false
    }
    finally {
        if ($listener -ne $null) {
            $listener.Stop()
        }
    }
}

function Get-CodexAvailableTcpPort {
    param(
        [int]$StartPort
    )

    for ($port = $StartPort; $port -lt ($StartPort + 200); $port++) {
        if (Test-CodexTcpPortAvailable -Port $port) {
            return [string]$port
        }
    }

    throw ("No se encontro un puerto libre a partir de {0}" -f $StartPort)
}

function Get-CodexEnvValues {
    param(
        [string]$Path
    )

    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }

    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed -split "=", 2
        if ($parts.Count -ne 2) {
            continue
        }

        $key = $parts[0].Trim()
        $rawValue = $parts[1].Trim()
        if ($rawValue.Contains("#")) {
            $rawValue = ($rawValue -split "#", 2)[0].TrimEnd()
        }
        $values[$key] = $rawValue.Trim('"')
    }

    return $values
}

function Ensure-CodexEnvFile {
    param(
        [string]$RepoRoot
    )

    $envPath = Get-CodexEnvPath -RepoRoot $RepoRoot
    $examplePath = Get-CodexEnvExamplePath -RepoRoot $RepoRoot
    $requiredDefaults = Get-CodexRequiredEnvDefaults -RepoRoot $RepoRoot
    $created = $false
    $updatedKeys = [System.Collections.Generic.List[string]]::new()

    if (-not (Test-Path $envPath)) {
        Copy-Item $examplePath $envPath
        $created = $true
    }

    $envValues = Get-CodexEnvValues -Path $envPath
    if ($created) {
        $requiredDefaults["DOCKER_MYSQL_PORT_FORWARD"] = Get-CodexAvailableTcpPort -StartPort 3307
        $requiredDefaults["DOCKER_DJANGO_PORT_FORWARD"] = Get-CodexAvailableTcpPort -StartPort 8001
        $requiredDefaults["DOCKER_DEBUGGER_PORT_FORWARD"] = Get-CodexAvailableTcpPort -StartPort 3000
    }
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.AddRange([string[]](Get-Content $envPath))

    foreach ($key in $requiredDefaults.Keys) {
        $hasValue = $envValues.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace($envValues[$key])
        if ($hasValue) {
            continue
        }

        $replacement = '{0}="{1}"' -f $key, $requiredDefaults[$key]
        $pattern = '^{0}=' -f [regex]::Escape($key)
        $lineIndex = -1

        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match $pattern) {
                $lineIndex = $i
                break
            }
        }

        if ($lineIndex -ge 0) {
            $lines[$lineIndex] = $replacement
        }
        else {
            $lines.Add($replacement)
        }

        $updatedKeys.Add($key) | Out-Null
    }

    if ($created -or $updatedKeys.Count -gt 0) {
        Set-Content -Path $envPath -Value $lines -Encoding UTF8
    }

    return [pscustomobject]@{
        Path = $envPath
        Created = $created
        UpdatedKeys = [string[]]$updatedKeys
        Values = Get-CodexEnvValues -Path $envPath
    }
}

function Test-CodexDockerAvailable {
    try {
        docker version | Out-Null
        docker compose version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Invoke-CodexCompose {
    param(
        [string]$RepoRoot,
        [string[]]$Arguments
    )

    Push-Location $RepoRoot
    try {
        & docker compose @Arguments
    }
    finally {
        Pop-Location
    }
}

function Test-CodexLocalPythonAvailable {
    try {
        & py -3 --version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Ensure-CodexLocalVenv {
    param(
        [string]$RepoRoot
    )

    $venvPath = Join-Path $RepoRoot ".venv"
    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
    $created = $false

    if (-not (Test-Path $pythonExe)) {
        & py -3 -m venv $venvPath
        $created = $true
    }

    return [pscustomobject]@{
        Path = $venvPath
        PythonExe = $pythonExe
        Created = $created
    }
}

function Ensure-CodexLocalDependencies {
    param(
        [string]$RepoRoot
    )

    $venv = Ensure-CodexLocalVenv -RepoRoot $RepoRoot
    & $venv.PythonExe -m pip install --upgrade pip
    & $venv.PythonExe -m pip install -r (Join-Path $RepoRoot "requirements.txt")

    return $venv
}
