@echo off
REM Change to your project directory
cd /d C:\Data\Anish\Github\feline_skin_disease_detection\app\final_design

echo Starting Flask server...
start cmd /k "python app.py"

echo Waiting for Flask to start...
timeout /t 3 >nul

echo Starting ngrok tunnel on port 5000...
start "" ngrok http 5000 > ngrok.log

REM Wait a bit for ngrok to start
timeout /t 5 >nul

REM Read the ngrok log and extract the HTTPS forwarding URL
for /f "tokens=2 delims= " %%a in ('findstr /r /c:"https://.*ngrok-free.app" ngrok.log') do set NGROK_URL=%%a

echo Ngrok URL detected: %NGROK_URL%

REM Update baseUrl in S3ApiService.dart
powershell -Command "(Get-Content .\lib\utils\aws_s3_api.dart) -replace 'static const baseUrl = \".*\";', 'static const baseUrl = \"%NGROK_URL%\";' | Set-Content .\lib\utils\aws_s3_api.dart"

echo Done! Your Flutter app will now use %NGROK_URL%
pause
