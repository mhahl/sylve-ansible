#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
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
    choices:
    - record
    - config
    default: record
    required: false
  state:
    description: Desired state.
    type: str
    choices:
    - present
    - absent
    - query
    default: present
    required: false
  record_id:
    description: Numeric mDNS record ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: mDNS record name.
    type: str
    required: false
  type:
    description: mDNS record/service type.
    type: str
    required: false
  port:
    description: Service port.
    type: int
    required: false
  enabled:
    description: Enable the mDNS record or service.
    type: bool
    required: false
  data:
    description: Additional raw request fields (or full body for C(resource=config)).
    type: dict
    required: false
version_added: 1.0.0
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
- name: Create an mDNS record
  sylve.cloud.sylve_mdns:
    resource: record
    name: web-ui
    type: _https._tcp
    port: 8443
    state: present

- name: Manage Sylve mDNS configuration and records on a specific node using a named context
  sylve.cloud.sylve_mdns:
    context: prod
    node: node1.lan
    resource: record
    state: query
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
mdns:
  description: mDNS record or configuration details.
  returned: always
  type: raw
  sample: '{"id": 1, "name": "web-ui", "type": "_https._tcp"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveMDNSModule(SylveModule):
    argument_spec = {
        "resource": {"type": "str", "choices": ["record", "config"], "default": "record"},
        "state": {"type": "str", "choices": ["present", "absent", "query"], "default": "present"},
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
            if state == "query" or (
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
        if state == "query":
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
