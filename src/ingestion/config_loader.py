from functools import lru_cache
from pathlib import Path

import yaml

SOURCES_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"


@lru_cache
def load_sources_config() -> dict:
    if not SOURCES_CONFIG_PATH.exists():
        return {"sources": {}}
    with SOURCES_CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {"sources": {}}


def get_source_config(source_key: str) -> dict:
    config = load_sources_config()
    return config.get("sources", {}).get(source_key, {})
