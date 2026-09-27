# Launch Dockyard through WSL 2 without changing the default distribution or Windows settings.
[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$Distribution = 'Ubuntu',
    [string]$LinuxProjectPath = '~/code/dockyard',
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$DockyardArguments = @()
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'Install WSL 2 and an Ubuntu distribution first: https://learn.microsoft.com/windows/wsl/install'
}
if ($LinuxProjectPath.StartsWith('~/')) {
    $LinuxHome = (& wsl.exe --distribution $Distribution --exec printenv HOME)
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $LinuxProjectPath = $LinuxHome.TrimEnd() + '/' + $LinuxProjectPath.Substring(2)
}
if (-not $LinuxProjectPath.StartsWith('/') -or $LinuxProjectPath.StartsWith('/mnt/')) {
    throw 'Use a project path in the Linux filesystem, for example ~/code/dockyard.'
}
# WSL receives individual arguments and a working directory; no shell source is interpolated.
& wsl.exe --distribution $Distribution --cd $LinuxProjectPath --exec ./dockyard @DockyardArguments
exit $LASTEXITCODE
