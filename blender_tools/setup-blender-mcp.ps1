# v3: Installs Blender, uv, and MCP for Blender (ahujasid/blender-mcp), then
# registers the "blender" MCP server in Claude Desktop with telemetry off.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$log = Join-Path $PSScriptRoot 'blender-mcp-setup.log'
Start-Transcript -Path $log -Force | Out-Null
function Run($exe, [string[]]$a) { & $exe @a 2>&1 | Out-String -Stream | ForEach-Object { Write-Host $_ }; Write-Host "(exit code $LASTEXITCODE)" }
function Find-Blender { Get-ChildItem "$env:ProgramFiles\Blender Foundation\Blender*\blender.exe" -ErrorAction SilentlyContinue | Sort-Object FullName | Select-Object -Last 1 }

Write-Host '=== 1/4 Blender ==='
$blender = Find-Blender
if (-not $blender) {
    try {
        # Official Blender mirror (download.blender.org sits behind a bot check)
        $url  = 'https://mirrors.ocf.berkeley.edu/blender/release/Blender5.3/blender-5.3.0-windows-x64.msi'
        $hash = '3FF4EC8A488BE1148AA2BDB2CB229BE21B8050E75931DA617934CAC254DD726C'
        $dest = Join-Path $env:TEMP 'blender-5.3.0-windows-x64.msi'
        Write-Host "Downloading Blender 5.3.0 (about 350 MB) from $url ..."
        Start-BitsTransfer -Source $url -Destination $dest -ErrorAction SilentlyContinue
        if (-not (Test-Path $dest)) { Invoke-WebRequest $url -OutFile $dest -UseBasicParsing }
        $got = (Get-FileHash $dest -Algorithm SHA256).Hash
        if ($got -ne $hash) { throw "Checksum mismatch ($got), not installing" }
        Write-Host 'Checksum OK. Installing (approve the admin prompt if Windows shows one)...'
        $p = Start-Process msiexec.exe -ArgumentList "/i `"$dest`" /passive /norestart" -Verb RunAs -Wait -PassThru
        Write-Host "msiexec exit code $($p.ExitCode)"
        $blender = Find-Blender
    } catch { Write-Host "Blender download/install failed: $_" -ForegroundColor Red }
}
if ($blender) { Write-Host "Blender OK: $($blender.FullName)" -ForegroundColor Green } else { Write-Host 'BLENDER INSTALL FAILED' -ForegroundColor Red }

Write-Host '=== 2/4 uv ==='
function Find-Uvx {
    $cmd = Get-Command uvx -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($d in @("$env:USERPROFILE\.local\bin", "$env:USERPROFILE\.cargo\bin")) {
        if (Test-Path (Join-Path $d 'uvx.exe')) { return (Join-Path $d 'uvx.exe') }
    }
    return $null
}
$uvx = Find-Uvx
if (-not $uvx) {
    # uv 0.13.8 is bundled next to this script (official release, checksum verified)
    $bin = "$env:USERPROFILE\.local\bin"
    New-Item -ItemType Directory -Force -Path $bin | Out-Null
    Copy-Item (Join-Path $PSScriptRoot 'uv\*.exe') $bin -Force
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if (-not $userPath) { $userPath = '' }
    if (($userPath -split ';') -notcontains $bin) {
        [Environment]::SetEnvironmentVariable('Path', ($bin + ';' + $userPath).TrimEnd(';'), 'User')
        Write-Host "Added $bin to your user PATH"
    }
    $uvx = Find-Uvx
}
if (-not $uvx) { Write-Host 'UV INSTALL FAILED' -ForegroundColor Red; Stop-Transcript | Out-Null; Read-Host 'Press Enter to close'; exit 1 }
Write-Host "uvx OK: $uvx" -ForegroundColor Green
$env:Path = "$(Split-Path $uvx);$env:Path"

Write-Host '=== 3/4 MCP for Blender setup (addon + Claude Desktop config) ==='
$env:DISABLE_TELEMETRY = 'true'
Run $uvx @('--refresh-package','mcp-for-blender','mcp-for-blender@latest','setup','--yes')

Write-Host '=== 4/4 Turn telemetry off in the Claude Desktop entry ==='
$cfgs = @("$env:APPDATA\Claude\claude_desktop_config.json")
$cfgs += Get-ChildItem "$env:LOCALAPPDATA\Packages\Claude_*\LocalCache\Roaming\Claude\claude_desktop_config.json" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
foreach ($cfg in $cfgs) {
    if (-not (Test-Path $cfg)) { Write-Host "Not present: $cfg"; continue }
    try {
        $j = [IO.File]::ReadAllText($cfg) | ConvertFrom-Json
        $b = $j.mcpServers.blender
        if ($b) {
            Copy-Item $cfg "$cfg.pre-telemetry.bak" -Force
            $b | Add-Member -NotePropertyName env -NotePropertyValue ([pscustomobject]@{ DISABLE_TELEMETRY = 'true' }) -Force
            $out = $j | ConvertTo-Json -Depth 50
            $null = $out | ConvertFrom-Json
            [IO.File]::WriteAllText($cfg, $out, (New-Object Text.UTF8Encoding($false)))
            Write-Host "Updated $cfg"
            Write-Host ($j.mcpServers | ConvertTo-Json -Depth 10)
        } else { Write-Host "No blender entry in $cfg" }
    } catch { Write-Host "Could not patch $cfg : $_" -ForegroundColor Yellow }
}

Write-Host ''
Write-Host 'DONE. Fully quit Claude (system tray > Quit), reopen it, then open Blender.' -ForegroundColor Green
Stop-Transcript | Out-Null
Read-Host 'Press Enter to close'
