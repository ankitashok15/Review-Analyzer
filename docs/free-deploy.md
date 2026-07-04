# Deploy for Free (Neon + Cloudflare Tunnel)

**Works when Render, Koyeb, and Hugging Face fail.** No credit card, no hosting bill.

| Component | Service | Cost |
|-----------|---------|------|
| PostgreSQL + pgvector | [Neon](https://neon.tech) | Free — **already set up** |
| FastAPI API | **Your PC** + [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) | Free |
| React dashboard | GitHub Pages | Free — **already live** |

**Full guide:** [cloudflare-tunnel-deploy.md](cloudflare-tunnel-deploy.md)

---

## Quick start (3 steps)

### 1. Install cloudflared

```powershell
winget install Cloudflare.cloudflared
```

Restart PowerShell after install.

### 2. Start API + public URL

```powershell
cd "c:\Users\Hp\OneDrive\Desktop\Spotify Review Analyser"
.\scripts\start_public_demo.ps1
```

Copy the `https://....trycloudflare.com` URL from the output.

### 3. Wire GitHub Pages

1. GitHub → repo → **Settings** → **Actions** → **Variables**
2. `RENDER_API_URL` = your tunnel URL
3. **Actions** → **Deploy Frontend to GitHub Pages** → **Run workflow**

Open https://ankitashok15.github.io/Review-Analyzer/

**Keep the PowerShell window open** while demoing.

---

## Your Neon data (ready)

| Data | Count |
|------|-------|
| Reviews | 1,354 |
| Embeddings | 1,034 (~76%) |

Search/Ask need Gemini quota (resets daily).

---

## Why other platforms failed

| Platform | Issue |
|----------|-------|
| Render | Credit card / paid Postgres |
| Koyeb | Credit card / no real free tier |
| Hugging Face | Monorepo too large, build timeouts, secrets setup — see [HF fix below](#hugging-face-spaces-if-you-want-to-retry) |

---

## Hugging Face Spaces (if you want to retry)

HF often fails when you point it at the full monorepo. **Pack a slim Space instead:**

```powershell
.\scripts\pack_huggingface_space.ps1
```

This creates `dist/hf-space/` — push **only those files** to your HF Space git repo, then add Secrets in Space Settings.

Template README: `deploy/huggingface/README.md`

---

## Local development

```powershell
uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev
```
