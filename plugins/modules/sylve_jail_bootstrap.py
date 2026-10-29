#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_jail_bootstrap
short_description: Manage pkgbase FreeBSD jail bootstraps on Sylve
description:
  - List, create, or delete pkgbase FreeBSD jail bootstraps on a ZFS pool.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired bootstrap state.
    type: str
    choices: [present, absent]
    default: present
  name:
    description: Bootstrap dataset/entry name (used for C(state=absent) or matching).
    type: str
  pool:
    description: ZFS pool name.
    type: str
  major:
    description: FreeBSD major version (e.g. C(14) or C(15)).
    type: int
  minor:
    description: FreeBSD minor version (e.g. C(2)).
    type: int
    default: 0
  type:
    description: Bootstrap flavor (e.g. C(base), C(minimal)).
    type: str
    default: base
"""

EXAMPLES = r"""
- name: Ensure FreeBSD 14.2 base jail bootstrap exists on zroot
  sylve.cloud.sylve_jail_bootstrap:
    pool: zroot
    major: 14
    minor: 2
    type: base
    state: present
"""

RETURN = r"""
bootstrap:
  description: Bootstrap record or request payload.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveJailBootstrapModule(SylveModule):
    argument_spec = {
        "state": {"type": "str", "choices": ["present", "absent"], "default": "present"},
        "name": {"type": "str"},
        "pool": {"type": "str"},
        "major": {"type": "int"},
        "minor": {"type": "int", "default": 0},
        "type": {"type": "str", "default": "base"},
    }

    def run(self) -> None:
        pool = self.params.get("pool")
        name = self.params.get("name")
        major = self.params.get("major")
        minor = self.params.get("minor", 0)
        btype = self.params.get("type", "base")

        existing = None
        if pool:
            items = self.client.get("/jail/bootstraps", params={"pool": pool}, node=self.node) or []
            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue
                if name and item.get("name") == name:
                    existing = item
                    break
                if (
                    major is not None
                    and str(item.get("version") or "").startswith(f"{major}.{minor}")
                    and (not btype or item.get("type") == btype)
                ):
                    existing = item
                    name = item.get("name")
                    break

        if self.params["state"] == "absent":
            if not name:
                self.exit_json(changed=False, bootstrap={})
                return
            if not self.check_mode:
                self.client.delete(
                    f"/jail/bootstraps/{name}",
                    params={"pool": pool} if pool else None,
                    node=self.node,
                )
            self.exit_json(changed=True, bootstrap=existing or {"name": name})
            return

        if existing:
            self.exit_json(changed=False, bootstrap=existing)
            return

        if not pool or major is None:
            self.fail_json(msg="Both 'pool' and 'major' are required to create a jail bootstrap.")
        body = {"pool": pool, "major": major, "minor": minor, "type": btype}
        if not self.check_mode:
            resp = self.client.post("/jail/bootstraps", json_body=body, node=self.node)
        else:
            resp = body
        self.exit_json(changed=True, bootstrap=resp or body)


def main() -> None:
    SylveJailBootstrapModule()()


if __name__ == "__main__":
    main()
