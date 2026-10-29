#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_samba
short_description: Manage Sylve Samba global configuration, shares, and audit logs
description:
  - Query or update Samba global configuration, create/update/enable/disable/delete Samba shares, or fetch Samba audit logs.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  resource:
    description: Samba component to manage.
    type: str
    choices: [share, config, audit_logs]
    default: share
  state:
    description: Desired share state.
    type: str
    choices: [present, absent, enabled, disabled, info]
    default: present
  share_id:
    description: Numeric Samba share ID.
    type: int
    aliases: [id]
  name:
    description: Samba share name.
    type: str
  dataset:
    description: ZFS dataset or path backing the share.
    type: str
  enabled:
    description: Enable or disable the share.
    type: bool
  data:
    description: Additional raw request fields (or full body for C(resource=config)).
    type: dict
"""

EXAMPLES = r"""
- name: Create a Samba share
  sylve.cloud.sylve_samba:
    resource: share
    name: media
    dataset: zroot/media
    enabled: true
    state: present
"""

RETURN = r"""
samba:
  description: Samba share, global config, or audit logs.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveSambaModule(SylveModule):
    argument_spec = {
        "resource": {
            "type": "str",
            "choices": ["share", "config", "audit_logs"],
            "default": "share",
        },
        "state": {
            "type": "str",
            "choices": ["present", "absent", "enabled", "disabled", "info"],
            "default": "present",
        },
        "share_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "dataset": {"type": "str"},
        "enabled": {"type": "bool"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        resource = self.params["resource"]
        state = self.params["state"]
        payload: dict = dict(self.params.get("data") or {})

        if resource == "audit_logs":
            logs = self.client.get("/samba/audit-logs", node=self.node)
            self.exit_json(changed=False, samba=logs)
            return

        if resource == "config":
            current = self.client.get("/samba/config", node=self.node) or {}
            if state == "info" or (
                isinstance(current, dict) and not self.subset_differs(payload, current)
            ):
                self.exit_json(changed=False, samba=current)
                return
            if not self.check_mode:
                resp = self.client.put("/samba/config", json_body=payload, node=self.node)
            else:
                resp = payload
            self.exit_json(changed=True, samba=resp or payload)
            return

        shares = self.client.get("/samba/shares", node=self.node) or []
        if state == "info":
            self.exit_json(changed=False, samba=shares)
            return

        sid = self.params.get("share_id")
        name = self.params.get("name")
        existing = None
        for sh in shares if isinstance(shares, list) else []:
            if not isinstance(sh, dict):
                continue
            if sid is not None and sh.get("id") == sid:
                existing = sh
                break
            if name and str(sh.get("name") or "").lower() == name.lower():
                existing = sh
                sid = int(sh["id"])
                break

        if state == "absent":
            if sid is None:
                self.exit_json(changed=False, samba={})
                return
            if not self.check_mode:
                self.client.delete(f"/samba/shares/{sid}", node=self.node)
            self.exit_json(changed=True, samba=existing or {"id": sid})
            return

        if state in ("enabled", "disabled"):
            if sid is None:
                self.fail_json(msg="Samba share not found.")
            body = {"enabled": state == "enabled"}
            if not self.check_mode:
                resp = self.client.put(
                    f"/samba/shares/{sid}/enabled", json_body=body, node=self.node
                )
            else:
                resp = body
            self.exit_json(changed=True, samba=resp or body)
            return

        for key in ("name", "dataset", "enabled"):
            if self.params.get(key) is not None:
                payload[key] = self.params[key]

        if existing and sid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, samba=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/samba/shares/{sid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, samba=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/samba/shares", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, samba=resp or payload)


def main() -> None:
    SylveSambaModule()()


if __name__ == "__main__":
    main()
