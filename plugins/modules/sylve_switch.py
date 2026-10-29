#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_switch
short_description: Manage Sylve standard and manual network switches
description:
- Create, update, delete, or synchronize standard and manual FreeBSD bridge network switches on Sylve.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired switch state or action.
    type: str
    choices:
    - present
    - absent
    - synced
    default: present
    required: false
  switch_id:
    description: Numeric switch ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: Switch name.
    type: str
    required: false
  type:
    description: Switch type (C(standard) or C(manual)).
    type: str
    choices:
    - standard
    - manual
    default: standard
    required: false
  bridge:
    description: Existing host bridge interface name when C(type=manual) (e.g. C(bridge0)).
    type: str
    required: false
  bridge_mac:
    description: Bridge MAC source (sent as C(bridgeMac)). Required by the API when creating a standard switch.
    type: dict
    required: false
    suboptions:
      mode:
        description: MAC source mode (e.g. C(port), as used by switches created in the web UI).
        type: str
      port:
        description: Member port name to derive the bridge MAC from (when C(mode=port)).
        type: str
      mac_object_id:
        description: MAC network object ID (for object-backed modes).
        type: int
  ports:
    description: List of member interface names when C(type=standard).
    type: list
    elements: str
    required: false
  private:
    description: Host-only private switch flag.
    type: bool
    default: false
    required: false
  dhcp:
    description: Enable DHCP client on the switch bridge.
    type: bool
    default: false
    required: false
  mtu:
    description: Switch MTU.
    type: int
    default: 1500
    required: false
  vlan:
    description: VLAN tag.
    type: int
    default: 0
    required: false
  vlan_filtering:
    description: Enable FreeBSD bridge VLAN filtering.
    type: bool
    default: false
    required: false
  default_access_vlan:
    description: Default access VLAN when VLAN filtering is enabled.
    type: int
    default: 0
    required: false
  address:
    description: Optional IPv4 CIDR address or network object.
    type: str
    required: false
  data:
    description: Additional raw fields merged into the request body.
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
- name: Create a standard switch on em0
  sylve.cloud.sylve_switch:
    name: lan0
    type: standard
    ports: [em0]
    mtu: 1500
    state: present

- name: Manage Sylve standard and manual network switches on a specific node using a named context
  sylve.cloud.sylve_switch:
    context: prod
    node: node1.lan
    name: lan0
    type: standard
    ports: [em0]
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
switch:
  description: Switch details.
  returned: always
  type: dict
  sample: '{"id": 1, "name": "lan0", "type": "standard"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveSwitchModule(SylveModule):
    argument_spec = {
        "state": {"type": "str", "choices": ["present", "absent", "synced"], "default": "present"},
        "switch_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "type": {"type": "str", "choices": ["standard", "manual"], "default": "standard"},
        "bridge": {"type": "str"},
        "bridge_mac": {
            "type": "dict",
            "options": {
                "mode": {"type": "str"},
                "port": {"type": "str"},
                "mac_object_id": {"type": "int"},
            },
        },
        "ports": {"type": "list", "elements": "str"},
        "private": {"type": "bool", "default": False},
        "dhcp": {"type": "bool", "default": False},
        "mtu": {"type": "int", "default": 1500},
        "vlan": {"type": "int", "default": 0},
        "vlan_filtering": {"type": "bool", "default": False},
        "default_access_vlan": {"type": "int", "default": 0},
        "address": {"type": "str"},
        "data": {"type": "dict"},
    }

    def _find_switch(self) -> tuple[int | None, str, dict]:
        all_sw = self.client.get("/network/switch", node=self.node) or {}
        sid = self.params.get("switch_id")
        name = self.params.get("name")
        pref_type = self.params["type"]
        types = [pref_type, "manual" if pref_type == "standard" else "standard"]
        if isinstance(all_sw, dict):
            for stype in types:
                for sw in all_sw.get(stype) or []:
                    if not isinstance(sw, dict):
                        continue
                    if sid is not None and sw.get("id") == sid:
                        return int(sid), stype, sw
                    if name and str(sw.get("name") or "").lower() == name.lower():
                        return int(sw["id"]), stype, sw
        return None, pref_type, {}

    def run(self) -> None:
        state = self.params["state"]
        if state == "synced":
            if not self.check_mode:
                self.client.post("/network/switch/sync", node=self.node)
            self.exit_json(changed=True, switch={})
            return

        sid, stype, existing = self._find_switch()
        if state == "absent":
            if sid is None:
                self.exit_json(changed=False, switch={})
                return
            if not self.check_mode:
                self.client.delete(f"/network/switch/{stype}/{sid}", node=self.node)
            self.exit_json(changed=True, switch=existing)
            return

        if stype == "manual":
            if existing:
                self.exit_json(changed=False, switch=existing)
                return
            if not self.params.get("name") or not self.params.get("bridge"):
                self.fail_json(msg="Both 'name' and 'bridge' are required for manual switches.")
            body = {"name": self.params["name"], "bridge": self.params["bridge"]}
            if self.params.get("data"):
                body.update(self.params["data"])
            if not self.check_mode:
                resp = self.client.post("/network/switch/manual", json_body=body, node=self.node)
            else:
                resp = body
            self.exit_json(changed=True, switch=resp or body)
            return

        body = {
            "name": self.params.get("name") or existing.get("name"),
            "private": self.params["private"],
            "dhcp": self.params["dhcp"],
            "mtu": self.params["mtu"],
            "ports": self.params.get("ports") or [],
            "vlan": self.params["vlan"],
            "vlanFiltering": self.params["vlan_filtering"],
            "defaultAccessVlan": self.params["default_access_vlan"],
        }
        if self.params.get("address") is not None:
            body["address"] = self.params["address"]
        if self.params.get("bridge_mac") is not None:
            bm = self.params["bridge_mac"] or {}
            body["bridgeMac"] = {
                "mode": bm.get("mode"),
                "port": bm.get("port"),
                "macObjectId": bm.get("mac_object_id"),
            }
        if self.params.get("data"):
            body.update(self.params["data"])

        if existing and sid is not None:
            existing_ports = [
                str(p.get("name") if isinstance(p, dict) else p)
                for p in (existing.get("ports") or [])
            ]
            compare_current = dict(
                existing,
                ports=existing_ports,
                private=bool(existing.get("private", False)),
                dhcp=bool(existing.get("dhcp", False)),
                mtu=int(existing.get("mtu") or 1500),
                vlan=int(existing.get("vlan") or 0),
                vlanFiltering=bool(existing.get("vlanFiltering", False)),
                defaultAccessVlan=int(existing.get("defaultAccessVlan") or 0),
                bridgeMac={
                    "mode": existing.get("bridgeMacMode"),
                    "port": existing.get("bridgeMacSourcePort"),
                    "macObjectId": existing.get("bridgeMacObjectId"),
                },
            )
            if not self.subset_differs(body, compare_current):
                self.exit_json(changed=False, switch=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/network/switch/standard/{sid}", json_body=body, node=self.node
                )
            else:
                resp = body
            self.exit_json(changed=True, switch=resp or body)
            return

        if not self.check_mode:
            resp = self.client.post("/network/switch/standard", json_body=body, node=self.node)
        else:
            resp = body
        self.exit_json(changed=True, switch=resp or body)


def main() -> None:
    SylveSwitchModule()()


if __name__ == "__main__":
    main()
