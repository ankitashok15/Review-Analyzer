from fastapi import HTTPException, Request, status

from config.settings import get_settings


def verify_admin_api_key(request: Request) -> None:
    settings = get_settings()
    if not settings.require_admin_api_key:
        return

    expected = settings.admin_api_key.strip()
    if not expected or expected == "placeholder":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API key is not configured on the server",
        )

    provided = (request.headers.get(settings.admin_api_key_header) or "").strip()
    if not provided or provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
        )
