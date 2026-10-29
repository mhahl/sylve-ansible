#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_network_info
short_description: Gather information about Sylve network interfaces, switches, routes, DHCP, firewall, and WireGuard
description:
- Query network interfaces, L3 configurations, pending L3 changes, global network config, switches, switch sync status, static
  routes, network objects, DHCP config/ranges/leases, firewall rules/counters/rendered/live logs/route suggestions, and WireGuard.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  gather:
    description: List of network sections to query.
    type: list
    elements: str
    default:
    - interfaces
    - switches
    - routes
    - objects
    required: false
  nat_rule_id:
    description: Optional NAT rule ID to fetch route suggestions for (C(/network/firewall/nat/{id}/route-suggestions)).
    type: int
    required: false
  log_params:
    description: Optional query parameters for C(/network/firewall/logs/live).
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
- name: Gather switches and interfaces across the cluster
  sylve.cloud.sylve_network_info:
    gather: [interfaces, switches, dhcp, firewall, wireguard]
  register: net_info

- name: Gather information about Sylve network interfaces, switches, routes, DHCP, firewall, and WireGuard on a specific node using a named context
  sylve.cloud.sylve_network_info:
    context: prod
    node: node1.lan
    gather: [interfaces, switches, routes, objects]
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
network_info:
  description: Dictionary of gathered network resources.
  returned: always
  type: dict
  sample: '{"switches": {"standard": [{"id": 1, "name": "lan0"}]}}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveNetworkInfoModule(SylveModule):
    argument_spec = {
        "gather": {
            "type": "list",
            "elements": "str",
            "default": ["interfaces", "switches", "routes", "objects"],
        },
        "nat_rule_id": {"type": "int"},
        "log_params": {"type": "dict"},
    }

    def run(self) -> None:
        gather = set(self.params.get("gather") or [])
        out: dict = {}

        if "interfaces" in gather or "all" in gather:
            out["interfaces"] = self.client.get("/network/interface", node=self.node)
            out["l3"] = self.client.get("/network/interface/l3", node=self.node)
            out["l3_pending"] = self.client.get("/network/interface/l3/pending", node=self.node)
            out["global_config"] = self.client.get("/network/global-config", node=self.node)

        if "switches" in gather or "all" in gather:
            out["switches"] = self.client.get("/network/switch", node=self.node)
            out["switch_sync"] = self.client.get("/network/switch/sync", node=self.node)

        if "routes" in gather or "all" in gather:
            out["routes"] = self.client.get("/network/route", node=self.node)

        if "objects" in gather or "all" in gather:
            out["objects"] = self.client.get("/network/object", node=self.node)

        if "dhcp" in gather or "all" in gather:
            out["dhcp_config"] = self.client.get("/network/dhcp/config", node=self.node)
            out["dhcp_ranges"] = self.client.get("/network/dhcp/range", node=self.node)
            out["dhcp_leases"] = self.client.get("/network/dhcp/lease", node=self.node)

        if "firewall" in gather or "all" in gather:
            out["firewall_traffic"] = self.client.get(
                "/network/firewall/traffic", node=self.node
            )
            out["firewall_traffic_counters"] = self.client.get(
                "/network/firewall/traffic/counters", node=self.node
            )
            out["firewall_nat"] = self.client.get("/network/firewall/nat", node=self.node)
            out["firewall_nat_counters"] = self.client.get(
                "/network/firewall/nat/counters", node=self.node
            )
            out["firewall_advanced"] = self.client.get(
                "/network/firewall/advanced", node=self.node
            )
            out["firewall_rendered"] = self.client.get(
                "/network/firewall/advanced/rendered", node=self.node
            )
            if self.params.get("nat_rule_id") is not None:
                nid = self.params["nat_rule_id"]
                out["nat_route_suggestions"] = self.client.get(
                    f"/network/firewall/nat/{nid}/route-suggestions", node=self.node
                )

        if "firewall_logs" in gather:
            out["firewall_logs"] = self.client.get(
                "/network/firewall/logs/live",
                params=self.params.get("log_params"),
                node=self.node,
            )

        if "wireguard" in gather or "all" in gather:
            out["wireguard_server"] = self.client.get(
                "/network/wireguard/server", node=self.node
            )
            out["wireguard_clients"] = self.client.get(
                "/network/wireguard/clients", node=self.node
            )

        self.exit_json(changed=False, network_info=out)


def main() -> None:
    SylveNetworkInfoModule()()


if __name__ == "__main__":
    main()
