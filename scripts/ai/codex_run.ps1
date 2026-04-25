param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "bootstrap",
        "doctor",
        "up",
        "shell",
        "test",
        "smoke",
        "black-check",
        "black-format",
        "djlint-check",
        "djlint-format",
        "pylint",
        "manage"
    )]
    [string]$Action,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "codex_common.ps1")

$repoRoot = Get-CodexRepoRoot

function Invoke-CodexBootstrap {
    param(
        [switch]$NoStart,
        [switch]$ExposePorts
    )

    $bootstrapParams = @{}
    if ($NoStart) {
        $bootstrapParams["NoStart"] = $true
    }
    if ($ExposePorts) {
        $bootstrapParams["ExposePorts"] = $true
    }

    & (Join-Path $PSScriptRoot "codex_bootstrap.ps1") @bootstrapParams
}

function Invoke-DjangoOneOffCommand {
    param(
        [string[]]$CommandArgs
    )

    Invoke-CodexBootstrap -NoStart
    Invoke-CodexCompose -RepoRoot $repoRoot -Arguments (@("run", "--rm", "--no-deps", "django") + $CommandArgs)
}

switch ($Action) {
    "bootstrap" {
        $bootstrapParams = @{}
        if ($Args -contains "-NoStart" -or $Args -contains "--no-start") {
            $bootstrapParams["NoStart"] = $true
        }
        if ($Args -contains "-PreferLocalFallback" -or $Args -contains "--prefer-local-fallback") {
            $bootstrapParams["PreferLocalFallback"] = $true
        }
        if ($Args -contains "-ExposePorts" -or $Args -contains "--expose-ports") {
            $bootstrapParams["ExposePorts"] = $true
        }
        & (Join-Path $PSScriptRoot "codex_bootstrap.ps1") @bootstrapParams
        break
    }
    "doctor" {
        & (Join-Path $PSScriptRoot "codex_doctor.ps1")
        break
    }
    "up" {
        Invoke-CodexBootstrap -ExposePorts:($Args -contains "-ExposePorts" -or $Args -contains "--expose-ports")
        break
    }
    "shell" {
        $exposePorts = $Args -contains "-ExposePorts" -or $Args -contains "--expose-ports"
        Invoke-CodexBootstrap -ExposePorts:$exposePorts
        Invoke-CodexCompose -RepoRoot $repoRoot -Arguments @("exec", "django", "bash") -ExposePorts:$exposePorts
        break
    }
    "test" {
        $targetArgs = if ($Args) { $Args } else { @("-n", "auto") }
        Invoke-DjangoOneOffCommand -CommandArgs (@("pytest") + $targetArgs)
        break
    }
    "smoke" {
        Invoke-DjangoOneOffCommand -CommandArgs @("pytest", "-m", "smoke")
        break
    }
    "black-check" {
        $targetArgs = if ($Args) { $Args } else { @(".", "--config", "pyproject.toml") }
        Invoke-DjangoOneOffCommand -CommandArgs (@("black", "--check") + $targetArgs)
        break
    }
    "black-format" {
        $targetArgs = if ($Args) { $Args } else { @(".", "--config", "pyproject.toml") }
        Invoke-DjangoOneOffCommand -CommandArgs (@("black") + $targetArgs)
        break
    }
    "djlint-check" {
        $targetArgs = if ($Args) { $Args } else { @(".", "--configuration=.djlintrc") }
        Invoke-DjangoOneOffCommand -CommandArgs (@("djlint") + $targetArgs + @("--check"))
        break
    }
    "djlint-format" {
        $targetArgs = if ($Args) { $Args } else { @(".", "--configuration=.djlintrc") }
        Invoke-DjangoOneOffCommand -CommandArgs (@("djlint") + $targetArgs + @("--reformat"))
        break
    }
    "pylint" {
        if (-not $Args) {
            throw "pylint requiere al menos una ruta de archivo."
        }
        Invoke-DjangoOneOffCommand -CommandArgs (@("pylint") + $Args + @("--rcfile=.pylintrc"))
        break
    }
    "manage" {
        if (-not $Args) {
            throw "manage requiere argumentos para manage.py."
        }
        Invoke-DjangoOneOffCommand -CommandArgs (@("python", "manage.py") + $Args)
        break
    }
}
