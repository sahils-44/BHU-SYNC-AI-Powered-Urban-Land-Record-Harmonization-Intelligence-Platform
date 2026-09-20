# BHU-SYNC Local Setup & Configuration Guide

This guide describes how to configure and run the BHU-SYNC frontend and backend on localhost.

## 1. Required Frontend Environment Variables

The frontend requires public Supabase client credentials defined in rontend/.env.local or rontend/.env:

`env
VITE_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_PUBLIC_ANON_KEY
`

A template with safe placeholders is provided at rontend/.env.example.

> [!CAUTION]
> **Zero Service-Role Key Exposure**:
> NEVER put SUPABASE_SERVICE_ROLE_KEY or database passwords in the frontend directory or inside any VITE_ variables. The frontend client only requires the public anonymous/publishable key (VITE_SUPABASE_ANON_KEY).

## 2. Environment File Locations

- **Backend Configuration:** ackend/.env (contains SUPABASE_URL, SUPABASE_KEY, DEMO_MODE=true, ALLOWED_ORIGINS).
- **Frontend Configuration:** rontend/.env.local (and rontend/.env) (contains VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY).

## 3. Starting the Services

### Backend (Terminal 1)
`powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
`
- API Endpoint: http://127.0.0.1:8000
- Swagger Docs: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

### Frontend (Terminal 2)
`powershell
cd frontend
npm run dev
`
- Web Application: http://localhost:5173

> [!IMPORTANT]
> **Restart Vite After Environment Changes**:
> Vite embeds import.meta.env.VITE_* variables at server startup. Whenever you add or edit .env or .env.local in rontend/, you MUST stop (Ctrl+C) and restart the Vite development server (
pm run dev) for changes to take effect.
