[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$BuildDir = Join-Path ([System.IO.Path]::GetTempPath()) ("suiyu-phase0-" + [guid]::NewGuid().ToString('N'))
$TempCreated = $false
$Completed = $false

function Invoke-NativeStep {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [string]$WorkingDirectory,
        [Parameter(Mandatory)] [scriptblock]$Action
    )

    Write-Host "==> $Name"
    Push-Location $WorkingDirectory
    try {
        $captured = @(& $Action 2>&1 | ForEach-Object { $_.ToString() })
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    foreach ($line in $captured) {
        Write-Host $line
    }

    if ($exitCode -ne 0) {
        throw "$Name failed with exit code $exitCode"
    }

    return $captured
}

function Assert-ExactOutput {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [object[]]$Actual,
        [Parameter(Mandatory)] [string]$Expected
    )

    $text = (($Actual | ForEach-Object { $_.ToString().TrimEnd("`r", "`n") }) -join "`n").Trim()
    if ($text -ne $Expected) {
        throw "$Name produced unexpected output: '$text'"
    }
}

try {
    New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
    $TempCreated = $true
    $GoCache = Join-Path $BuildDir 'go-cache'
    $GoModuleCache = Join-Path $BuildDir 'go-mod-cache'
    $CargoHome = Join-Path $BuildDir 'cargo-home'
    $CargoTarget = Join-Path $BuildDir 'cargo-target'
    foreach ($path in @($GoCache, $GoModuleCache, $CargoHome, $CargoTarget)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }

    $savedEnvironment = @{
        GOTOOLCHAIN = $env:GOTOOLCHAIN
        GOROOT = $env:GOROOT
        GOPATH = $env:GOPATH
        GOENV = $env:GOENV
        GOTMPDIR = $env:GOTMPDIR
        GOPROXY = $env:GOPROXY
        GOCACHE = $env:GOCACHE
        GOMODCACHE = $env:GOMODCACHE
        CARGO_HOME = $env:CARGO_HOME
        CARGO_TARGET_DIR = $env:CARGO_TARGET_DIR
    }
    $env:GOTOOLCHAIN = 'local'
    Remove-Item Env:GOROOT -ErrorAction SilentlyContinue
    Remove-Item Env:GOPATH -ErrorAction SilentlyContinue
    Remove-Item Env:GOENV -ErrorAction SilentlyContinue
    Remove-Item Env:GOTMPDIR -ErrorAction SilentlyContinue
    Remove-Item Env:GOPROXY -ErrorAction SilentlyContinue
    $env:GOCACHE = $GoCache
    $env:GOMODCACHE = $GoModuleCache
    $env:CARGO_HOME = $CargoHome
    $env:CARGO_TARGET_DIR = $CargoTarget

    $GoRoot = Join-Path $RepoRoot 'compiler-go'
    $RustManifest = Join-Path $RepoRoot 'runtime-rust/Cargo.toml'

    $formatOutput = Invoke-NativeStep -Name 'Go format' -WorkingDirectory $GoRoot -Action {
        & gofmt -l main.go main_test.go
    }
    if ($formatOutput.Count -ne 0) {
        throw "Go format reported unformatted files: $($formatOutput -join ', ')"
    }

    Invoke-NativeStep -Name 'Rust format' -WorkingDirectory $RepoRoot -Action {
        & cargo fmt --manifest-path $RustManifest --all -- --check
    } | Out-Null

    Invoke-NativeStep -Name 'Go tests' -WorkingDirectory $GoRoot -Action {
        & go test -count=1 ./...
    } | Out-Null

    Invoke-NativeStep -Name 'Rust tests' -WorkingDirectory $RepoRoot -Action {
        & cargo test --locked --manifest-path $RustManifest
    } | Out-Null

    $GoExe = Join-Path $BuildDir 'suiyu-go-phase0.exe'
    Invoke-NativeStep -Name 'Go build' -WorkingDirectory $GoRoot -Action {
        & go build -trimpath -o $GoExe .
    } | Out-Null
    $goRunOutput = Invoke-NativeStep -Name 'Go startup' -WorkingDirectory $GoRoot -Action {
        & $GoExe
    }
    Assert-ExactOutput -Name 'Go startup' -Actual $goRunOutput -Expected 'suiyu-go-phase0'

    Invoke-NativeStep -Name 'Rust build' -WorkingDirectory $RepoRoot -Action {
        & cargo build --locked --manifest-path $RustManifest
    } | Out-Null
    $RustExe = Join-Path $CargoTarget 'debug/suiyu-phase0-runtime.exe'
    if (-not (Test-Path $RustExe)) {
        throw "Rust build did not produce $RustExe"
    }
    $rustRunOutput = Invoke-NativeStep -Name 'Rust startup' -WorkingDirectory $RepoRoot -Action {
        & $RustExe
    }
    Assert-ExactOutput -Name 'Rust startup' -Actual $rustRunOutput -Expected 'suiyu-rust-phase0'

    $Completed = $true
    Write-Host 'Phase 0 checks passed.'
}
catch {
    Write-Error $_
    if ($TempCreated) {
        Write-Warning "Temporary build directory retained for inspection: $BuildDir"
    }
    exit 1
}
finally {
    if ($savedEnvironment) {
        foreach ($name in $savedEnvironment.Keys) {
            $value = $savedEnvironment[$name]
            if ($null -eq $value) {
                Remove-Item "Env:$name" -ErrorAction SilentlyContinue
            }
            else {
                Set-Item "Env:$name" $value
            }
        }
    }
    if ($Completed -and $TempCreated -and (Test-Path $BuildDir)) {
        Remove-Item -LiteralPath $BuildDir -Recurse -Force
    }
}
