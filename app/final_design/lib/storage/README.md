# Storage

This folder holds **both** sides of the app's storage layer — the Flutter
frontend (Dart) and the Flask backend (Python) — co-located here.

## The two axes

Every file fits on two axes: **which side of the wire** it lives on, and
**cloud vs. mock**.

```
Flutter app (Dart)  ──HTTP──▶  Flask backend (Python)  ──▶  Supabase / S3 / mock
lib/storage/*.dart              lib/storage/*.py
```

Dart does **not** call Python directly. The Dart layer makes HTTP calls to the
Flask backend (`app.py`), and the backend does the real storage work.

|                | Cloud (dormant — kept for future) | Mock (testing / no backend)     |
| -------------- | --------------------------------- | ------------------------------- |
| **Dart** (FE)  | `cloud_storage_provider.dart`     | `mock_storage_provider.dart`    |
| **Python** (BE)| `supabase_provider.py` (primary), `s3_provider.py` (legacy) | `mock_provider.py` |
| **Shared**     | `app_storage_provider.dart` (abstract) / `index.dart`; `storage_provider.py` (abstract) / `__init__.py` |

The `mock_*` files are **test/offline stand-ins**, not the planned local-storage
implementation. They let the app run without a live backend.

## Cloud is dormant

Cloud storage is kept intact for future plans but is not the primary path. The
cloud providers are marked with a `DORMANT` banner at the top of each file.

- **Backend** picks its provider via the `STORAGE_PROVIDER` env var
  (`supabase` | `s3` | `mock`).
- **Frontend** picks its provider in `index.dart` (`CloudStorageProvider` for
  backend calls, `MockStorageProvider` on-device when `USE_MOCKS=true`).

## Naming note

`CloudStorageProvider` (Dart) and the `BackendApiService` it uses
(`utils/backend_api.dart`) are **generic backend clients** — they are not
S3-specific. They call whichever cloud provider the backend is configured to
use. (Both were previously named after "S3" before the backend moved to
Supabase.)
