@echo off
setlocal

echo.

:: Check if python3 or python is available
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON=python3"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON=python"
    ) else (
        echo Could not find python or python3. Please make sure they are installed.
        exit /b 1
    )
)

:: Check if pip3 or pip is available
where pip3 >nul 2>&1
if %errorlevel% equ 0 (
    set "PIP=pip3"
) else (
    where pip >nul 2>&1
    if %errorlevel% equ 0 (
        set "PIP=pip"
    ) else (
        echo Could not find pip or pip3. Please make sure they are installed.
        exit /b 1
    )
)

:: Load configuration from .env file if it exists
set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%.env" (
    for /f "usebackq tokens=*" %%i in ("%SCRIPT_DIR%.env") do (
        set "line=%%i"
        if not "!line!"=="" (
            if "!line:~0,1!" neq "#" set "%line%"
        )
    )
)

cd /d "%SCRIPT_DIR%"

:: Set proxy for pip if PROXY_ADDRESS is not empty
if not "%PROXY_ADDRESS%"=="" (
    set "PIP_PROXY=--proxy %PROXY_ADDRESS%"
    set "HTTP_PROXY=%PROXY_ADDRESS%"
    set "HTTPS_PROXY=%PROXY_ADDRESS%"
) else (
    set "PIP_PROXY="
)

:: Check if virtual environment directory exists
if not exist "venv" (
    echo Creating virtual environment
    %PYTHON% -m venv venv

    call venv\Scripts\activate

    echo Installing dependencies
    %PIP% install %PIP_PROXY% -r requirements.txt --upgrade
) else (
    echo Activating virtual environment
    call venv\Scripts\activate

    :: Check if "--upgrade" is passed in the arguments
    echo %* | findstr /i "--upgrade" >nul
    if not errorlevel 1 (
        echo Upgrading dependencies...
        %PIP% install %PIP_PROXY% --upgrade -r requirements.txt
        echo Upgraded dependencies. Please restart the application.
        exit /b 0
    )
)

:: Run the Python application
%PYTHON% app.py %*

endlocal
