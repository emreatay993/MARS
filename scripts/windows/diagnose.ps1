<#
.SYNOPSIS
Diagnose the packaged GUI without any installed Python or active environment.
.DESCRIPTION
Options: -PackageDir <folder> -TimeoutSeconds <seconds> -LogRoot <folder> -NoPause -Help.
Requires a matching ready report AND exit 0 from every configured startup executable.
If batchExecutable is configured, also require its --help command to exit 0.
The timeout applies separately to each executable; a live process/window is not success.
Logs default to %TEMP%\MARS-startup-logs so read-only copied packages are supported.
#>
$runArguments = @($args)
$noPause = (@($runArguments | Where-Object { $_ -in @('-NoPause', '--no-pause') }).Count -gt 0)
$result = 1
$transcribing = $false
$process = $null
$logDirectory = '(not created)'
$packageDirectory = $PSScriptRoot
$executable = '(not resolved)'
$evidenceNames = @('application.stdout.log', 'application.stderr.log', 'smoke-report.json')
try {
    $ErrorActionPreference = 'Stop'
    . (Join-Path $PSScriptRoot 'windows_common.ps1')
    # Establish fallback logs before parsing, including invalid arguments.
    $logDirectory = New-RunLogDirectory (Join-Path ([IO.Path]::GetTempPath()) 'MARS-startup-logs')
    $options = Read-RunOptions $runArguments @('nopause', 'help', 'h', '?') @('packagedir', 'timeoutseconds', 'logroot')
    if ($options.logroot) { $logDirectory = New-RunLogDirectory (Get-FullPath $options.logroot) }
    $null = Start-Transcript -LiteralPath (Join-Path $logDirectory 'diagnose.transcript.log')
    $transcribing = $true
    if ($options.packagedir) { $packageDirectory = Get-FullPath $options.packagedir }
    if ($options.help -or $options.h -or $options['?']) {
        Write-Host 'Usage: diagnose.ps1 [-PackageDir <folder>] [-TimeoutSeconds 90] [-LogRoot <folder>] [-NoPause] [-Help]'
        Write-Host 'Run diagnose.bat from a complete package. No Python installation or environment is needed.'
        $result = 0
    }
    else {
        $timeout = 90
        if ($options.timeoutseconds) { $timeout = [int]$options.timeoutseconds }
        if ($timeout -lt 1 -or $timeout -gt 600) { throw '-TimeoutSeconds must be between 1 and 600.' }
        Write-Host "[1/3] Package: $packageDirectory"
        $configuration = Get-Content -LiteralPath (Join-Path $packageDirectory 'package.json') -Raw | ConvertFrom-Json
        $startupExecutables = @($configuration.startupExecutables)
        if (-not $startupExecutables.Count -or [string]::IsNullOrWhiteSpace($startupExecutables[0])) {
            throw 'package.json must declare startupExecutables. Refresh the packaged diagnostic support files.'
        }
        foreach ($name in $startupExecutables) {
            if ([string]::IsNullOrWhiteSpace($name) -or [IO.Path]::GetFileName($name) -ne $name -or [IO.Path]::GetExtension($name) -ne '.exe') {
                throw "Invalid startup executable name: $name"
            }
        }
        if ($startupExecutables[0] -ne $configuration.diagnosticExecutable) { throw 'The console diagnostic must be first in startupExecutables.' }
        if (@($startupExecutables | ForEach-Object { $_.ToLowerInvariant() } | Select-Object -Unique).Count -ne $startupExecutables.Count) {
            throw 'startupExecutables must not contain duplicate executable names.'
        }
        $executable = Join-Path $packageDirectory $configuration.diagnosticExecutable
        Write-Host "Executable: $executable"
        $inventoryProblems = @()
        $inventoryFile = Join-Path $packageDirectory 'runtime-inventory.json'
        if (Test-Path -LiteralPath $inventoryFile) {
            $inventory = Get-Content -LiteralPath $inventoryFile -Raw | ConvertFrom-Json
            foreach ($entry in $inventory.files) {
                $path = Get-FullPath (Join-Path $packageDirectory $entry.path)
                if (-not (Test-PathWithin $path $packageDirectory)) { throw "Inventory path outside package: $path" }
                if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $inventoryProblems += "Missing: $path" }
                elseif ((Get-RuntimeHash $path) -ne $entry.sha256) { $inventoryProblems += "Hash mismatch: $path" }
            }
        }
        else { $inventoryProblems += "Missing runtime inventory: $inventoryFile" }
        foreach ($problem in $inventoryProblems) { Write-Host "[INVENTORY] $problem" }
        # Still launch on runtime corruption: bootloader stderr is the essential evidence.
        for ($index = 0; $index -lt $startupExecutables.Count; $index++) {
            $name = $startupExecutables[$index]
            $executable = Join-Path $packageDirectory $name
            $label = [IO.Path]::GetFileNameWithoutExtension($name)
            if ($index -eq 0) {
                $label = 'application'
                $reportName = 'smoke-report.json'
            }
            else {
                $reportName = "$label.smoke-report.json"
                $evidenceNames += @("$label.stdout.log", "$label.stderr.log", $reportName)
            }
            Write-Host "[2/3] Startup $($index + 1)/$($startupExecutables.Count): $executable (timeout ${timeout}s)."
            $reportPath = Join-Path $logDirectory $reportName
            $nativePrefix = Join-Path $logDirectory $label
            $process = Start-DiagnosticProcess $executable @('--smoke-test', '--smoke-report', $reportPath) $packageDirectory $nativePrefix
            $deadline = [DateTime]::UtcNow.AddSeconds($timeout)
            while (-not $process.WaitForExit(250)) {
                if ([DateTime]::UtcNow -ge $deadline) { throw "Startup timed out after $timeout seconds for $executable; no completed readiness acknowledgment." }
            }
            $nativeCode = $process.ExitCode
            if ($null -eq $nativeCode) { throw "Cannot determine application exit status: $executable" }
            Write-Host "Application exit code: $nativeCode ($executable)"
            if ($nativeCode -ne 0) {
                $errorObject = New-Object System.Exception("Application exited ${nativeCode}: $executable. See $nativePrefix.stderr.log and $reportPath.")
                $errorObject.Data['ExitCode'] = $nativeCode
                throw $errorObject
            }
            if (-not (Test-Path -LiteralPath $reportPath)) { throw "Application exited without a readiness report (possibly before Python started): $executable" }
            $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
            if ($report.protocol -ne 'mars-startup-v1' -or $report.status -ne 'ready' -or
                $report.phase -ne 'event-loop-complete' -or $report.pid -ne $process.Id -or
                -not (Get-FullPath $report.executable).Equals((Get-FullPath $executable), [StringComparison]::OrdinalIgnoreCase)) {
                throw "Application did not acknowledge completed GUI/controller/event-loop startup for this process: $executable"
            }
            # Dispose this launch's job before moving on to the next executable.
            $process.Dispose()
            $process = $null
            Write-Host "Startup acknowledged: $executable"
        }
        if ($configuration.batchExecutable) {
            $name = $configuration.batchExecutable
            if ([IO.Path]::GetFileName($name) -ne $name -or [IO.Path]::GetExtension($name) -ne '.exe') {
                throw "Invalid batch executable name: $name"
            }
            $executable = Join-Path $packageDirectory $name
            $nativePrefix = Join-Path $logDirectory 'batch-help'
            $evidenceNames += @('batch-help.stdout.log', 'batch-help.stderr.log')
            Write-Host "[2/3] Batch CLI help: $executable --help (timeout ${timeout}s)."
            $process = Start-DiagnosticProcess $executable @('--help') $packageDirectory $nativePrefix
            if (-not $process.WaitForExit($timeout * 1000)) { throw "Batch --help timed out after $timeout seconds: $executable" }
            $nativeCode = $process.ExitCode
            if ($nativeCode -ne 0) {
                $errorObject = New-Object System.Exception("Batch --help exited ${nativeCode}: $executable. See $nativePrefix.stderr.log.")
                $errorObject.Data['ExitCode'] = $nativeCode
                throw $errorObject
            }
            $process.Dispose()
            $process = $null
            Write-Host "Batch --help passed: $executable"
        }
        if ($inventoryProblems.Count) { throw 'Startup completed but runtime inventory validation failed.' }
        Write-Host '[3/3] PASS: every startup executable initialized its GUI, ran the event loop, acknowledged readiness, and exited 0.'
        $result = 0
    }
}
catch {
    Write-Host "[FAILED] $($_.Exception.Message)"
    if ($_.Exception.Data.Contains('ExitCode')) { $result = [int]$_.Exception.Data['ExitCode'] }
    if ($logDirectory -ne '(not created)') { $_ | Out-String | Out-File -LiteralPath (Join-Path $logDirectory 'runner-error.log') -Encoding utf8 }
}
finally {
    if ($process) {
        try {
            if (-not $process.HasExited) {
                Write-Host "Requesting closure of launched PID $($process.Id)."
                $null = $process.CloseMainWindow()
                if (-not $process.WaitForExit(2000)) { $process.Kill(); $null = $process.WaitForExit(2000) }
            }
        }
        catch { Write-Host "Process cleanup: $($_.Exception.Message)"; $result = 1 }
        finally { $process.Dispose() }
    }
    foreach ($name in $evidenceNames) {
        $path = Join-Path $logDirectory $name
        Write-Host "Evidence: $path"
        if (Test-Path -LiteralPath $path) { Get-Content -LiteralPath $path | ForEach-Object { Write-Host $_ } }
    }
    Write-Host "Result: $result"
    Write-Host "Package: $packageDirectory"
    Write-Host "Executable: $executable"
    Write-Host "Logs: $logDirectory"
    if ($transcribing) { try { $null = Stop-Transcript } catch { Write-Host $_.Exception.Message } }
    if (Get-Command Wait-RunPrompt -ErrorAction SilentlyContinue) { Wait-RunPrompt $noPause }
    elseif (-not $noPause) { try { $null = Read-Host 'Press Enter to close' } catch { Write-Host $_.Exception.Message } }
}
exit $result
