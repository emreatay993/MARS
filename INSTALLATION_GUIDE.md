# MARS: Windows installation and builds with Python 3.12

Use an activated **64-bit Python 3.12** environment. Its name and location are
your choice; the build uses the `python.exe` selected in the current terminal.
It prints and validates that interpreter before installing dependencies.

## Script and guide locations

- `INSTALLATION_GUIDE.md`: this guide.
- `build.ps1`: the build/test entry point at the repository root.
- `build.bat`: the compatible batch entry point.
- `scripts\windows\diagnose.ps1`: startup diagnostic source.
- `dist\MARS\diagnose.bat`: diagnostic launcher delivered with the package.

## 1. Get the repository

Clone the branch used for these builds, or download and extract that branch:

```powershell
git clone --branch main --single-branch https://github.com/emreatay993/MARS.git MARS_
Set-Location .\MARS_
```

An existing checkout only needs to be opened in PowerShell at its repository
root. PyCharm is optional; its terminal works too.

## 2. Activate your chosen environment

If you already have a Python 3.12 environment, find its actual folder and run
its activation script in this terminal. Replace the example path:

```powershell
& 'C:\PythonEnvironments\my release environment\Scripts\Activate.ps1'
python -c "import sys, struct; print(sys.executable); print(sys.version); print(struct.calcsize('P') * 8, 'bit')"
```

The output must show the Python executable in your chosen environment,
Python `3.12.x`, and `64 bit`. Keep this terminal open for the build.
Selecting an interpreter in PyCharm alone does not activate it in every terminal.

If you need a new environment, first install 64-bit Python 3.12 with the Windows
`py` launcher, then create and activate one. This example keeps it outside the
repository:

```powershell
$ReleaseEnv = Join-Path $env:USERPROFILE 'PythonEnvironments\MARS_-release-312'
py -3.12 -m venv "$ReleaseEnv"
& "$ReleaseEnv\Scripts\Activate.ps1"
python --version
```

Do not recreate an existing environment containing work you need. The build
refuses absent, mismatched, or non-3.12 environments; it does not choose one by
folder name. Activation persists when you change back to the repository root.

## 3. Build and test the executables

From the repository root, in the same activated terminal:

```powershell
.\build.ps1 -Clean
```

The script prints each stage, installs `requirements-portable.txt` and the required build
tools into the active environment, runs PyInstaller, and smoke-tests the
resulting package. It reports the full package and executable paths, the log
folder, and the result. It waits for **Enter** before returning, on success or
failure.

To reuse already installed dependencies:

```powershell
.\build.ps1 -Clean -SkipDeps
```

Use `-NoPause` only for automation. A nonzero exit code means the build or
startup test failed. `-Clean` removes only `build\pyinstaller-<application>`.
Every full build replaces `dist\<application>`, including builds without
`-Clean`. Keep valuable files outside that application output folder.

The existing batch entry point remains available, using the same activated
environment:

```powershell
.\build.bat --clean
```

It accepts `--skip-deps`, `--no-pause`, `--smoke-only`, and `--help`.
Double-clicking a build script without an activated environment will not select
your Python environment automatically.

## 4. Run or distribute the package

The application is created at:

```text
dist\MARS\MARS.exe
```

The folder also contains `MARSBatch.exe` for headless jobs and
`MARSDiagnostics.exe` for capturing GUI startup and bootloader errors.

Run the application:

```powershell
.\dist\MARS\MARS.exe
```

Copy or zip the **entire** `dist\MARS` folder, including `_internal` and the
diagnostic files. Extract the whole archive on the destination machine before
running it. Python and the build environment are not required on that machine.
Ansys result-file workflows still require the appropriate licensed Ansys/DPF
runtime there.

## 5. Diagnose an executable that does not open

Retest the current package without rebuilding or activating Python:

```powershell
.\build.ps1 -SmokeOnly
```

To test a copy in another folder:

```powershell
.\build.ps1 -SmokeOnly -PackageDir 'C:\Apps\MARS'
```

On the destination computer, double-click `diagnose.bat` inside the extracted
application folder. It keeps the command window open until you press Enter and
prints the full log location. No Python environment is needed. From PowerShell:

```powershell
& 'C:\Apps\MARS\diagnose.ps1'
```

Build logs live under `build\logs\<unique run>\` in the repository. Standalone
diagnostic logs default to `%TEMP%\MARS-startup-logs\<unique run>\`, which also
works when the application folder is read-only. Each run keeps:

- The build or diagnostic transcript and the native command exit codes.
- `application.stdout.log` and `application.stderr.log` for console output,
  including errors before Python starts.
- `smoke-report.json` when Python reaches the startup test, recording its phase,
  exception/traceback on failure, or GUI readiness on success.

MARS additionally checks the real windowed `MARS.exe`, saving `MARS.stdout.log`,
`MARS.stderr.log`, and `MARS.smoke-report.json`. It then runs `MARSBatch.exe --help`
and saves `batch-help.stdout.log` and `batch-help.stderr.log`. All three launchers
must pass before the overall result is successful.

If no smoke report exists, read the stderr log: Python may have failed before
it could write a report. Send the complete printed run-log folder with an error
report. Logs may contain local paths; review them before sharing publicly.

For a slow machine, the diagnostic runner accepts a longer timeout (up to
600 seconds); its default is 90 seconds:

```powershell
& 'C:\Apps\MARS\diagnose.ps1' -TimeoutSeconds 180
```

The smoke test requires the application to acknowledge GUI initialization and
exit successfully. A process that merely stays alive, hangs, or displays an
error dialog does not pass. Logs distinguish startup failures, Python
exceptions, and timeouts. This checks startup, not every solver or result-file
workflow; exercise those with your own inputs before distributing a release.

The message **Failed to start embedded python interpreter!** occurs before the
application can handle Python exceptions. A missing or damaged
`_internal\base_library.zip` is one possible cause, not a diagnosis from the
popup alone. The console diagnostic captures the underlying bootloader/Python
message. Recopy a complete matching package if files are missing; do not mix
executables and `_internal` folders from different builds. See
[PyInstaller startup troubleshooting](https://pyinstaller.org/en/stable/when-things-go-wrong.html).

## Optional: run from source

With your chosen environment still active:

```powershell
python -m pip install -r .\requirements-portable.txt
python .\src\main.py
```

## Troubleshooting setup

- **Wrong interpreter:** reactivate the intended environment and check
  `python -c "import sys; print(sys.executable)"`. An old terminal can retain a
  different environment.
- **Scripts blocked by policy:** follow your organization's script-signing or
  execution-policy requirements. These scripts do not bypass policy. Run from
  an already open terminal to retain the error if PowerShell refuses to start.
- **Package-index connection errors:** use `python -m pip config debug` in the
  active environment and check the configured indexes/network. A failed
  dependency-install stage must be resolved before building.
- **Optional PyInstaller warnings:** read the full build log and the smoke-test
  result. A passing startup check does not validate an optional feature you
  have not exercised.
