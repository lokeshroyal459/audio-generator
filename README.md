# Travel Guide Audio Generator

AI-generated travel descriptions and audio guides, with a Vite frontend and Flask API.

## Run locally

1. Install the backend dependencies from `Backend/requirements.txt` and create `Backend/.env` with `GEMINI_API_KEY` and `MURF_API_KEY`.
2. Start the backend with `Backend/.venv/bin/python Backend/app.py` from the repository root.
3. In another terminal, run `npm install` and `npm run dev` from `Frontend/`.

The Vite development server proxies API requests to Flask on `127.0.0.1:5000`.

## Deploy the frontend to Vercel and API to Render

Deploy `Frontend/` on Vercel and `Backend/` as a Render Web Service. On Render, use `pip install -r requirements.txt` as the build command and `gunicorn app:app` as the start command.

Set `GEMINI_API_KEY` and `MURF_API_KEY` in the Render service's Environment settings, and set `FRONTEND_ORIGINS` to the Vercel site origin. In Vercel, set `VITE_API_BASE_URL` to the Render service URL, then redeploy the frontend. Never put real API keys in source control; use `Backend/.env` only for local development.