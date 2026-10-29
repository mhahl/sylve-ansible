# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
MOD_FILES = sorted((ROOT / "plugins" / "modules").glob("sylve_*.py"))


def _blocks(path: pathlib.Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    out = {}
    for block in ("DOCUMENTATION", "EXAMPLES", "RETURN"):
        m = re.search(rf"{block} = r\"\"\"(.*?)\"\"\"", text, re.S)
        assert m, f"{path.name} is missing a {block} block"
        out[block] = m.group(1)
    return out


def test_docs_directory_mirrors_modules() -> None:
    """Every module must have a docs page mirroring its DOCUMENTATION."""
    import yaml as _yaml

    docs_dir = ROOT / "docs"
    assert (docs_dir / "index.md").exists()
    for mf in MOD_FILES:
        page = docs_dir / f"{mf.stem}.md"
        assert page.exists(), mf.name
        text = page.read_text(encoding="utf-8")
        mod = importlib.import_module(
            f"ansible_collections.sylve.cloud.plugins.modules.{mf.stem}"
        )
        doc = _yaml.safe_load(
            re.search(r'DOCUMENTATION = r"""(.*?)"""', mf.read_text(encoding="utf-8"), re.S).group(1)
        )
        assert doc["short_description"] in text, mf.name
        assert f"sylve.cloud.{mf.stem}" in text, mf.name
        for opt_name in (doc.get("options") or {}):
            assert f"`{opt_name}`" in text, (mf.name, opt_name)


def test_docs_follow_ansible_conventions() -> None:
    """Every module must carry full ansible-doc metadata, explicit required flags,
    at least two documented examples, and a RETURN block with samples."""
    assert len(MOD_FILES) == 45

    for mf in MOD_FILES:
        mod = importlib.import_module(
            f"ansible_collections.sylve.cloud.plugins.modules.{mf.stem}"
        )
        blocks = _blocks(mf)
        doc = yaml.safe_load(blocks["DOCUMENTATION"])
        assert doc["module"] == mf.stem, mf.name
        assert doc["version_added"] == "0.3.1", mf.name
        assert isinstance(doc["author"], list) and doc["author"], mf.name
        assert doc["attributes"]["check_mode"]["support"] == "full", mf.name
        assert doc["notes"], mf.name
        assert doc["seealso"], mf.name

        # required flags must be explicit and match argument_spec
        module_cls = next(
            v
            for k, v in vars(mod).items()
            if isinstance(v, type) and isinstance(getattr(v, "argument_spec", None), dict)
        )
        spec_required = {
            name
            for name, opts in module_cls.argument_spec.items()
            if isinstance(opts, dict) and opts.get("required") is True
        }
        for opt_name, opt_doc in (doc.get("options") or {}).items():
            assert "required" in opt_doc, f"{mf.name} option {opt_name} lacks required:"
            if opt_name in spec_required:
                assert opt_doc["required"] is True, f"{mf.name} option {opt_name}"

        examples = yaml.safe_load(blocks["EXAMPLES"])
        assert isinstance(examples, list) and len(examples) >= 2, mf.name
        assert any("register" in task for task in examples if isinstance(task, dict)), mf.name

        ret = yaml.safe_load(blocks["RETURN"])
        assert ret["changed"]["returned"] == "always", mf.name
        for key, val in ret.items():
            assert {"description", "returned", "type", "sample"} <= set(val), (
                mf.name,
                key,
            )
