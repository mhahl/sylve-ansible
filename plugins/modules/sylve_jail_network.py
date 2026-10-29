#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_jail_network
short_description: Manage network attachments for a Sylve FreeBSD jail
description:
- Attach, update, or detach networks on a FreeBSD jail, or configure network inheritance.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired network state.
    type: str
    choices:
    - present
    - absent
    - inheritance
    default: present
    required: false
  jail:
    description: Jail CTID or name.
    type: str
    required: true
  network_id:
    description: Jail network attachment ID.
    type: int
    required: false
  name:
    description: Network attachment name.
    type: str
    required: false
  switch_id:
    description: Switch ID.
    type: int
    required: false
  switch_type:
    description: Switch type (C(standard) or C(manual)).
    type: str
    required: false
  mac_id:
    description: MAC object ID.
    type: int
    required: false
  ipv4_id:
    description: IPv4 network object ID.
    type: int
    required: false
  ipv4_gw_id:
    description: IPv4 gateway object ID.
    type: int
    required: false
  ipv6_id:
    description: IPv6 network object ID.
    type: int
    required: false
  ipv6_gw_id:
    description: IPv6 gateway object ID.
    type: int
    required: false
  dhcp:
    description: Enable DHCP on the jail interface.
    type: bool
    required: false
  slaac:
    description: Enable IPv6 SLAAC on the jail interface.
    type: bool
    required: false
  inherit_ipv4:
    description: Inherit host IPv4 when C(state=inheritance).
    type: bool
    required: false
  inherit_ipv6:
    description: Inherit host IPv6 when C(state=inheritance).
    type: bool
    required: false
  data:
    description: Additional raw request body fields.
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
- name: Attach jail 201 to switch 1 with DHCP
  sylve.cloud.sylve_jail_network:
    jail: 201
    name: net0
    switch_id: 1
    dhcp: true
    state: present

- name: Manage network attachments for a Sylve FreeBSD jail on a specific node using a named context
  sylve.cloud.sylve_jail_network:
    context: prod
    node: node1.lan
    jail: app-01
    state: inheritance
    inherit_ipv4: true
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
network:
  description: Jail network attachment details.
  returned: always
  type: dict
  sample: '{"id": 1, "name": "net0", "switchId": 2}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveJailNetworkModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "inheritance"],
            "default": "present",
        },
        "jail": {"type": "str", "required": True},
        "network_id": {"type": "int"},
        "name": {"type": "str"},
        "switch_id": {"type": "int"},
        "switch_type": {"type": "str"},
        "mac_id": {"type": "int"},
        "ipv4_id": {"type": "int"},
        "ipv4_gw_id": {"type": "int"},
        "ipv6_id": {"type": "int"},
        "ipv6_gw_id": {"type": "int"},
        "dhcp": {"type": "bool"},
        "slaac": {"type": "bool"},
        "inherit_ipv4": {"type": "bool"},
        "inherit_ipv6": {"type": "bool"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        ctid, host, _ = self.client.resolve_jail(self.params["jail"], node=self.node)
        state = self.params["state"]

        if state == "inheritance":
            body = {
                "ipv4": bool(self.params.get("inherit_ipv4", False)),
                "ipv6": bool(self.params.get("inherit_ipv6", False)),
            }
            if not self.check_mode:
                self.client.put(f"/jail/{ctid}/network/inheritance", json_body=body, node=host)
            self.exit_json(changed=True, network=body)
            return

        detail = self.client.get(f"/jail/{ctid}", node=host) or {}
        networks = detail.get("networks") or []
        net_id = self.params.get("network_id")
        existing = None
        for net in networks if isinstance(networks, list) else []:
            if not isinstance(net, dict):
                continue
            if net_id is not None and net.get("id") == net_id:
                existing = net
                break
            if self.params.get("name") and net.get("name") == self.params["name"]:
                existing = net
                net_id = net.get("id")
                break

        if state == "absent":
            if net_id is None:
                self.exit_json(changed=False, network={})
                return
            if not self.check_mode:
                self.client.delete(f"/jail/{ctid}/networks/{net_id}", node=host)
            self.exit_json(changed=True, network=existing or {"id": net_id})
            return

        payload: dict = dict(self.params.get("data") or {})
        field_map = {
            "name": "name",
            "switch_id": "switchId",
            "switch_type": "switchType",
            "mac_id": "macId",
            "ipv4_id": "ipv4Id",
            "ipv4_gw_id": "ipv4GwId",
            "ipv6_id": "ipv6Id",
            "ipv6_gw_id": "ipv6GwId",
            "dhcp": "dhcp",
            "slaac": "slaac",
        }
        for src, dst in field_map.items():
            if self.params.get(src) is not None:
                payload[dst] = self.params[src]

        if existing and net_id is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, network=existing)
                return
            if not self.check_mode:
                resp = self.client.patch(
                    f"/jail/{ctid}/networks/{net_id}", json_body=payload, node=host
                )
            else:
                resp = payload
            self.exit_json(changed=True, network=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(f"/jail/{ctid}/networks", json_body=payload, node=host)
        else:
            resp = payload
        self.exit_json(changed=True, network=resp or payload)


def main() -> None:
    SylveJailNetworkModule()()


if __name__ == "__main__":
    main()
