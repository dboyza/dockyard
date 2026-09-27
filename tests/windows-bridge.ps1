# Contract test using real PowerShell parsing and invocation, with only WSL replaced.
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent
$global:DockyardTestExitCode = 0
$global:DockyardTestCalls = [System.Collections.Generic.List[object]]::new()
function global:wsl.exe {
    $global:DockyardTestCalls.Add(@($args))
    $global:LASTEXITCODE = $global:DockyardTestExitCode
    if ($args -contains 'printenv') { return '/home/test user' }
}
function Assert-Arguments($Actual, $Expected) {
    if (($Actual | ConvertTo-Json -Compress) -cne ($Expected | ConvertTo-Json -Compress)) {
        throw "Unexpected WSL arguments: $($Actual | ConvertTo-Json -Compress)"
    }
}
& (Join-Path $Root 'dockyard.ps1') -Distribution 'Ubuntu Test' -LinuxProjectPath '~/code/dockyard with spaces' -DockyardArguments @('--data-dir', '/tmp/profile $literal', 'doctor')
Assert-Arguments $global:DockyardTestCalls[0] @('--distribution', 'Ubuntu Test', '--exec', 'printenv', 'HOME')
Assert-Arguments $global:DockyardTestCalls[1] @('--distribution', 'Ubuntu Test', '--cd', '/home/test user/code/dockyard with spaces', '--exec', './dockyard', '--data-dir', '/tmp/profile $literal', 'doctor')
$global:DockyardTestCalls.Clear()
& (Join-Path $Root 'scripts/install-wsl.ps1') -Distribution 'Ubuntu Test' -LinuxProjectPath '/home/test user/code/dockyard'
Assert-Arguments $global:DockyardTestCalls[0] @('--distribution', 'Ubuntu Test', '--cd', '/home/test user/code/dockyard', '--exec', 'bash', 'scripts/install.sh')
$global:DockyardTestCalls.Clear()
$Rejected = $false
try { & (Join-Path $Root 'dockyard.ps1') -LinuxProjectPath '/mnt/c/project' }
catch { $Rejected = $true }
if (-not $Rejected -or $global:DockyardTestCalls.Count -ne 0) { throw 'Windows mount path was not rejected before invoking WSL.' }
$global:DockyardTestCalls.Clear()
& (Join-Path $Root 'dockyard.ps1') doctor
Assert-Arguments $global:DockyardTestCalls[1] @('--distribution', 'Ubuntu', '--cd', '/home/test user/code/dockyard', '--exec', './dockyard', 'doctor')
$global:DockyardTestExitCode = 37
$global:DockyardTestCalls.Clear()
& (Join-Path $Root 'dockyard.ps1') -LinuxProjectPath '~/code/dockyard'
if ($LASTEXITCODE -ne 37 -or $global:DockyardTestCalls.Count -ne 1) { throw 'Failed WSL home discovery did not stop and propagate the exit code.' }
Remove-Variable DockyardTestExitCode -Scope Global
Remove-Item Function:\wsl.exe
Remove-Variable DockyardTestCalls -Scope Global
Write-Output 'Windows bridge contracts passed: distribution, spaces, literal arguments, installer, mount rejection, and exit status.'
# The expected failure above must not become the CI wrapper's process exit status.
exit 0
