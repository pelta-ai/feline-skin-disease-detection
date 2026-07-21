# Pelta AI - Feline Skin Disease Detection

> *"Pelta"* means "small shield" in Latin — protection for your pet's skin health.

A mobile app that uses AI to detect skin diseases in cats from photos. Built with Flutter (frontend) and Flask + CNN (backend).

## Features

- **AI-Powered Detection**: CNN ensemble for disease classification
- **Disease Categories**: Demodicosis, Dermatitis, Flea Allergy, Fungus, Ringworm, Scabies
- **User Accounts**: Firebase Authentication with email verification
- **Scan History**: View recent diagnoses and track pet health over time

## Tech Stack

| Component | Technology |
|-----------|------------|
| Mobile App | Flutter |
| Backend | Flask |
| Classification | CNN (Keras/TensorFlow) |
| Storage | Supabase Storage |
| Auth | Firebase Authentication |

## Getting Started

### Prerequisites

- Flutter SDK (3.x)
- Python 3.10+
- Supabase account (free tier)
- Firebase project (for auth)

### Install Dependencies

Run the setup script to install both the Python backend and Flutter app dependencies. It creates a Python virtual environment in `.venv`, installs `requirements.txt`, and runs `flutter pub get`.

```powershell
# Windows (PowerShell)
./setup.ps1
```

```bash
# macOS / Linux
./setup.sh
```

Install just one stack with `-Python`/`-Flutter` (PowerShell) or `--python`/`--flutter` (bash).

## Repository Note

Mirrored from [Daxz0/feline_skin_disease_detection](https://github.com/Daxz0/feline_skin_disease_detection) for the `pelta-ai` organization. Full git history preserved.

## Team

Built by a team of 3 student developers.

## License

This project is for educational purposes.

---

*Pelta AI — Your pet's shield against skin disease.*
