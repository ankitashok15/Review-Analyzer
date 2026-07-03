# Secrets Rotation Guide

## Secrets inventory

| Secret | Location | Rotation frequency |
|--------|----------|-------------------|
| `GOOGLE_API_KEY` | `.env`, Google AI Studio | 90 days or on leak |
| `ADMIN_API_KEY` | `.env` | 90 days or on staff change |
| `DATABASE_URL` password | `.env`, Docker Compose | 180 days |
| `REDIS_URL` password | `.env` (if auth enabled) | 180 days |

## Rotate ADMIN_API_KEY

1. Generate new key (40+ random chars)
2. Update `.env`: `ADMIN_API_KEY=new-value`
3. Restart API: `uvicorn src.api.main:app --reload`
4. Update any clients sending `X-API-Key` (scripts, CI secrets)
5. Revoke old key (remove from all stores)

## Rotate GOOGLE_API_KEY

1. [Google AI Studio](https://aistudio.google.com) → create new API key
2. Update `.env` `GOOGLE_API_KEY`
3. Restart API + Celery workers
4. Delete old key in Google console
5. Verify: `GET /health?detailed=true` → gemini `configured`

## GitHub Actions secrets

Repository: [ankitashok15/Review-Analyzer](https://github.com/ankitashok15/Review-Analyzer)

| Secret | Used for |
|--------|----------|
| `GOOGLE_API_KEY` | Optional integration tests |
| `ADMIN_API_KEY` | CI admin endpoint tests |

**Never commit** `.env` — only `.env.example` with placeholders.

## Redis / Postgres

- Change password in `docker-compose.yml` and `DATABASE_URL`
- `docker compose down && docker compose up -d`
- Run `alembic upgrade head` if needed

## Checklist after rotation

- [ ] `/health` ok
- [ ] Search + ask work
- [ ] Admin ingest with new `X-API-Key`
- [ ] Celery worker reconnects to Redis
