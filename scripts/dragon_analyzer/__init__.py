"""Public analyzer API with optional heavy imports resolved only on demand."""
from importlib import import_module

_EXPORTS = {
    "DragonAnalyzer": "analyzer",
    "create_analyzer": "analyzer",
    "DragonData": "models",
    "Dragon": "models",
    "ArmyComposition": "models",
    "Ability": "models",
    "Habit": "models",
    "DragonClass": "models",
    "AbilityType": "models",
    "DamageType": "models",
    "DragonScreenshotOCR": "ocr",
    "create_ocr_processor": "ocr",
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module("." + _EXPORTS[name], __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
