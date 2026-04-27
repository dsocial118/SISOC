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

function Get-CodexComposeOverridePath {
    param(
        [string]$RepoRoot
    )

    return Join-Path $RepoRoot "docker-compose.codex.yml"
}

function Get-CodexComposeFileArgs {
    param(
        [string]$RepoRoot,
        [switch]$ExposePorts
    )

    $args = @("-f", "docker-compose.yml")
    $overridePath = Get-CodexComposeOverridePath -RepoRoot $RepoRoot

    if (-not $ExposePorts -and (Test-Path $overridePath)) {
        $args += @("-f", "docker-compose.codex.yml")
    }

    return $args
}

function Get-CodexWorktreeContext {
    param(
        [string]$RepoRoot
    )

    $currentPath = (Resolve-Path -LiteralPath $RepoRoot).Path
    while ($true) {
        $parentPath = Split-Path $currentPath -Parent
        if (-not $parentPath -or $parentPath -eq $currentPath) {
            break
        }

        if ((Split-Path $parentPath -Leaf) -ieq "worktrees") {
            return [pscustomobject]@{
                Root = $parentPath
                Slug = Split-Path $currentPath -Leaf
            }
        }

        $currentPath = $parentPath
    }

    return [pscustomobject]@{
        Root = $null
        Slug = $null
    }
}

function Get-CodexRequiredEnvDefaults {
    param(
        [string]$RepoRoot
    )

    $projectName = Get-CodexComposeProjectName -RepoRoot $RepoRoot

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

function Get-CodexComposeProjectName {
    param(
        [string]$RepoRoot
    )

    $repoLeaf = Split-Path $RepoRoot -Leaf
    $worktreeContext = Get-CodexWorktreeContext -RepoRoot $RepoRoot
    $suffix = if (-not [string]::IsNullOrWhiteSpace($worktreeContext.Slug)) {
        $worktreeContext.Slug
    }
    elseif ($repoLeaf -ieq "SISOC") {
        "main"
    }
    else {
        $repoLeaf
    }

    $projectName = "sisoc-{0}" -f $suffix.ToLowerInvariant()
    return ($projectName -replace "[^a-z0-9_-]", "-")
}

function Set-CodexUtf8NoBomContent {
    param(
        [string]$Path,
        [string[]]$Value
    )

    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllLines($Path, $Value, $encoding)
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
        Set-CodexUtf8NoBomContent -Path $envPath -Value ([string[]]$lines)
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
        & docker version *> $null
        if ($LASTEXITCODE -ne 0) {
            return $false
        }

        & docker compose version *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Invoke-CodexCompose {
    param(
        [string]$RepoRoot,
        [string[]]$Arguments,
        [switch]$ExposePorts
    )

    Push-Location $RepoRoot
    try {
        $composeFileArgs = Get-CodexComposeFileArgs -RepoRoot $RepoRoot -ExposePorts:$ExposePorts
        $allArgs = @() + $composeFileArgs + $Arguments
        & docker compose @allArgs
        if ($LASTEXITCODE -ne 0) {
            throw ("docker compose fallo con exit code {0}." -f $LASTEXITCODE)
        }
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
