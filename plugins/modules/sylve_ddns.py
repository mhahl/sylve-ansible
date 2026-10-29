#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_ddns
short_description: Manage Sylve Dynamic DNS entries
description:
- List, create, update, synchronize, or delete Dynamic DNS entries on Sylve.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired DDNS entry state or action.
    type: str
    choices:
    - present
    - absent
    - synced
    - query
    default: present
    required: false
  entry_id:
    description: Numeric DDNS entry ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: DDNS entry name or hostname.
    type: str
    required: false
  provider:
    description: DDNS provider name.
    type: str
    required: false
  domain:
    description: Domain or record to update.
    type: str
    required: false
  enabled:
    description: Enable the DDNS entry.
    type: bool
    default: true
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
- name: Create a Dynamic DNS entry
  sylve.cloud.sylve_ddns:
    name: home-wan
    provider: cloudflare
    domain: home.example.com
    state: present

- name: Manage Sylve Dynamic DNS entries on a specific node using a named context
  sylve.cloud.sylve_ddns:
    context: prod
    node: node1.lan
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
ddns:
  description: Dynamic DNS entry details.
  returned: always
  type: raw
  sample: '{"id": 1, "name": "home-wan", "domain": "home.example.com"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveDDNSModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "synced", "query"],
            "default": "present",
        },
        "entry_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "provider": {"type": "str"},
        "domain": {"type": "str"},
        "enabled": {"type": "bool", "default": True},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        entries = self.client.get("/dynamic-dns/entries", node=self.node) or []
        if state == "query":
            self.exit_json(changed=False, ddns=entries)
            return

        eid = self.params.get("entry_id")
        name = self.params.get("name")
        domain = self.params.get("domain")
        existing = None
        for e in entries if isinstance(entries, list) else []:
            if not isinstance(e, dict):
                continue
            if eid is not None and e.get("id") == eid:
                existing = e
                break
            if name and str(e.get("name") or "").lower() == name.lower():
                existing = e
                eid = int(e["id"])
                break
            if domain and str(e.get("domain") or "").lower() == domain.lower():
                existing = e
                eid = int(e["id"])
                break

        if state == "absent":
            if eid is None:
                self.exit_json(changed=False, ddns={})
                return
            if not self.check_mode:
                self.client.delete(f"/dynamic-dns/entries/{eid}", node=self.node)
            self.exit_json(changed=True, ddns=existing or {"id": eid})
            return

        if state == "synced":
            if eid is None:
                self.fail_json(msg="DDNS entry not found for sync.")
            if not self.check_mode:
                resp = self.client.post(f"/dynamic-dns/entries/{eid}/sync", node=self.node)
            else:
                resp = {"id": eid}
            self.exit_json(changed=True, ddns=resp or {"id": eid})
            return

        payload: dict = dict(self.params.get("data") or {})
        for key in ("name", "provider", "domain", "enabled"):
            if self.params.get(key) is not None:
                payload[key] = self.params[key]

        if existing and eid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, ddns=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/dynamic-dns/entries/{eid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, ddns=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/dynamic-dns/entries", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, ddns=resp or payload)


def main() -> None:
    SylveDDNSModule()()


if __name__ == "__main__":
    main()
