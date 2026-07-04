# Deployment overview

| Layer | Service | Guide |
|-------|---------|-------|
| Database | **Neon** | Already set up |
| API | **Railway** | [railway-deploy.md](railway-deploy.md) |
| API (local demo, no hosting bill) | **Cloudflare Tunnel** | [cloudflare-tunnel-deploy.md](cloudflare-tunnel-deploy.md) |
| Frontend | **GitHub Pages** | Set `RENDER_API_URL` in repo Actions variables |

**Quick path:** [Deploy on Railway](railway-deploy.md) → set `RENDER_API_URL` → redeploy GitHub Pages.
