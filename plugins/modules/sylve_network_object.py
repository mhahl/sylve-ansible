#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_network_object
short_description: Manage Sylve network and firewall alias objects
description:
  - Create, update, delete, or bulk-delete network alias objects (Host, Network, Port, Mac).
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired network object state.
    type: str
    choices: [present, absent]
    default: present
  object_id:
    description: Numeric network object ID.
    type: int
    aliases: [id]
  ids:
    description: List of object IDs for bulk deletion when C(state=absent).
    type: list
    elements: int
  name:
    description: Network object name.
    type: str
  type:
    description: Object type (e.g. C(Host), C(Network), C(Port), C(Mac)).
    type: str
  values:
    description: List of values (IPs, CIDRs, ports, or MAC addresses).
    type: list
    elements: str
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Create a MAC address object
  sylve.cloud.sylve_network_object:
    name: web-01-mac
    type: Mac
    values: ["02:00:00:10:20:30"]
    state: present
"""

RETURN = r"""
object:
  description: Network object details.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveNetworkObjectModule(SylveModule):
    argument_spec = {
        "state": {"type": "str", "choices": ["present", "absent"], "default": "present"},
        "object_id": {"type": "int", "aliases": ["id"]},
        "ids": {"type": "list", "elements": "int"},
        "name": {"type": "str"},
        "type": {"type": "str"},
        "values": {"type": "list", "elements": "str"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        if self.params["state"] == "absent" and self.params.get("ids"):
            if not self.check_mode:
                self.client.delete(
                    "/network/object",
                    json_body={"ids": self.params["ids"]},
                    node=self.node,
                )
            self.exit_json(changed=True, object={"ids": self.params["ids"]})
            return

        objs = self.client.get("/network/object", node=self.node) or []
        oid = self.params.get("object_id")
        name = self.params.get("name")
        existing = None
        for obj in objs if isinstance(objs, list) else []:
            if not isinstance(obj, dict):
                continue
            if oid is not None and obj.get("id") == oid:
                existing = obj
                break
            if name and str(obj.get("name") or "").lower() == name.lower():
                existing = obj
                oid = int(obj["id"])
                break

        if self.params["state"] == "absent":
            if oid is None:
                self.exit_json(changed=False, object={})
                return
            if not self.check_mode:
                self.client.delete(f"/network/object/{oid}", node=self.node)
            self.exit_json(changed=True, object=existing or {"id": oid})
            return

        payload: dict = dict(self.params.get("data") or {})
        if self.params.get("name") is not None:
            payload["name"] = self.params["name"]
        if self.params.get("type") is not None:
            payload["type"] = self.params["type"]
        if self.params.get("values") is not None:
            payload["values"] = self.params["values"]

        if existing and oid is not None:
            cur_vals = [
                str(v.get("value") if isinstance(v, dict) else v)
                for v in (existing.get("entries") or existing.get("values") or [])
            ]
            compare_current = dict(existing, values=cur_vals)
            if not self.subset_differs(payload, compare_current):
                self.exit_json(changed=False, object=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/network/object/{oid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, object=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/network/object", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, object=resp or payload)


def main() -> None:
    SylveNetworkObjectModule()()


if __name__ == "__main__":
    main()
