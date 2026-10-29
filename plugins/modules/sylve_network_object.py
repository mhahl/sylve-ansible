#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
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
    choices:
    - present
    - absent
    default: present
    required: false
  object_id:
    description: Numeric network object ID.
    type: int
    aliases:
    - id
    required: false
  ids:
    description: List of object IDs for bulk deletion when C(state=absent).
    type: list
    elements: int
    required: false
  name:
    description: Network object name.
    type: str
    required: false
  type:
    description: Object type (e.g. C(Host), C(Network), C(Port), C(Mac)).
    type: str
    required: false
  values:
    description: List of values (IPs, CIDRs, ports, or MAC addresses).
    type: list
    elements: str
    required: false
  data:
    description: Additional raw request fields.
    type: dict
    required: false
version_added: 0.3.1
author:
- Sylve Contributors (@mhahl)
requirements:
- python >= 3.10
- PyYAML
attributes:
  check_mode:
    description: Can run in check mode and return changed status prediction without modifying the target.
    support: full
  diff_mode:
    description: Will return details on what has changed when in diff mode. This module does not report diffs.
    support: none
notes:
- Supports C(check_mode).
- 'C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.'
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).
seealso:
- module: sylve.cloud.sylve_api
  description: Execute any Sylve REST API endpoint directly.
- name: sylve.cloud collection README
  link: https://github.com/mhahl/sylve-ansible
  description: Authentication, configuration, and inventory plugin usage.
"""

EXAMPLES = r"""
- name: Create a MAC address object
  sylve.cloud.sylve_network_object:
    name: web-01-mac
    type: Mac
    values: ["02:00:00:10:20:30"]
    state: present

- name: Manage Sylve network and firewall alias objects on a specific node using a named context
  sylve.cloud.sylve_network_object:
    context: prod
    node: node1.lan
    name: web-01-mac
    type: Mac
    values: ["02:00:00:10:20:30"]
    state: present
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
"""

RETURN = r"""changed:
  description: Whether the module made changes on the Sylve cluster.
  returned: always
  type: bool
  sample: true
object:
  description: Network object details.
  returned: always
  type: dict
  sample: '{"id": 9, "name": "web-01-mac", "type": "Mac"}'
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
