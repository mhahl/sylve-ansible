#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_firewall
short_description: Manage Sylve PF firewall traffic rules, NAT rules, and advanced settings
description:
  - Create, update, reorder, delete, or bulk-delete PF firewall traffic and NAT rules, or update/preview advanced PF settings.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  rule_type:
    description: Firewall component to manage.
    type: str
    choices: [traffic, nat, advanced]
    default: traffic
  state:
    description: Desired state or operation.
    type: str
    choices: [present, absent, reordered, preview]
    default: present
  rule_id:
    description: Numeric rule ID.
    type: int
    aliases: [id]
  ids:
    description: List of rule IDs for bulk deletion (C(state=absent)) or reordering (C(state=reordered)).
    type: list
    elements: int
  name:
    description: Rule name.
    type: str
  priority:
    description: Rule evaluation priority.
    type: int
  action:
    description: Traffic rule action (e.g. C(pass), C(block)).
    type: str
  nat_type:
    description: NAT rule type (e.g. C(nat), C(rdr), C(binat)) when C(rule_type=nat).
    type: str
  direction:
    description: Packet direction (C(in) or C(out)).
    type: str
  protocol:
    description: Protocol (e.g. C(tcp), C(udp), C(icmp), C(any)).
    type: str
  interface:
    description: Network interface.
    type: str
  source:
    description: Source address/object.
    type: str
  destination:
    description: Destination address/object.
    type: str
  dst_ports:
    description: Destination port(s).
    type: str
  enabled:
    description: Enable the rule.
    type: bool
    default: true
  data:
    description: Additional raw request fields (or full body for C(rule_type=advanced)).
    type: dict
"""

EXAMPLES = r"""
- name: Allow inbound HTTPS traffic
  sylve.cloud.sylve_firewall:
    rule_type: traffic
    name: allow-https
    action: pass
    direction: in
    protocol: tcp
    destination: any
    dst_ports: "443"
    enabled: true
    state: present
"""

RETURN = r"""
firewall:
  description: Firewall rule or settings result.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveFirewallModule(SylveModule):
    argument_spec = {
        "rule_type": {
            "type": "str",
            "choices": ["traffic", "nat", "advanced"],
            "default": "traffic",
        },
        "state": {
            "type": "str",
            "choices": ["present", "absent", "reordered", "preview"],
            "default": "present",
        },
        "rule_id": {"type": "int", "aliases": ["id"]},
        "ids": {"type": "list", "elements": "int"},
        "name": {"type": "str"},
        "priority": {"type": "int"},
        "action": {"type": "str"},
        "nat_type": {"type": "str"},
        "direction": {"type": "str"},
        "protocol": {"type": "str"},
        "interface": {"type": "str"},
        "source": {"type": "str"},
        "destination": {"type": "str"},
        "dst_ports": {"type": "str"},
        "enabled": {"type": "bool", "default": True},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        rtype = self.params["rule_type"]
        state = self.params["state"]
        payload: dict = dict(self.params.get("data") or {})

        if rtype == "advanced":
            if state == "preview":
                res = self.client.post(
                    "/network/firewall/advanced/preview", json_body=payload, node=self.node
                )
                self.exit_json(changed=False, firewall=res or {})
                return
            current = self.client.get("/network/firewall/advanced", node=self.node) or {}
            if isinstance(current, dict) and not self.subset_differs(payload, current):
                self.exit_json(changed=False, firewall=current)
                return
            if not self.check_mode:
                resp = self.client.put(
                    "/network/firewall/advanced", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, firewall=resp or payload)
            return

        base_path = f"/network/firewall/{rtype}"

        if state == "reordered":
            body = payload or {"ids": self.params.get("ids") or []}
            if not self.check_mode:
                resp = self.client.put(f"{base_path}/reorder", json_body=body, node=self.node)
            else:
                resp = body
            self.exit_json(changed=True, firewall=resp or body)
            return

        if state == "absent" and self.params.get("ids"):
            body = {"ids": self.params["ids"]}
            if not self.check_mode:
                self.client.delete(base_path, json_body=body, node=self.node)
            self.exit_json(changed=True, firewall=body)
            return

        rules = self.client.get(base_path, node=self.node) or []
        rid = self.params.get("rule_id")
        name = self.params.get("name")
        existing = None
        for r in rules if isinstance(rules, list) else []:
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
                self.exit_json(changed=False, firewall={})
                return
            if not self.check_mode:
                self.client.delete(f"{base_path}/{rid}", node=self.node)
            self.exit_json(changed=True, firewall=existing or {"id": rid})
            return

        field_map = {
            "name": "name",
            "priority": "priority",
            "action": "action",
            "nat_type": "natType",
            "direction": "direction",
            "protocol": "protocol",
            "interface": "interface",
            "source": "sourceRaw",
            "destination": "destRaw",
            "dst_ports": "dstPortsRaw",
            "enabled": "enabled",
        }
        for src, dst in field_map.items():
            if self.params.get(src) is not None:
                payload[dst] = self.params[src]

        if existing and rid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, firewall=existing)
                return
            if not self.check_mode:
                resp = self.client.put(f"{base_path}/{rid}", json_body=payload, node=self.node)
            else:
                resp = payload
            self.exit_json(changed=True, firewall=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(base_path, json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, firewall=resp or payload)


def main() -> None:
    SylveFirewallModule()()


if __name__ == "__main__":
    main()
