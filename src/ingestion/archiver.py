import json
from datetime import datetime, timezone
from pathlib import Path

from config.settings import get_settings

settings = get_settings()


def archive_raw_payload(source: str, source_id: str | None, payload: dict) -> str | None:
    if not settings.archive_raw_payloads:
        return None

    root = Path(settings.raw_archive_path)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folder = root / source / day
    folder.mkdir(parents=True, exist_ok=True)

    safe_id = (source_id or "unknown").replace("/", "_")[:120]
    path = folder / f"{safe_id}.json"
    path.write_text(json.dumps(payload, default=str), encoding="utf-8")
    return str(path)
