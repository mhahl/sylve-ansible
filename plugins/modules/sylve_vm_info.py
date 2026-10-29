#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_vm_info
short_description: Gather information about Sylve Bhyve VMs, templates, snapshots, stats, and logs
description:
  - Query Bhyve virtual machines, simple summaries, libvirt domain XML, QEMU guest-agent data, console logs, snapshots, templates, and RRD stats.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  vm:
    description: Optional VM RID or name to query a single VM.
    type: str
  simple:
    description: Use C(/vm/simple) instead of full C(/vm) details.
    type: bool
    default: false
  include_domain:
    description: Include libvirt domain XML (C(/vm/{rid}/domain)) when querying a single VM.
    type: bool
    default: false
  include_guest_agent:
    description: Include QEMU guest agent info (C(/vm/{rid}/guest-agent)) when querying a single VM.
    type: bool
    default: false
  include_logs:
    description: Include console logs (C(/vm/{rid}/logs)) when querying a single VM.
    type: bool
    default: false
  include_snapshots:
    description: Include VM snapshots (C(/vm/{rid}/snapshots)) when querying a single VM.
    type: bool
    default: false
  include_stats:
    description: Include VM stats (C(/vm/{rid}/stats) or C(/vm/{rid}/stats/{step})).
    type: bool
    default: false
  stats_step:
    description: Optional step interval for C(/vm/{rid}/stats/{step}).
    type: str
  include_templates:
    description: Also list VM templates across the cluster/node (C(/vm/templates)).
    type: bool
    default: false
"""

EXAMPLES = r"""
- name: List all VMs across the cluster
  sylve.cloud.sylve_vm_info:
  register: vm_info
"""

RETURN = r"""
vms:
  description: List of matching virtual machines.
  returned: always
  type: list
  elements: dict
templates:
  description: List of VM templates when C(include_templates=true).
  returned: when requested
  type: list
  elements: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveVMInfoModule(SylveModule):
    argument_spec = {
        "vm": {"type": "str"},
        "simple": {"type": "bool", "default": False},
        "include_domain": {"type": "bool", "default": False},
        "include_guest_agent": {"type": "bool", "default": False},
        "include_logs": {"type": "bool", "default": False},
        "include_snapshots": {"type": "bool", "default": False},
        "include_stats": {"type": "bool", "default": False},
        "stats_step": {"type": "str"},
        "include_templates": {"type": "bool", "default": False},
    }

    def run(self) -> None:
        vms: list[dict] = []
        if self.params.get("vm"):
            rid, host, _ = self.client.resolve_vm(self.params["vm"], node=self.node)
            endpoint = f"/vm/simple/{rid}" if self.params["simple"] else f"/vm/{rid}"
            data = self.client.get(endpoint, node=host) or {}
            if isinstance(data, dict):
                data["node"] = host
                if self.params["include_domain"]:
                    data["domain"] = self.client.get(f"/vm/{rid}/domain", node=host)
                if self.params["include_guest_agent"]:
                    data["guest_agent"] = self.client.get(f"/vm/{rid}/guest-agent", node=host)
                if self.params["include_logs"]:
                    data["logs"] = self.client.get(f"/vm/{rid}/logs", node=host)
                if self.params["include_snapshots"]:
                    data["snapshots"] = self.client.get(f"/vm/{rid}/snapshots", node=host)
                if self.params["include_stats"]:
                    step = self.params.get("stats_step")
                    stat_path = f"/vm/{rid}/stats/{step}" if step else f"/vm/{rid}/stats"
                    data["stats"] = self.client.get(stat_path, node=host)
                vms.append(data)
        else:
            endpoint = "/vm/simple" if self.params["simple"] else "/vm"
            for host, items in self.client.fan_out_get(endpoint, node=self.node):
                for item in items if isinstance(items, list) else []:
                    if isinstance(item, dict):
                        row = dict(item)
                        row.setdefault("node", host)
                        vms.append(row)

        templates: list[dict] = []
        if self.params["include_templates"]:
            for host, items in self.client.fan_out_get("/vm/templates", node=self.node):
                for t in items if isinstance(items, list) else []:
                    if isinstance(t, dict):
                        row = dict(t)
                        row.setdefault("node", host)
                        templates.append(row)

        self.exit_json(changed=False, vms=vms, templates=templates)


def main() -> None:
    SylveVMInfoModule()()


if __name__ == "__main__":
    main()
