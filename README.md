# Travel Guide Audio Generator

AI-generated travel descriptions and audio guides, with a Vite frontend and Flask API.

## Run locally

1. Install the backend dependencies from `Backend/requirements.txt` and create `Backend/.env` with `GEMINI_API_KEY` and `MURF_API_KEY`.
2. Start the backend with `Backend/.venv/bin/python Backend/app.py` from the repository root.
3. In another terminal, run `npm install` and `npm run dev` from `Frontend/`.

The Vite development server proxies API requests to Flask on `127.0.0.1:5000`.

## Deploy to Vercel

Import this repository into Vercel with the repository root as the project root. The repository's `vercel.json` configures separate Flask and Vite services and routes the guide and health endpoints to Flask.

In Vercel Project Settings → Environment Variables, add `GEMINI_API_KEY` and `MURF_API_KEY` for the environments you use, then redeploy. Never put real API keys in source control; use `Backend/.env` only for local development.