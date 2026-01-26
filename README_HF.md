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

Flask backend for feline skin disease detection using YOLOv8 + CNN.

## API Endpoints

- `POST /generate-ai-predictions` - Analyze cat skin image
- `GET /get-today-date` - Get current date
- `POST /add-file` - Upload file to storage
- `GET /get-file-url` - Get signed URL for file

## Environment Variables

Required:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SECRET_KEY` - Supabase secret key
