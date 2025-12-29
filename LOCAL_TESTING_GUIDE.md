# Local Testing Guide

## Quick Test on Chrome (Web) - Works Immediately

```bash
cd app/final_design
flutter run -d chrome
```

Note: Camera won't work on web, but you can test the UI and upload functionality.

---

## Android Phone Testing (Recommended)

### Option 1: Connect Physical Android Phone

1. **Enable Developer Options on your phone:**
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times
   - Go back to Settings > Developer Options
   - Enable "USB Debugging"

2. **Connect phone via USB cable**

3. **Verify connection:**
   ```bash
   flutter devices
   ```
   Your phone should appear in the list.

4. **Run the app:**
   ```bash
   cd app/final_design
   flutter run
   ```

### Option 2: Android Emulator

1. **Open Android Studio**
   - Click "More Actions" (or Tools menu)
   - Select "Virtual Device Manager"

2. **Create New Device:**
   - Click "Create Device"
   - Select "Pixel 6" or similar
   - Click "Next"
   - Download a system image (API 34 recommended)
   - Click "Finish"

3. **Start the emulator:**
   - Click the Play button next to your device

4. **Run the app:**
   ```bash
   cd app/final_design
   flutter run
   ```

### Fix Android SDK Issues (One-time setup)

1. **Open Android Studio**
2. Go to **Tools > SDK Manager**
3. Click **SDK Tools** tab
4. Check **Android SDK Command-line Tools (latest)**
5. Click **Apply** and wait for download
6. Run: `flutter doctor --android-licenses`
7. Type `y` to accept all licenses

---

## Backend Server Setup

The app needs the Flask backend running to process images.

### Start Backend (Terminal 1):
```bash
cd app/final_design
python app.py
```
Server runs on http://localhost:5000

### Start ngrok tunnel (Terminal 2):
```bash
ngrok http 5000
```
Copy the https URL (e.g., https://xxxx.ngrok-free.app)

### Update app config:
Edit `lib/utils/app_config.dart` and update `_devBackendUrl` with your ngrok URL.

---

## Full Local Testing Steps

1. **Terminal 1 - Start Backend:**
   ```bash
   cd C:\github\feline_skin_disease_detection\app\final_design
   python app.py
   ```

2. **Terminal 2 - Start ngrok:**
   ```bash
   ngrok http 5000
   ```

3. **Update ngrok URL** in `lib/utils/app_config.dart`

4. **Terminal 3 - Run Flutter App:**
   ```bash
   cd C:\github\feline_skin_disease_detection\app\final_design
   flutter run
   ```

5. **Select device** when prompted (phone or emulator)

---

## Troubleshooting

### "703 problems in VS Code"
- Close and reopen VS Code
- Run `flutter pub get` in terminal
- Restart VS Code's Dart Analysis Server (Ctrl+Shift+P > "Dart: Restart Analysis Server")

### "No devices found"
- For phone: Enable USB debugging, try different USB cable
- For emulator: Start it from Android Studio first

### "Cannot connect to backend"
- Verify Flask server is running (http://localhost:5000)
- Verify ngrok is running and URL is updated in app_config.dart
- Check that ngrok URL starts with https://
