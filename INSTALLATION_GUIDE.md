# MARS Installation Guide (Python 3.12)

This guide installs MARS from source and builds the Windows executable package
with 64-bit Python 3.12. Run the commands from PowerShell in the repository
root.

## Important locations

- Installation guide: `INSTALLATION_GUIDE.md`
- Executable build script: `build.bat`
- PyInstaller definition: `MARS.spec`
- GUI source entry point: `src\main.py`
- Build verification script: `verify_build.py`
- Packaged GUI: `dist\MARS\MARS.exe`
- Packaged batch runner: `dist\MARS\MARSBatch.exe`

## Requirements

- 64-bit Windows 10 or Windows 11
- 64-bit Python 3.12 with the Windows `py` launcher
- Git, if cloning instead of downloading a source archive
- A compatible licensed Ansys DPF server/runtime for direct `.rst` loading
  (CSV workflows do not require it)

## 1. Get the source

Clone the `main` branch:

```powershell
git clone --branch main --single-branch https://github.com/emreatay993/MARS.git MARS_
Set-Location .\MARS_
```

If you downloaded an archive, extract it and use `Set-Location` to enter the
folder containing `build.bat` and `MARS.spec`.

## 2. Verify Python 3.12

```powershell
py -3.12 -c "import struct, sys; print(sys.version); print(struct.calcsize('P') * 8, 'bit')"
```

The output must report Python `3.12.x` and `64 bit`. If `py -3.12` is not found,
install the 64-bit Python 3.12 release from python.org and enable the Python
launcher during installation.

## 3. Install and run from source

Create a project environment without changing PowerShell's execution policy:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

Launch the GUI:

```powershell
.\.venv\Scripts\python.exe .\src\main.py
```

The virtual environment does not need to be activated because these commands
call its Python executable directly.

## 4. Build the Windows executables

The checked-in wrapper creates and uses a separate `build_venv` environment. It
requires Python 3.12, installs `requirements-portable.txt`, and invokes the root
`MARS.spec` file.

Run a clean release build:

```powershell
.\build.bat --clean
```

For a repeat build after the build environment is already prepared:

```powershell
.\build.bat --clean --skip-deps
```

A successful build creates the complete application folder at `dist\MARS`.

## 5. Verify the package

Check the console launcher and run the repository's packaged-build verifier:

```powershell
.\dist\MARS\MARSBatch.exe --help
.\build_venv\Scripts\python.exe .\verify_build.py --package-dir .\dist\MARS
```

Then launch the GUI:

```powershell
.\dist\MARS\MARS.exe
```

The verifier should finish with `All critical checks passed!`.

## 6. Distribute MARS

Distribute the entire `dist\MARS` folder. Do not copy only `MARS.exe` or
`MARSBatch.exe`; both launchers require the accompanying `_internal` files and
libraries.

On another Windows machine, extract the folder and run `MARS.exe`. Python does
not need to be installed on the target machine. Direct `.rst` loading still
requires a compatible licensed Ansys DPF server/runtime on that machine.

## Troubleshooting

### The wrong Python version is reported

Confirm the launcher can find Python 3.12:

```powershell
py -0p
py -3.12 --version
```

The build wrapper deliberately stops if its generated `build_venv` is not based
on Python 3.12.

### Dependency installation cannot reach a configured package index

Inspect active pip configuration:

```powershell
py -3.12 -m pip config debug
```

Remove or correct an unavailable organization-specific index, or run the build
from a network that can reach it.

### PyInstaller prints optional-module warnings

Use the build exit code, the expected files under `dist\MARS`, the verification
script, and a real GUI launch as the acceptance checks. Review a warning further
if one of those checks fails or the affected optional feature is required.
