"""The small updater that runs after Aperture quits: swap, start, keep or roll back.

The running app cannot replace itself (Windows locks its files; on Linux it would be
replacing what is executing), so it writes one of these scripts, starts it detached, and
quits. The script keeps the previous version until the new one reports a successful start
by creating the marker file; if that does not happen in time it puts the old one back.

Linux AppImage updates replace the file at its existing path, so menu entries and the
default-player association, which point at that path, keep working.
"""

from __future__ import annotations

# sh updater.sh PID NEW TARGET KIND MARKER [TIMEOUT_SECONDS]
POSIX_UPDATER = r"""#!/bin/sh
# Aperture updater. Started by the app just before it quits.
pid=$1 new=$2 target=$3 kind=$4 marker=$5 timeout=${6:-30}
backup="$target.previous"

while kill -0 "$pid" 2>/dev/null; do sleep 0.2; done

start() {
    if [ "$kind" = appimage ]; then
        "$target" >/dev/null 2>&1 &
    else
        "$target/aperture" >/dev/null 2>&1 &
    fi
    echo $!
}

rm -rf "$backup"
if [ "$kind" = appimage ]; then
    cp -p "$target" "$backup" || { echo "cannot back up $target"; exit 1; }
    chmod +x "$new" && mv -f "$new" "$target" || { echo "swap failed"; exit 1; }
else
    mv "$target" "$backup" || { echo "cannot back up $target"; exit 1; }
    if ! mv "$new" "$target"; then
        mv "$backup" "$target"
        echo "swap failed"
        exit 1
    fi
fi

rm -f "$marker"
child=$(start)
ticks=0
while [ "$ticks" -lt $((timeout * 5)) ]; do
    if [ -e "$marker" ]; then
        rm -rf "$backup"
        echo "updated"
        exit 0
    fi
    sleep 0.2
    ticks=$((ticks + 1))
done

echo "the new version did not start; restoring the previous one"
kill "$child" 2>/dev/null
if [ "$kind" = appimage ]; then
    mv -f "$backup" "$target"
else
    rm -rf "$target" && mv "$backup" "$target"
fi
start >/dev/null
exit 1
"""

# powershell -File updater.ps1 -AppPid N -Installer setup.exe -AppDir DIR -Marker FILE
WINDOWS_UPDATER = r"""param(
    [int]$AppPid, [string]$Installer, [string]$AppDir, [string]$Marker, [int]$Timeout = 30
)
# Aperture updater. Started by the app just before it quits.
$exe = Join-Path $AppDir 'aperture.exe'
$backup = Join-Path $env:LOCALAPPDATA 'Aperture\previous'

Wait-Process -Id $AppPid -ErrorAction SilentlyContinue

# Keep the installed version until the new one has started once.
if (Test-Path $backup) { Remove-Item $backup -Recurse -Force }
robocopy $AppDir $backup /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Output "cannot back up $AppDir"; Start-Process $exe; exit 1 }

# Same install scope as before: an all-users install needs /ALLUSERS (and asks for admin).
$scope = if ($AppDir -like "$env:ProgramFiles*") { '/ALLUSERS' } else { '/CURRENTUSER' }
Remove-Item $Marker -ErrorAction SilentlyContinue
$arguments = '/SILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CLOSEAPPLICATIONS', $scope
$setup = Start-Process -FilePath $Installer -ArgumentList $arguments -Wait -PassThru
if ($setup.ExitCode -ne 0) {
    Write-Output "installer failed with $($setup.ExitCode)"
    Start-Process $exe
    exit 1
}

$app = Start-Process -FilePath $exe -PassThru
$deadline = (Get-Date).AddSeconds($Timeout)
while ((Get-Date) -lt $deadline) {
    if (Test-Path $Marker) {
        Remove-Item $backup -Recurse -Force
        Remove-Item $Installer -Force -ErrorAction SilentlyContinue
        Write-Output 'updated'
        exit 0
    }
    Start-Sleep -Milliseconds 200
}

Write-Output 'the new version did not start; restoring the previous one'
Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
robocopy $backup $AppDir /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
Start-Process $exe
exit 1
"""
