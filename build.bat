@echo off
REM ============================================================================
REM MARS Build Script for Windows
REM Creates a portable executable that works on different Windows PCs
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   MARS - Modal Analysis Response Solver - Build Script
echo ============================================================
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH. Please install Python 3.10+ and try again.
    exit /b 1
)

REM Get Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [INFO] Found: %PYVER%

REM Check for virtual environment
if not defined VIRTUAL_ENV (
    echo [INFO] No virtual environment active.
    if exist "venv\Scripts\activate.bat" (
        echo [INFO] Activating existing virtual environment...
        call venv\Scripts\activate.bat
    ) else (
        echo [INFO] Creating new virtual environment...
        python -m venv venv
        call venv\Scripts\activate.bat
    )
)
echo [INFO] Virtual environment: %VIRTUAL_ENV%
echo.

REM Parse command line arguments
set CUDA_BUILD=0
set CLEAN_BUILD=0
set SKIP_DEPS=0

:parse_args
if "%~1"=="" goto :done_parsing
if /i "%~1"=="--cuda" set CUDA_BUILD=1
if /i "%~1"=="--clean" set CLEAN_BUILD=1
if /i "%~1"=="--skip-deps" set SKIP_DEPS=1
if /i "%~1"=="--help" goto :show_help
shift
goto :parse_args
:done_parsing

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
    
    if %CUDA_BUILD%==1 (
        echo [INFO] Installing with CUDA support...
        pip install -r requirements-portable.txt --extra-index-url https://download.pytorch.org/whl/cu126
    ) else (
        echo [INFO] Installing CPU-only version...
        pip install -r requirements-portable.txt
    )
    
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies.
        exit /b 1
    )
    echo.
    echo [INFO] Dependencies installed successfully.
    echo.
)

REM Verify torch installation
echo [INFO] Verifying PyTorch installation...
python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyTorch verification failed.
    exit /b 1
)
echo.

REM Build with PyInstaller
echo [INFO] Building executable with PyInstaller...
echo.
pyinstaller MARS.spec --noconfirm
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD COMPLETE
echo ============================================================
echo.
echo Output directory: dist\MARS\
echo Executable: dist\MARS\MARS.exe
echo.
echo To test the build:
echo   cd dist\MARS
echo   MARS.exe
echo.

goto :eof

:show_help
echo.
echo Usage: build.bat [options]
echo.
echo Options:
echo   --cuda       Build with CUDA support (requires NVIDIA GPU)
echo   --clean      Clean previous build directories before building
echo   --skip-deps  Skip dependency installation (use existing packages)
echo   --help       Show this help message
echo.
echo Examples:
echo   build.bat                    # CPU-only build
echo   build.bat --cuda             # CUDA-enabled build
echo   build.bat --clean --cuda     # Clean CUDA build
echo.
goto :eof

