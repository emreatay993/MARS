<#
.SYNOPSIS
Build with the manually activated Python 3.12 x64 environment, or diagnose a package.
.DESCRIPTION
Options: -Clean -SkipDeps -NoPause -SmokeOnly -PackageDir <folder> -Help.
No activation, environment creation, or execution-policy changes are performed.
-Clean removes only build\pyinstaller-<application>. Other build/dist entries are preserved.
Every build uses a fresh work/cache directory and PyInstaller --clean.
-SmokeOnly needs no Python. -PackageDir is valid only with -SmokeOnly.
.EXAMPLE
.\build.ps1 -SkipDeps -NoPause
.EXAMPLE
.\build.ps1 -SmokeOnly -PackageDir 'D:\Copied packages\MARS' -NoPause
#>
$runArguments = @($args)
$noPause = (@($runArguments | Where-Object { $_ -in @('-NoPause', '--no-pause') }).Count -gt 0)
$result = 1
$transcribing = $false
$logDirectory = '(not created)'
$packageDirectory = '(not resolved)'
$configuration = $null
$oldCache = $env:PYINSTALLER_CONFIG_DIR
try {
    $ErrorActionPreference = 'Stop'
    . (Join-Path $PSScriptRoot 'scripts\windows\windows_common.ps1')
    $configuration = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'scripts\windows\package.json') -Raw | ConvertFrom-Json
    $packageDirectory = Join-Path $PSScriptRoot "dist\$($configuration.name)"
    $logDirectory = New-RunLogDirectory (Join-Path $PSScriptRoot 'build\logs')
    $null = Start-Transcript -LiteralPath (Join-Path $logDirectory 'build.transcript.log')
    $transcribing = $true
    Write-Host "[1/5] Build options. Logs: $logDirectory"
    $options = Read-RunOptions $runArguments @('clean', 'skipdeps', 'nopause', 'smokeonly', 'help', 'h', '?') @('packagedir')
    if ($options.help -or $options.h -or $options['?']) {
        Write-Host 'Usage: build.ps1 [-Clean] [-SkipDeps] [-NoPause] [-SmokeOnly [-PackageDir <folder>]] [-Help]'
        Write-Host 'Activate ANY Python 3.12 x64 environment manually before building. SmokeOnly needs no Python.'
        Write-Host 'Clean removes only build\pyinstaller-<application>; the application package is replaced by a fresh build.'
        Write-Host 'build.bat also accepts --clean --skip-deps --no-pause --smoke-only --package-dir <folder> --help.'
        $result = 0
    }
    else {
        if ($options.packagedir -and -not $options.smokeonly) { throw '-PackageDir requires -SmokeOnly.' }
        if ($options.smokeonly -and ($options.clean -or $options.skipdeps)) { throw '-SmokeOnly cannot be combined with -Clean or -SkipDeps.' }
        if ($options.packagedir) { $packageDirectory = Get-FullPath $options.packagedir }
        if (-not $options.smokeonly) {
            Write-Host '[2/5] Validating active interpreter before dependency writes or cleanup.'
            $python = Get-ActiveBuildPython $PSScriptRoot $logDirectory
            $workRoot = Join-Path $PSScriptRoot "build\pyinstaller-$($configuration.name)"
            Assert-BuildTarget $workRoot (Join-Path $PSScriptRoot "build\pyinstaller-$($configuration.name)") $python.prefix
            Assert-BuildTarget $packageDirectory (Join-Path $PSScriptRoot "dist\$($configuration.name)") $python.prefix
            if ($options.clean -and (Test-Path -LiteralPath $workRoot)) {
                Write-Host "Removing PyInstaller work/cache only: $workRoot"
                Remove-Item -LiteralPath $workRoot -Recurse -Force
            }
            $workDirectory = New-RunLogDirectory $workRoot
            $env:PYINSTALLER_CONFIG_DIR = Join-Path $workDirectory 'cache'
            Write-Host '[3/5] Dependencies.'
            if (-not $options.skipdeps) {
                Invoke-LoggedProcess $python.executable @('-m', 'pip', 'install', '-r', (Join-Path $PSScriptRoot $configuration.requirements)) $PSScriptRoot (Join-Path $logDirectory 'dependencies')
                if ($configuration.installPyInstaller) {
                    Invoke-LoggedProcess $python.executable @('-m', 'pip', 'install', 'pyinstaller') $PSScriptRoot (Join-Path $logDirectory 'pyinstaller-install')
                }
            }
            else { Write-Host 'Dependency installation skipped.' }
            Invoke-LoggedProcess $python.executable @('-c', 'import PyInstaller; print(PyInstaller.__version__)') $PSScriptRoot (Join-Path $logDirectory 'pyinstaller-version')
            Write-Host "[4/5] Packaging. Work: $workDirectory"
            # Recheck immediately before PyInstaller replaces its COLLECT directory.
            Assert-BuildTarget $packageDirectory (Join-Path $PSScriptRoot "dist\$($configuration.name)") $python.prefix
            Invoke-LoggedProcess $python.executable @('-m', 'PyInstaller', '--clean', '--noconfirm', '--workpath', $workDirectory, '--distpath', (Join-Path $PSScriptRoot 'dist'), (Join-Path $PSScriptRoot $configuration.spec)) $PSScriptRoot (Join-Path $logDirectory 'pyinstaller')
        }
        Write-Host '[5/5] Packaged GUI startup acknowledgment.'
        $shell = (Get-Process -Id $PID).Path
        Invoke-LoggedProcess $shell @('-NoProfile', '-File', (Join-Path $PSScriptRoot 'scripts\windows\diagnose.ps1'), '-PackageDir', $packageDirectory, '-LogRoot', $logDirectory, '-NoPause') $PSScriptRoot (Join-Path $logDirectory 'diagnose-runner')
        $result = 0
    }
}
catch {
    Write-Host "[FAILED] $($_.Exception.Message)"
    if ($_.Exception.Data.Contains('ExitCode')) { $result = [int]$_.Exception.Data['ExitCode'] }
}
finally {
    $env:PYINSTALLER_CONFIG_DIR = $oldCache
    Write-Host "Result: $result"
    Write-Host "Package: $packageDirectory"
    if ($configuration) { foreach ($name in $configuration.executables) { Write-Host "Executable: $(Join-Path $packageDirectory $name)" } }
    Write-Host "Logs: $logDirectory"
    if ($transcribing) { try { $null = Stop-Transcript } catch { Write-Host $_.Exception.Message } }
    if (Get-Command Wait-RunPrompt -ErrorAction SilentlyContinue) { Wait-RunPrompt $noPause }
    elseif (-not $noPause) { try { $null = Read-Host 'Press Enter to close' } catch { Write-Host $_.Exception.Message } }
}
exit $result
