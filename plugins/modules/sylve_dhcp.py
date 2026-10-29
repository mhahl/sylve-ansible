#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
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
    choices: [config, range, lease, dynamic_lease]
    default: range
  state:
    description: Desired state.
    type: str
    choices: [present, absent]
    default: present
  id:
    description: Numeric ID of the DHCP range or static lease.
    type: int
  start_ip:
    description: Range start IP address when C(resource=range).
    type: str
  end_ip:
    description: Range end IP address when C(resource=range).
    type: str
  type:
    description: Range type (e.g. C(ipv4), C(ipv6)) when C(resource=range).
    type: str
  expiry:
    description: Lease expiry in seconds.
    type: int
  slaac:
    description: Enable SLAAC on IPv6 range.
    type: bool
  hostname:
    description: Static lease hostname when C(resource=lease).
    type: str
  ip:
    description: Static or dynamic lease IP address.
    type: str
  mac:
    description: Static or dynamic lease MAC address.
    type: str
  data:
    description: Additional raw request fields (or full body for C(resource=config)).
    type: dict
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
"""

RETURN = r"""
dhcp:
  description: DHCP resource details.
  returned: always
  type: dict
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
