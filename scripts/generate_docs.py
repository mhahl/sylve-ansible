#!/usr/bin/env python3
"""Generate docs/*.md from module DOCUMENTATION/EXAMPLES/RETURN blocks."""

from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def blocks(path: pathlib.Path) -> tuple[dict, str, dict]:
    text = path.read_text(encoding="utf-8")
    doc = yaml.safe_load(re.search(r'DOCUMENTATION = r"""(.*?)"""', text, re.S).group(1))
    ex = re.search(r'EXAMPLES = r"""(.*?)"""', text, re.S).group(1).strip()
    ret = yaml.safe_load(re.search(r'RETURN = r"""(.*?)"""', text, re.S).group(1))
    return doc, ex, ret


def fmt_default(opt: dict) -> str:
    if "default" not in opt or opt["default"] is None:
        return "—"
    d = opt["default"]
    if isinstance(d, bool):
        return f"`{str(d).lower()}`"
    return f"`{d}`"


def fmt_choices(opt: dict) -> str:
    c = opt.get("choices")
    return ", ".join(f"`{x}`" for x in c) if c else "—"


def option_rows(options: dict, prefix: str = "") -> list[str]:
    rows = []
    for name, opt in (options or {}).items():
        if not isinstance(opt, dict):
            continue
        full = f"{prefix}{name}"
        req = "yes" if opt.get("required") else "no"
        aliases = opt.get("aliases")
        disp = f"`{full}`" + (f" (aliases: {', '.join(f'`{a}`' for a in aliases)})" if aliases else "")
        desc = str(opt.get("description", "")).replace("\n", " ")
        rows.append(
            f"| {disp} | `{opt.get('type', 'str')}` | {req} | {fmt_default(opt)} | {fmt_choices(opt)} | {desc} |"
        )
        sub = opt.get("suboptions")
        if isinstance(sub, dict):
            rows.extend(option_rows(sub, prefix=f"{full}."))
    return rows


def render(mod: str, doc: dict, examples: str, ret: dict) -> str:
    opt_count = len(doc.get("options") or {})
    lines = [
        f"# {mod}",
        "",
        f"_{doc.get('short_description', '')}_",
        "",
    ]
    for para in doc.get("description") or []:
        lines += [str(para).strip(), ""]
    lines += [
        f"- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.{mod}`)",
        f"- **Added in:** `sylve.cloud {doc.get('version_added', '1.0.0')}`",
        f"- **Author:** {', '.join(doc.get('author', []))}",
    ]
    reqs = doc.get("requirements")
    if reqs:
        lines.append(f"- **Requirements:** {', '.join(f'`{r}`' for r in reqs)}")
    attrs = (doc.get("attributes") or {}).get("check_mode", {}).get("support")
    if attrs:
        lines.append(f"- **Check mode:** supported (`{attrs}`)")
    lines += [""]

    lines += ["## Options", ""]
    if opt_count:
        lines += [
            "| Option | Type | Required | Default | Choices | Description |",
            "| --- | --- | --- | --- | --- | --- |",
            *option_rows(doc.get("options")),
            "",
        ]
    else:
        lines += ["_This module takes no options beyond the shared connection options._", ""]

    frag_note = (
        "All modules also accept the shared [sylve connection options](index.md#authentication) "
        "(`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, "
        "`auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`)."
    )
    lines += [frag_note, ""]

    if doc.get("notes"):
        lines += ["## Notes", ""]
        lines += [f"- {n}" for n in doc["notes"]] + [""]

    lines += ["## Examples", "", "```yaml", examples, "```", ""]
    lines += ["## Return values", ""]
    lines += [
        "| Key | Type | Returned | Description | Sample |",
        "| --- | --- | --- | --- | --- |",
    ]
    for key, val in (ret or {}).items():
        sample = str(val.get("sample", "—")).replace("\n", " ")
        lines.append(
            f"| `{key}` | `{val.get('type', '—')}` | {val.get('returned', '—')} | {val.get('description', '')} | `{sample}` |"
        )
    lines += [""]
    if doc.get("seealso"):
        lines += ["## See also", ""]
        for item in doc["seealso"]:
            if "module" in item:
                lines.append(f"- Module `{item['module']}` — {item.get('description', '')}")
            else:
                lines.append(f"- [{item.get('name')}]({item.get('link')}) — {item.get('description', '')}")
        lines += [""]

    lines.append(f"_Auto-generated from `plugins/modules/{mod}.py` — edit the module, not this file._")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    mods = sorted(p.stem for p in (ROOT / "plugins" / "modules").glob("sylve_*.py"))

    index = [
        "# sylve.cloud documentation",
        "",
        "Ansible collection for managing Sylve FreeBSD hypervisor clusters.",
        "Each page below mirrors its module's `DOCUMENTATION` block — "
        "the module source is the canonical reference.",
        "",
        "## Authentication",
        "",
        "All modules share `~/.config/sylve/config.yaml` contexts and `SYLVE_*` "
        "environment variables with `sylve-cli`. Common options: `config_path`, "
        "`context` (alias `cloud`), `auth` dict, `server` (`SYLVE_SERVER`), `token` "
        "(`SYLVE_TOKEN`), `username`/`password`, `auth_type`, `node` (`SYLVE_NODE`), "
        "`validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`.",
        "",
        "## Modules",
        "",
        "| Module | Short description |",
        "| --- | --- |",
    ]
    for mod in mods:
        doc, examples, ret = blocks(ROOT / "plugins" / "modules" / f"{mod}.py")
        (DOCS / f"{mod}.md").write_text(render(mod, doc, examples, ret), encoding="utf-8")
        index.append(f"| [`{mod}`]({mod}.md) | {doc.get('short_description', '')} |")
        print(f"wrote docs/{mod}.md")

    index += ["", "## Inventory", "", "See `plugins/inventory/sylve.py` (`sylve.cloud.sylve`).", ""]
    (DOCS / "index.md").write_text("\n".join(index), encoding="utf-8")
    print(f"\nwrote docs/index.md ({len(mods)} modules)")


if __name__ == "__main__":
    sys.exit(main())
