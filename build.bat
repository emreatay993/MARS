@echo off
REM ============================================================================
REM MARS Build Script for Windows
REM Creates a portable executable that works on different Windows PCs
REM ============================================================================
setlocal enabledelayedexpansion

REM Parse command line arguments before touching Python so --help always works.
set CLEAN_BUILD=0
set SKIP_DEPS=0

:parse_args
if "%~1"=="" goto :done_parsing
if /i "%~1"=="--clean" set CLEAN_BUILD=1
if /i "%~1"=="--skip-deps" set SKIP_DEPS=1
if /i "%~1"=="--help" goto :show_help
shift
goto :parse_args
:done_parsing

echo.
echo ============================================================
echo   MARS - Modal Analysis Response Solver - Build Script
echo ============================================================
echo.

REM Keep release dependencies separate from the developer's normal venv.
if not exist "build_venv\Scripts\python.exe" (
    echo [INFO] Creating dedicated Python 3.12 build environment...
    where py >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Python Launcher not found. Install 64-bit Python 3.12.
        exit /b 1
    )
    py -3.12 -m venv build_venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Could not create the Python 3.12 build environment.
        exit /b 1
    )
)
call build_venv\Scripts\activate.bat

REM MARS release builds use exactly Python 3.12.
python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] build_venv is not Python 3.12.
    echo [ERROR] Remove build_venv and rerun this script.
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [INFO] Found: %PYVER%
echo [INFO] Virtual environment: %VIRTUAL_ENV%
echo.

REM Clean previous builds if requested
if %CLEAN_BUILD%==1 (
    echo [INFO] Cleaning previous builds...
    if exist "build" rmdir /s /q "build"
    if exist "dist" rmdir /s /q "dist"
    echo [INFO] Clean complete.
    echo.
)

REM Install/update dependencies
if %SKIP_DEPS%==0 (
    echo [INFO] Installing/updating dependencies...
    echo.
    
    REM Upgrade pip first
    python -m pip install --upgrade pip
    
    echo [INFO] Installing dependencies...
    python -m pip install -r requirements-portable.txt
    
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies.
        exit /b 1
    )
    echo.
    echo [INFO] Dependencies installed successfully.
    echo.
)

REM Build with PyInstaller
echo [INFO] Building executable with PyInstaller...
echo.
python -m PyInstaller MARS.spec --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

if not exist "dist\MARS\MARS.exe" (
    echo [ERROR] Windowed launcher was not created: dist\MARS\MARS.exe
    exit /b 1
)
if not exist "dist\MARS\MARSBatch.exe" (
    echo [ERROR] Batch launcher was not created: dist\MARS\MARSBatch.exe
    exit /b 1
)

echo [INFO] Verifying the packaged batch launcher...
dist\MARS\MARSBatch.exe --help >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] MARSBatch.exe failed its help smoke test.
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD COMPLETE
echo ============================================================
echo.
echo Output directory: dist\MARS\
echo GUI executable: dist\MARS\MARS.exe
echo Batch executable: dist\MARS\MARSBatch.exe
echo.
echo To test the build:
echo   cd dist\MARS
echo   MARS.exe
echo   MARSBatch.exe --help
echo.

goto :eof

:show_help
echo.
echo Usage: build.bat [options]
echo.
echo Options:
echo   --clean      Clean previous build directories before building
echo   --skip-deps  Skip dependency installation (use existing packages)
echo   --help       Show this help message
echo.
echo Examples:
echo   build.bat                    # Build with default settings
echo   build.bat --clean            # Clean build
echo.
goto :eof

