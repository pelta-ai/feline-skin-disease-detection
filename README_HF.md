---
title: Pelta AI - Feline Skin Disease Detection
emoji: 🐱
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Pelta AI Backend

Flask backend for feline skin disease detection using a CNN ensemble.

## API Endpoints

- `POST /generate-ai-predictions` - Analyze cat skin image
- `GET /get-today-date` - Get current date
- `POST /add-file` - Upload file to storage
- `GET /get-file-url` - Get signed URL for file

## Environment Variables

Required:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SECRET_KEY` - Supabase secret key

Optional:
- `ALLOWED_ORIGINS` - Comma-separated list of origins permitted to call the API
  from a browser (e.g. `https://pelta-ai.com,https://pelta-ai.pages.dev`).
  Required once the web frontend is served from a CDN rather than by this app.
  When unset, only local development origins are allowed.
