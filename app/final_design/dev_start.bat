@echo off
setlocal enabledelayedexpansion
REM Pelta AI - Development Startup Script
REM Starts Flask + ngrok and updates app_config.dart automatically

cd /d "%~dp0"

echo ========================================
echo  Pelta AI - Dev Server Startup
echo ========================================
echo.

echo [1/4] Starting Flask server...
start "Flask Server" cmd /k "python app.py"

echo [2/4] Waiting for Flask to start...
timeout /t 3 >nul

echo [3/4] Starting ngrok tunnel...
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: ngrok not found in PATH.
    echo Install ngrok: winget install ngrok
    echo Then restart your terminal and try again.
    pause
    exit /b 1
)
start "ngrok" ngrok http 5000

echo [4/4] Waiting for ngrok to initialize...
timeout /t 6 >nul

REM Get ngrok URL from API
echo.
echo Fetching ngrok URL from ngrok API...

REM Try multiple times to get the URL
set NGROK_URL=
for /L %%i in (1,1,5) do (
    if "!NGROK_URL!"=="" (
        for /f "delims=" %%j in ('powershell -Command "try { (Invoke-WebRequest -Uri http://127.0.0.1:4040/api/tunnels -UseBasicParsing -ErrorAction Stop | ConvertFrom-Json).tunnels[0].public_url } catch { '' }"') do set NGROK_URL=%%j
        if "!NGROK_URL!"=="" (
            echo Attempt %%i: Waiting for ngrok...
            timeout /t 2 >nul
        )
    )
)

if "!NGROK_URL!"=="" (
    echo.
    echo ERROR: Could not detect ngrok URL automatically.
    echo.
    echo Please check the ngrok window for the URL and update manually:
    echo   1. Look for "Forwarding" line in ngrok window
    echo   2. Copy the https://xxx.ngrok-free.app URL
    echo   3. Edit lib\utils\app_config.dart line 63
    echo   4. Replace the URL in _devBackendUrl
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  ngrok URL: !NGROK_URL!
echo ========================================
echo.

REM Update app_config.dart using PowerShell for reliable replacement
echo Updating app_config.dart with ngrok URL...
powershell -Command "$content = Get-Content 'lib\utils\app_config.dart' -Raw; $content = $content -replace 'static const String _devBackendUrl = \"[^\"]*\";', 'static const String _devBackendUrl = \"!NGROK_URL!\";'; Set-Content 'lib\utils\app_config.dart' $content -NoNewline"

echo.
echo ========================================
echo  SUCCESS! Backend is ready.
echo ========================================
echo.
echo Next steps:
echo   1. Hot restart your Flutter app (press R in terminal)
echo   2. Or run: flutter run
echo.
pause
