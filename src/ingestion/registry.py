from src.ingestion.base import SourceAdapter

_ADAPTERS: dict[str, type[SourceAdapter]] = {}


def register_adapter(name: str):
    def decorator(cls: type[SourceAdapter]) -> type[SourceAdapter]:
        _ADAPTERS[name] = cls
        cls.source_name = name
        return cls

    return decorator


def get_adapter(name: str) -> SourceAdapter:
    if name not in _ADAPTERS:
        raise KeyError(f"No ingestion adapter registered for source: {name}")
    return _ADAPTERS[name]()


def list_adapters() -> list[str]:
    return sorted(_ADAPTERS.keys())
