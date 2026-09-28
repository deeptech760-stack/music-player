@echo off
REM Build script for MusicPlayer Windows package
REM Usage: build_windows.bat [clean]

cd /d "%~dp0"

echo ============================================
echo MusicPlayer Windows Build Script
echo ============================================

REM Check for PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Check for VLC
if not exist "C:\Program Files\VideoLAN\VLC\libvlc.dll" (
    echo WARNING: VLC not found at C:\Program Files\VideoLAN\VLC\
    echo The packaged application may not play audio without VLC DLLs.
    echo Please install VLC media player (64-bit) from https://www.videolan.org/vlc/
)

REM Clean if requested
if "%1"=="clean" (
    echo Cleaning previous builds...
    rmdir /s /q build 2>nul
    rmdir /s /q dist 2>nul
    del /q *.spec 2>nul
)

echo Building MusicPlayer...
python -m PyInstaller MusicPlayer.spec --clean

if errorlevel 1 (
    echo BUILD FAILED
    exit /b 1
)

echo.
echo ============================================
echo BUILD SUCCESSFUL
echo ============================================
echo.
echo Packaged application location:
echo   %~dp0\dist\MusicPlayer\MusicPlayer.exe
echo.
echo To create desktop shortcut, run:
echo   python create_shortcut.py
echo.
echo To test the application:
echo   %~dp0\dist\MusicPlayer\MusicPlayer.exe
echo.

pause