# Changelog

## [2026-01-25] - Repository Migration & Supabase Storage

### Repository
- Migrated to GitHub Organization: `pelta-ai`
- New URL: https://github.com/pelta-ai/feline-skin-disease-detection
- Full git history preserved

### Added
- Supabase Storage integration as the default storage provider
- Training data scripts (`scripts/upload_training_data.py`, `scripts/generate_npz_from_supabase.py`)
- 400 training/testing images uploaded to Supabase (4 categories)

### Changed
- Default storage provider changed from Firebase to Supabase
- Updated environment variables for Supabase configuration

### Removed
- Firebase Storage provider and config files
- Local training images (now in Supabase)

**Note:** Firebase Auth is still used in the Flutter app. Only Firebase Storage was removed.

---

## [Previous] - Deployment Readiness

### Backend
- Added OpenTelemetry tracing
- Structured JSON logging with request IDs
- Storage provider abstraction (S3, Mock, Supabase)

### Frontend
- Firebase Crashlytics and Analytics
- Auth provider abstraction (Firebase, Mock)
- Environment-based configuration (dev/prod)
- Request ID tracing for debugging

### Documentation
- Added LOCAL_TESTING_GUIDE.md
