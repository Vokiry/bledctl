@echo off
:: bledctl Windows Installer
:: Run as: install.bat

setlocal

set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%USERPROFILE%\.local\bin"
set "PKG_DIR=%APPDATA%\Python\Python314\site-packages"

echo Installing bledctl...

:: Create directories
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%PKG_DIR%" mkdir "%PKG_DIR%"

:: Remove old package if exists
if exist "%PKG_DIR%\bledctl" rmdir /S /Q "%PKG_DIR%\bledctl"

:: Copy package files
xcopy /E /Y "%SCRIPT_DIR%bledctl" "%PKG_DIR%\" > nul

:: Create wrapper script
(
echo @echo off
echo python -m bledctl %%*
) > "%INSTALL_DIR%\bledctl.bat"

:: Add to PATH if not already present
set "PATH_ADDED=0"
reg query "HKCU\Environment" /v PATH 2>nul | findstr /C:".local" > nul
if errorlevel 1 (
    setx PATH "%PATH%;%INSTALL_DIR%" > nul
    set "PATH_ADDED=1"
)

echo.
echo bledctl installed to %INSTALL_DIR%\bledctl.bat
if "%PATH_ADDED%"=="1" echo Added %INSTALL_DIR% to PATH.
echo.
echo Make sure Python is in your PATH.
echo Run 'bledctl --help' to start.
echo.
pause
