#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_dhcp
short_description: Manage Sylve DHCP service configuration, IP ranges, and leases
description:
- Configure DHCP global settings, IPv4/IPv6 ranges, static leases, or delete dynamic leases.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  resource:
    description: DHCP sub-resource to manage.
    type: str
    choices:
    - config
    - range
    - lease
    - dynamic_lease
    default: range
    required: false
  state:
    description: Desired state.
    type: str
    choices:
    - present
    - absent
    default: present
    required: false
  id:
    description: Numeric ID of the DHCP range or static lease.
    type: int
    required: false
  start_ip:
    description: Range start IP address when C(resource=range).
    type: str
    required: false
  end_ip:
    description: Range end IP address when C(resource=range).
    type: str
    required: false
  type:
    description: Range type (e.g. C(ipv4), C(ipv6)) when C(resource=range).
    type: str
    required: false
  expiry:
    description: Lease expiry in seconds.
    type: int
    required: false
  slaac:
    description: Enable SLAAC on IPv6 range.
    type: bool
    required: false
  hostname:
    description: Static lease hostname when C(resource=lease).
    type: str
    required: false
  ip:
    description: Static or dynamic lease IP address.
    type: str
    required: false
  mac:
    description: Static or dynamic lease MAC address.
    type: str
    required: false
  data:
    description: Additional raw request fields (or full body for C(resource=config)).
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
- name: Create a DHCPv4 range
  sylve.cloud.sylve_dhcp:
    resource: range
    type: ipv4
    start_ip: 192.168.10.100
    end_ip: 192.168.10.200
    expiry: 3600
    state: present

- name: Manage Sylve DHCP service configuration, IP ranges, and leases on a specific node using a named context
  sylve.cloud.sylve_dhcp:
    context: prod
    node: node1.lan
    resource: range
    state: present
    type: ipv4
    start_ip: 192.168.10.100
    end_ip: 192.168.10.200
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
dhcp:
  description: DHCP resource details.
  returned: always
  type: raw
  sample: '{"id": 4, "startIp": "192.168.10.100", "endIp": "192.168.10.200"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveDHCPModule(SylveModule):
    argument_spec = {
        "resource": {
            "type": "str",
            "choices": ["config", "range", "lease", "dynamic_lease"],
            "default": "range",
        },
        "state": {"type": "str", "choices": ["present", "absent"], "default": "present"},
        "id": {"type": "int"},
        "start_ip": {"type": "str"},
        "end_ip": {"type": "str"},
        "type": {"type": "str"},
        "expiry": {"type": "int"},
        "slaac": {"type": "bool"},
        "hostname": {"type": "str"},
        "ip": {"type": "str"},
        "mac": {"type": "str"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        resource = self.params["resource"]
        state = self.params["state"]
        payload: dict = dict(self.params.get("data") or {})

        if resource == "config":
            current = self.client.get("/network/dhcp/config", node=self.node) or {}
            if isinstance(current, dict) and not self.subset_differs(payload, current):
                self.exit_json(changed=False, dhcp=current)
                return
            if not self.check_mode:
                resp = self.client.put("/network/dhcp/config", json_body=payload, node=self.node)
            else:
                resp = payload
            self.exit_json(changed=True, dhcp=resp or payload)
            return

        if resource == "dynamic_lease":
            if state != "absent":
                self.fail_json(msg="dynamic_lease only supports state=absent.")
            if self.params.get("ip"):
                payload["ip"] = self.params["ip"]
            if self.params.get("mac"):
                payload["mac"] = self.params["mac"]
            if not self.check_mode:
                self.client.delete(
                    "/network/dhcp/lease/dynamic", json_body=payload, node=self.node
                )
            self.exit_json(changed=True, dhcp=payload)
            return

        if resource == "range":
            for src, dst in (
                ("start_ip", "startIp"),
                ("end_ip", "endIp"),
                ("type", "type"),
                ("expiry", "expiry"),
                ("slaac", "slaac"),
            ):
                if self.params.get(src) is not None:
                    payload[dst] = self.params[src]
            items = self.client.get("/network/dhcp/range", node=self.node) or []
            item_id = self.params.get("id")
            existing = None
            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue
                if item_id is not None and item.get("id") == item_id:
                    existing = item
                    break
                if (
                    payload.get("startIp")
                    and item.get("startIp") == payload.get("startIp")
                    and item.get("endIp") == payload.get("endIp")
                ):
                    existing = item
                    item_id = int(item["id"])
                    break
            base_path = "/network/dhcp/range"
        else:
            for src, dst in (
                ("hostname", "hostname"),
                ("ip", "ip"),
                ("mac", "mac"),
                ("expiry", "expiry"),
            ):
                if self.params.get(src) is not None:
                    payload[dst] = self.params[src]
            items = self.client.get("/network/dhcp/lease", node=self.node) or []
            item_id = self.params.get("id")
            existing = None
            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue
                if item_id is not None and item.get("id") == item_id:
                    existing = item
                    break
                if payload.get("hostname") and item.get("hostname") == payload.get("hostname"):
                    existing = item
                    item_id = int(item["id"])
                    break
            base_path = "/network/dhcp/lease"

        if state == "absent":
            if item_id is None:
                self.exit_json(changed=False, dhcp={})
                return
            if not self.check_mode:
                self.client.delete(f"{base_path}/{item_id}", node=self.node)
            self.exit_json(changed=True, dhcp=existing or {"id": item_id})
            return

        if existing and item_id is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, dhcp=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"{base_path}/{item_id}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, dhcp=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(base_path, json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, dhcp=resp or payload)


def main() -> None:
    SylveDHCPModule()()


if __name__ == "__main__":
    main()
