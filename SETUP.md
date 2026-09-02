# Setup Guide — Pelta AI Flask Backend

Step-by-step instructions to get the Flask backend running locally for testing.

## What you need from the project owner

- [ ] The `trained_models/` folder (5 `.keras` files, ~30 MB) — **these are not in the repo**
- [ ] Optionally, Supabase credentials (not needed if you use mock mode in Step 5)

## Prerequisites

- **Python 3.10+** ([python.org](https://python.org)) — 3.13 is known to work
- **Git**
- Flutter SDK *only* if you also want to run the mobile UI

---

## Step 1 — Clone

```bash
git clone <repo-url>
cd feline-skin-disease-detection
```

## Step 2 — Install Python dependencies

The setup script creates a `.venv` and installs everything. The `-Python`/`--python` flag skips Flutter:

```powershell
# Windows (PowerShell)
./setup.ps1 -Python
```

```bash
# macOS / Linux
./setup.sh --python
```

> This pulls TensorFlow — expect a **~600 MB download** and several minutes.

> **PowerShell error about scripts being disabled?** Run once:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## Step 3 — Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1     # Windows
```

```bash
source .venv/bin/activate         # macOS / Linux
```

Your prompt should now show `(.venv)`.

## Step 4 — Add the model files

Put the folder you were sent at the **repo root**, so it looks like this:

```
feline-skin-disease-detection/
├── trained_models/
│   ├── new_mobilenetv3small_frozen_seed_1.keras
│   ├── new_mobilenetv3small_frozen_seed_2.keras
│   ├── new_mobilenetv3small_frozen_seed_3.keras
│   ├── new_mobilenetv3small_frozen_seed_4.keras
│   └── new_mobilenetv3small_frozen_seed_5.keras
├── app/
└── src/
```

All five must be present — the ensemble averages predictions across all of them.

## Step 5 — Create the `.env` file

Copy the template to the **repo root**:

```powershell
copy app\final_design\.env.example .env      # Windows
```

```bash
cp app/final_design/.env.example .env         # macOS / Linux
```

Then open `.env` and change **one line**:

```
STORAGE_PROVIDER=mock
```

This runs storage in-memory so you don't need a Supabase account. The AI prediction
endpoint works fully in this mode.

*If you were given real Supabase credentials instead, leave `STORAGE_PROVIDER=supabase`
and fill in `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and `SUPABASE_SECRET_KEY`.*

## Step 6 — Start the server

**Run from the `app/final_design` directory** — this matters:

```bash
cd app/final_design
python app.py
```

You should see `Starting server on 0.0.0.0:5000`. Leave this terminal open.

## Step 7 — Verify it works

In a **second terminal**:

```bash
curl http://localhost:5000/health
```

Expected response:

```json
{"status":"healthy","service":"pelta-ai-backend"}
```

Then test an actual prediction using a sample image from the repo (run from the repo root):

```bash
curl -X POST http://localhost:5000/generate-ai-predictions \
  -F "user_id=testuser" \
  -F "file=@test_images/sample_dermatitis_1.jpg"
```

You'll get back a top-3 ranked prediction with confidence scores.

> **The first prediction takes 10–30 seconds** while the 5 models load into memory.
> Every request after that is fast — the models stay cached for the life of the
> process. This is expected, not a hang.

---

## Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| `ValueError: Set SUPABASE_URL and SUPABASE_SECRET_KEY...` on startup | `.env` missing or not at repo root. Confirm Step 5, and that `STORAGE_PROVIDER=mock`. |
| `FileNotFoundError: CNN model file not found` | `trained_models/` missing or incomplete — all 5 files, at repo root (Step 4). |
| `ModuleNotFoundError` | Virtual environment not activated — redo Step 3, check for `(.venv)` in your prompt. |
| Port 5000 already in use | Set `FLASK_PORT=5001` in `.env`. On macOS, AirPlay Receiver squats on port 5000 — disable it in System Settings → General → AirDrop & Handoff. |
| PowerShell: "running scripts is disabled" | See the note in Step 2. |

## Running the Flutter app too

For the full mobile experience, see `LOCAL_TESTING_GUIDE.md`. In short: run `./setup.ps1`
without the `-Python` flag, start an ngrok tunnel to port 5000, and paste the tunnel URL
into `lib/utils/app_config.dart`.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/generate-ai-predictions` | Run the CNN ensemble on an uploaded image |
| GET | `/get-today-date` | Current date used for folder naming |
| POST | `/add-file` | Upload a file to storage |
| GET | `/list-objects` | List stored objects under a prefix |
| GET | `/get-file-url` | Get a URL for a stored file |
| GET | `/serve-file` | Serve file bytes directly (mock mode) |
| POST | `/download-file` | Download a stored file locally |
| GET | `/folder-exists` | Check whether a storage folder exists |
| POST | `/create-user-folder` | Create a user's storage folder |
| POST | `/create-today-folder` | Create today's dated folders |
