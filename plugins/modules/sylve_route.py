#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_route
short_description: Manage Sylve static network routes
description:
  - Create, update, or delete static network routes on a Sylve node.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired static route state.
    type: str
    choices: [present, absent]
    default: present
  route_id:
    description: Numeric static route ID.
    type: int
    aliases: [id]
  name:
    description: Route name.
    type: str
  family:
    description: Address family (C(inet) or C(inet6)).
    type: str
  destination_type:
    description: Destination type (e.g. C(network), C(host)).
    type: str
  destination:
    description: Destination CIDR or object.
    type: str
  gateway:
    description: Next-hop gateway IP or object.
    type: str
  interface:
    description: Outgoing network interface.
    type: str
  enabled:
    description: Enable the static route.
    type: bool
    default: true
  data:
    description: Additional raw fields merged into the request payload.
    type: dict
"""

EXAMPLES = r"""
- name: Add a static route to 10.20.0.0/16
  sylve.cloud.sylve_route:
    name: corp-vpn
    family: inet
    destination_type: network
    destination: 10.20.0.0/16
    gateway: 192.168.1.254
    enabled: true
    state: present
"""

RETURN = r"""
route:
  description: Static route details.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveRouteModule(SylveModule):
    argument_spec = {
        "state": {"type": "str", "choices": ["present", "absent"], "default": "present"},
        "route_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "family": {"type": "str"},
        "destination_type": {"type": "str"},
        "destination": {"type": "str"},
        "gateway": {"type": "str"},
        "interface": {"type": "str"},
        "enabled": {"type": "bool", "default": True},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        routes = self.client.get("/network/route", node=self.node) or []
        rid = self.params.get("route_id")
        name = self.params.get("name")
        existing = None
        for r in routes if isinstance(routes, list) else []:
            if not isinstance(r, dict):
                continue
            if rid is not None and r.get("id") == rid:
                existing = r
                break
            if name and str(r.get("name") or "").lower() == name.lower():
                existing = r
                rid = int(r["id"])
                break

        if self.params["state"] == "absent":
            if rid is None:
                self.exit_json(changed=False, route={})
                return
            if not self.check_mode:
                self.client.delete(f"/network/route/{rid}", node=self.node)
            self.exit_json(changed=True, route=existing or {"id": rid})
            return

        payload: dict = dict(self.params.get("data") or {})
        field_map = {
            "name": "name",
            "family": "family",
            "destination_type": "destinationType",
            "destination": "destinationRaw",
            "gateway": "gatewayRaw",
            "interface": "interface",
            "enabled": "enabled",
        }
        for src, dst in field_map.items():
            if self.params.get(src) is not None:
                payload[dst] = self.params[src]

        if existing and rid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, route=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/network/route/{rid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, route=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/network/route", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, route=resp or payload)


def main() -> None:
    SylveRouteModule()()


if __name__ == "__main__":
    main()
