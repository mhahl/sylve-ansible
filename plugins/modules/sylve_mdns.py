#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_mdns
short_description: Manage Sylve mDNS configuration and records
description:
  - Query or update mDNS settings and create, update, or delete mDNS service/host records.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  resource:
    description: mDNS component to manage.
    type: str
    choices: [record, config]
    default: record
  state:
    description: Desired state.
    type: str
    choices: [present, absent, info]
    default: present
  record_id:
    description: Numeric mDNS record ID.
    type: int
    aliases: [id]
  name:
    description: mDNS record name.
    type: str
  type:
    description: mDNS record/service type.
    type: str
  port:
    description: Service port.
    type: int
  enabled:
    description: Enable the mDNS record or service.
    type: bool
  data:
    description: Additional raw request fields (or full body for C(resource=config)).
    type: dict
"""

EXAMPLES = r"""
- name: Create an mDNS record
  sylve.cloud.sylve_mdns:
    resource: record
    name: web-ui
    type: _https._tcp
    port: 8443
    state: present
"""

RETURN = r"""
mdns:
  description: mDNS record or configuration details.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveMDNSModule(SylveModule):
    argument_spec = {
        "resource": {"type": "str", "choices": ["record", "config"], "default": "record"},
        "state": {"type": "str", "choices": ["present", "absent", "info"], "default": "present"},
        "record_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "type": {"type": "str"},
        "port": {"type": "int"},
        "enabled": {"type": "bool"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        resource = self.params["resource"]
        state = self.params["state"]
        payload: dict = dict(self.params.get("data") or {})

        if resource == "config":
            current = self.client.get("/mdns/config", node=self.node) or {}
            if self.params.get("enabled") is not None:
                payload.setdefault("enabled", self.params["enabled"])
            if state == "info" or (
                isinstance(current, dict) and not self.subset_differs(payload, current)
            ):
                self.exit_json(changed=False, mdns=current)
                return
            if not self.check_mode:
                resp = self.client.put("/mdns/config", json_body=payload, node=self.node)
            else:
                resp = payload
            self.exit_json(changed=True, mdns=resp or payload)
            return

        records = self.client.get("/mdns/records", node=self.node) or []
        if state == "info":
            self.exit_json(changed=False, mdns=records)
            return

        rid = self.params.get("record_id")
        name = self.params.get("name")
        existing = None
        for r in records if isinstance(records, list) else []:
            if not isinstance(r, dict):
                continue
            if rid is not None and r.get("id") == rid:
                existing = r
                break
            if name and str(r.get("name") or "").lower() == name.lower():
                existing = r
                rid = int(r["id"])
                break

        if state == "absent":
            if rid is None:
                self.exit_json(changed=False, mdns={})
                return
            if not self.check_mode:
                self.client.delete(f"/mdns/records/{rid}", node=self.node)
            self.exit_json(changed=True, mdns=existing or {"id": rid})
            return

        for key in ("name", "type", "port", "enabled"):
            if self.params.get(key) is not None:
                payload[key] = self.params[key]

        if existing and rid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, mdns=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/mdns/records/{rid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, mdns=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/mdns/records", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, mdns=resp or payload)


def main() -> None:
    SylveMDNSModule()()


if __name__ == "__main__":
    main()
