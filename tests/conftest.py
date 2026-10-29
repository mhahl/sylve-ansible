# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _setup_collection_namespace() -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    for pkg_name, pkg_path in (
        ("ansible_collections", None),
        ("ansible_collections.sylve", None),
        ("ansible_collections.sylve.cloud", ROOT),
        ("ansible_collections.sylve.cloud.plugins", ROOT / "plugins"),
        ("ansible_collections.sylve.cloud.plugins.module_utils", ROOT / "plugins" / "module_utils"),
        ("ansible_collections.sylve.cloud.plugins.modules", ROOT / "plugins" / "modules"),
        ("ansible_collections.sylve.cloud.plugins.inventory", ROOT / "plugins" / "inventory"),
        ("ansible_collections.sylve.cloud.plugins.doc_fragments", ROOT / "plugins" / "doc_fragments"),
    ):
        if pkg_name not in sys.modules:
            mod = types.ModuleType(pkg_name)
            mod.__path__ = [str(pkg_path)] if pkg_path else []  # type: ignore[attr-defined]
            sys.modules[pkg_name] = mod
        if "." in pkg_name:
            parent_name, attr_name = pkg_name.rsplit(".", 1)
            setattr(sys.modules[parent_name], attr_name, sys.modules[pkg_name])


_setup_collection_namespace()
