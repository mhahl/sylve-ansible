#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_network_interface
short_description: Manage Sylve host Layer-3 network interfaces, global network config, and pending IP changes
description:
  - Configure or remove host Layer-3 interface IP settings (C(/network/interface/{name}/l3)), reapply L3 settings,
    confirm or revert pending host IP transactions, or update global network settings (C(/network/global-config)).
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired L3 interface or global network action.
    type: str
    choices: [present, absent, reapplied, pending_confirmed, pending_reverted, global_config]
    default: present
  name:
    description: Host network interface name (e.g. C(em0), C(vtnet0)).
    type: str
  pending_id:
    description: Pending host IP transaction ID for C(pending_confirmed) or C(pending_reverted).
    type: str
  dhcp:
    description: Enable DHCPv4 on the interface.
    type: bool
  slaac:
    description: Enable IPv6 SLAAC on the interface.
    type: bool
  mtu:
    description: Interface MTU.
    type: int
  ipv4:
    description: List of IPv4 address configurations.
    type: list
    elements: raw
  ipv6:
    description: List of IPv6 address configurations.
    type: list
    elements: raw
  description:
    description: Interface description.
    type: str
  data:
    description: Raw request body for L3 configuration or C(global_config).
    type: dict
"""

EXAMPLES = r"""
- name: Configure static IPv4 on em1
  sylve.cloud.sylve_network_interface:
    name: em1
    dhcp: false
    mtu: 1500
    ipv4:
      - ip: 192.168.10.10
        netmask: 24
    state: present
"""

RETURN = r"""
interface:
  description: Interface L3 configuration or operation result.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveNetworkInterfaceModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": [
                "present",
                "absent",
                "reapplied",
                "pending_confirmed",
                "pending_reverted",
                "global_config",
            ],
            "default": "present",
        },
        "name": {"type": "str"},
        "pending_id": {"type": "str"},
        "dhcp": {"type": "bool"},
        "slaac": {"type": "bool"},
        "mtu": {"type": "int"},
        "ipv4": {"type": "list", "elements": "raw"},
        "ipv6": {"type": "list", "elements": "raw"},
        "description": {"type": "str"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        name = self.params.get("name")
        pending_id = self.params.get("pending_id")

        if state == "global_config":
            current = self.client.get("/network/global-config", node=self.node) or {}
            desired = dict(self.params.get("data") or {})
            if isinstance(current, dict) and not self.subset_differs(desired, current):
                self.exit_json(changed=False, interface=current)
                return
            if not self.check_mode:
                resp = self.client.put("/network/global-config", json_body=desired, node=self.node)
            else:
                resp = desired
            self.exit_json(changed=True, interface=resp or desired)
            return

        if state in ("pending_confirmed", "pending_reverted"):
            if not pending_id:
                self.fail_json(msg="'pending_id' is required for pending IP confirmation/revert.")
            act = "confirm" if state == "pending_confirmed" else "revert"
            if not self.check_mode:
                resp = self.client.post(
                    f"/network/host-ip/pending/{pending_id}/{act}", node=self.node
                )
            else:
                resp = {"id": pending_id, "action": act}
            self.exit_json(changed=True, interface=resp or {})
            return

        if not name:
            self.fail_json(msg="'name' is required for interface operations.")

        if state == "reapplied":
            if not self.check_mode:
                resp = self.client.post(f"/network/interface/{name}/l3/reapply", node=self.node)
            else:
                resp = {"name": name}
            self.exit_json(changed=True, interface=resp or {"name": name})
            return

        if state == "absent":
            if not self.check_mode:
                self.client.delete(f"/network/interface/{name}/l3", node=self.node)
            self.exit_json(changed=True, interface={"name": name})
            return

        payload: dict = dict(self.params.get("data") or {})
        for key in ("dhcp", "slaac", "mtu", "ipv4", "ipv6", "description"):
            if self.params.get(key) is not None:
                payload[key] = self.params[key]

        if not self.check_mode:
            resp = self.client.put(
                f"/network/interface/{name}/l3", json_body=payload, node=self.node
            )
        else:
            resp = payload
        self.exit_json(changed=True, interface=resp or payload)


def main() -> None:
    SylveNetworkInterfaceModule()()


if __name__ == "__main__":
    main()
