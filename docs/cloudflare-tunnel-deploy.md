# Deploy with Cloudflare Tunnel (100% free, no card)

**Use this when Render, Koyeb, and Hugging Face don't work.**

Your API runs on your PC and gets a public HTTPS URL via Cloudflare — no hosting bill, no credit card.

| Piece | Where |
|-------|--------|
| Database | Neon (already set up) |
| API | Your PC (`uvicorn`) |
| Public URL | Cloudflare quick tunnel |
| Frontend | GitHub Pages |

**Trade-off:** Your PC must stay on and the API running. The tunnel URL changes each restart (unless you set up a named tunnel with your own domain).

---

## Step 1 — Install cloudflared

**Windows (PowerShell as Admin):**

```powershell
winget install Cloudflare.cloudflared
```

Or download: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

Verify:

```powershell
cloudflared --version
```

---

## Step 2 — Configure `.env`

Your `.env` should already point at Neon:

```
DATABASE_URL=postgresql://...@...neon.tech/neondb?sslmode=require
GOOGLE_API_KEY=...
ADMIN_API_KEY=...
CORS_ORIGINS=https://ankitashok15.github.io,http://localhost:5173
```

---

## Step 3 — Start API + tunnel (one command)

```powershell
cd "c:\Users\Hp\OneDrive\Desktop\Spotify Review Analyser"
.\scripts\start_public_demo.ps1
```

This script:

1. Starts the FastAPI API on port **8000** (uses your `.env` → Neon)
2. Opens a Cloudflare quick tunnel
3. Prints a public URL like `https://random-words.trycloudflare.com`

**Keep this terminal open.** Closing it stops the API and tunnel.

---

## Step 4 — Connect GitHub Pages frontend

1. Copy the `https://....trycloudflare.com` URL from the script output
2. GitHub → `ankitashok15/Review-Analyzer` → **Settings** → **Secrets and variables** → **Actions** → **Variables**
3. Set **`RENDER_API_URL`** = that URL (no trailing slash)
4. **Actions** → **Deploy Frontend to GitHub Pages** → **Run workflow**

---

## Step 5 — Test

```powershell
curl https://YOUR-TUNNEL.trycloudflare.com/health
```

Open https://ankitashok15.github.io/Review-Analyzer/ and try **Search**.

---

## Manual start (two terminals)

**Terminal 1 — API:**

```powershell
cd "c:\Users\Hp\OneDrive\Desktop\Spotify Review Analyser"
.\.venv\Scripts\Activate.ps1
$env:CORS_ORIGINS = "https://ankitashok15.github.io,http://localhost:5173"
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Tunnel:**

```powershell
cloudflared tunnel --url http://localhost:8000
```

Look for: `Your quick Tunnel has been created! Visit it at https://....trycloudflare.com`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `cloudflared` not found | Restart terminal after `winget install`, or use full path |
| `/health` shows `db: disconnected` | Check `DATABASE_URL` in `.env` |
| Frontend loads, API calls fail | Update `RENDER_API_URL` + redeploy frontend; check `CORS_ORIGINS` includes `https://ankitashok15.github.io` |
| Search returns error | Gemini embed quota exhausted — wait ~24h |
| URL stopped working | Tunnel closed — rerun `start_public_demo.ps1` and update `RENDER_API_URL` |

---

## Stable URL (optional, advanced)

Quick tunnel URLs change every restart. For a **fixed** URL you need:

1. A free domain (or subdomain on Cloudflare)
2. A **named Cloudflare tunnel** (free Cloudflare account)

See: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

For a portfolio demo, updating `RENDER_API_URL` when you demo is usually enough.
