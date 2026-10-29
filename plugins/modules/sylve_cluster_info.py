#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_cluster_info
short_description: Gather information about Sylve cluster status, nodes, telemetry, and audit logs
description:
- Query cluster status, join key, nodes, cluster resources, cluster notes, node telemetry (CPU, RAM, swap, history), and audit
  logs.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  gather:
    description: Sections of cluster and node information to retrieve.
    type: list
    elements: str
    default:
    - cluster
    - nodes
    - resources
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
- name: Gather cluster status, nodes, and node telemetry
  sylve.cloud.sylve_cluster_info:
    gather: [cluster, nodes, resources, node_telemetry, audit_records]
  register: cluster_info

- name: Gather information about Sylve cluster status, nodes, telemetry, and audit logs on a specific node using a named context
  sylve.cloud.sylve_cluster_info:
    context: prod
    node: node1.lan
    gather: [cluster, nodes, resources]
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
cluster_info:
  description: Dictionary of gathered cluster and node data.
  returned: always
  type: dict
  sample: '{"nodes": [{"hostname": "node1.lan", "status": "online"}]}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveClusterInfoModule(SylveModule):
    argument_spec = {
        "gather": {
            "type": "list",
            "elements": "str",
            "default": ["cluster", "nodes", "resources"],
        },
    }

    def run(self) -> None:
        gather = set(self.params.get("gather") or [])
        out: dict = {}

        if "cluster" in gather or "all" in gather:
            out["cluster"] = self.client.get("/cluster")

        if "join_key" in gather or "all" in gather:
            out["join_key"] = self.client.get("/cluster/join-key")

        if "nodes" in gather or "all" in gather:
            out["nodes"] = self.client.get_cluster_nodes(refresh=True)

        if "resources" in gather or "all" in gather:
            out["resources"] = self.client.get_cluster_resources(refresh=True)

        if "cluster_notes" in gather or "all" in gather:
            out["cluster_notes"] = self.client.get("/cluster/notes")

        if "node_telemetry" in gather or "all" in gather:
            out["node"] = self.client.get("/info/node", node=self.node)
            out["basic"] = self.client.get("/info/basic", node=self.node)
            out["cpu"] = self.client.get("/info/cpu", node=self.node)
            out["ram"] = self.client.get("/info/ram", node=self.node)
            out["swap"] = self.client.get("/info/swap", node=self.node)
            out["host_notes"] = self.client.get("/info/notes", node=self.node)

        if "node_history" in gather or "all" in gather:
            out["cpu_historical"] = self.client.get("/info/cpu/historical", node=self.node)
            out["ram_historical"] = self.client.get("/info/ram/historical", node=self.node)
            out["swap_historical"] = self.client.get("/info/swap/historical", node=self.node)
            out["network_historical"] = self.client.get(
                "/info/network-interfaces/historical", node=self.node
            )
            out["summary_history"] = self.client.get("/info/summary/history", node=self.node)
            out["summary_delta"] = self.client.get(
                "/info/summary/history/delta", node=self.node
            )

        if "audit_records" in gather or "all" in gather:
            out["audit_records"] = self.client.get("/info/audit-records", node=self.node)

        self.exit_json(changed=False, cluster_info=out)


def main() -> None:
    SylveClusterInfoModule()()


if __name__ == "__main__":
    main()
