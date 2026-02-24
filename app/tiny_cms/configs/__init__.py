"""
Settings package for the tiny_cms Django project.

Django loads settings from a concrete module (e.g. `tiny_cms.configs.dev`),
but historically some code may import `tiny_cms.configs` directly. To keep that
working without `import *`, we re-export UPPER_CASE settings from the selected
module.
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType


def _select_settings_module() -> str:
    settings_module = os.getenv("DJANGO_SETTINGS_MODULE") or "tiny_cms.configs.dev"

    if settings_module.endswith(".prod") or "prod" in settings_module:
        return "tiny_cms.configs.prod"
    if settings_module.endswith(".dev") or "dev" in settings_module:
        return "tiny_cms.configs.dev"
    return "tiny_cms.configs.dev"


_settings: ModuleType = importlib.import_module(_select_settings_module())

for _name in dir(_settings):
    if _name.isupper():
        globals()[_name] = getattr(_settings, _name)

__all__ = sorted([name for name in globals() if name.isupper()])
