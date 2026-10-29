#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
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
    choices:
    - present
    - absent
    default: present
    required: false
  route_id:
    description: Numeric static route ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: Route name.
    type: str
    required: false
  family:
    description: Address family (C(inet) or C(inet6)).
    type: str
    required: false
  destination_type:
    description: Destination type (e.g. C(network), C(host)).
    type: str
    required: false
  destination:
    description: Destination CIDR or object.
    type: str
    required: false
  gateway:
    description: Next-hop gateway IP or object.
    type: str
    required: false
  interface:
    description: Outgoing network interface.
    type: str
    required: false
  enabled:
    description: Enable the static route.
    type: bool
    default: true
    required: false
  data:
    description: Additional raw fields merged into the request payload.
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
- name: Add a static route to 10.20.0.0/16
  sylve.cloud.sylve_route:
    name: corp-vpn
    family: inet
    destination_type: network
    destination: 10.20.0.0/16
    gateway: 192.168.1.254
    enabled: true
    state: present

- name: Manage Sylve static network routes on a specific node using a named context
  sylve.cloud.sylve_route:
    context: prod
    node: node1.lan
    name: corp-vpn
    destination: 10.20.0.0/16
    gateway: 192.168.1.254
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
route:
  description: Static route details.
  returned: always
  type: dict
  sample: '{"id": 1, "name": "corp-vpn", "destinationRaw": "10.20.0.0/16"}'
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
