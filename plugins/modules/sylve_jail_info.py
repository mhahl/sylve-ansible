#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_jail_info
short_description: Gather information about Sylve FreeBSD jails, bootstraps, templates, and stats
description:
- Query FreeBSD jails, simple summaries, live guest-info, root mountpoints, ZFS sources, logs, stats, snapshots, bootstraps,
  and templates.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  jail:
    description: Optional jail CTID or name to query a single jail.
    type: str
    required: false
  simple:
    description: Use C(/jail/simple) instead of full C(/jail) details.
    type: bool
    default: false
    required: false
  include_state:
    description: Fetch C(/jail/{ctid}/state) when querying a single jail.
    type: bool
    default: false
    required: false
  include_guest_info:
    description: Fetch live OS/network info (C(/jail/{ctid}/guest-info)) when querying a single jail.
    type: bool
    default: false
    required: false
  include_root_mountpoint:
    description: Fetch root mountpoint (C(/jail/{ctid}/root-mountpoint)) when querying a single jail.
    type: bool
    default: false
    required: false
  include_logs:
    description: Fetch console logs (C(/jail/{ctid}/logs)) when querying a single jail.
    type: bool
    default: false
    required: false
  include_snapshots:
    description: Fetch snapshots (C(/jail/{ctid}/snapshots)) when querying a single jail.
    type: bool
    default: false
    required: false
  include_stats:
    description: Fetch jail stats (C(/jail/{ctid}/stats) or C(/jail/{ctid}/stats/{step})).
    type: bool
    default: false
    required: false
  stats_step:
    description: Step parameter for C(/jail/{ctid}/stats/{step}).
    type: str
    required: false
  include_zfs_sources:
    description: Include available jail ZFS sources (C(/jail/zfs-sources)).
    type: bool
    default: false
    required: false
  bootstrap_pool:
    description: ZFS pool name to list pkgbase jail bootstraps from (C(/jail/bootstraps)).
    type: str
    required: false
  include_templates:
    description: Include jail templates (C(/jail/templates)).
    type: bool
    default: false
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
- name: List all jails across the cluster
  sylve.cloud.sylve_jail_info:
  register: jail_info

- name: Gather information about Sylve FreeBSD jails, bootstraps, templates, and stats on a specific node using a named context
  sylve.cloud.sylve_jail_info:
    context: prod
    node: node1.lan
    bootstrap_pool: zroot
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
jails:
  description: List of matching jails.
  returned: always
  type: list
  sample: '[{"ctId": 201, "name": "app-01", "state": "RUNNING"}]'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveJailInfoModule(SylveModule):
    argument_spec = {
        "jail": {"type": "str"},
        "simple": {"type": "bool", "default": False},
        "include_state": {"type": "bool", "default": False},
        "include_guest_info": {"type": "bool", "default": False},
        "include_root_mountpoint": {"type": "bool", "default": False},
        "include_logs": {"type": "bool", "default": False},
        "include_snapshots": {"type": "bool", "default": False},
        "include_stats": {"type": "bool", "default": False},
        "stats_step": {"type": "str"},
        "include_zfs_sources": {"type": "bool", "default": False},
        "bootstrap_pool": {"type": "str"},
        "include_templates": {"type": "bool", "default": False},
    }

    def run(self) -> None:
        jails: list[dict] = []
        if self.params.get("jail"):
            ctid, host, summary = self.client.resolve_jail(self.params["jail"], node=self.node)
            endpoint = f"/jail/simple/{ctid}" if self.params["simple"] else f"/jail/{ctid}"
            data = self.client.get(endpoint, node=host) or {}
            if isinstance(data, dict):
                data["node"] = host
                data.setdefault("state", summary.get("state"))
                if self.params["include_state"]:
                    data["live_state"] = self.client.get(f"/jail/{ctid}/state", node=host)
                if self.params["include_guest_info"]:
                    data["guest_info"] = self.client.get(f"/jail/{ctid}/guest-info", node=host)
                if self.params["include_root_mountpoint"]:
                    data["root_mountpoint"] = self.client.get(
                        f"/jail/{ctid}/root-mountpoint", node=host
                    )
                if self.params["include_logs"]:
                    data["logs"] = self.client.get(f"/jail/{ctid}/logs", node=host)
                if self.params["include_snapshots"]:
                    data["snapshots"] = self.client.get(f"/jail/{ctid}/snapshots", node=host)
                if self.params["include_stats"]:
                    step = self.params.get("stats_step")
                    stat_path = f"/jail/{ctid}/stats/{step}" if step else f"/jail/{ctid}/stats"
                    data["stats"] = self.client.get(stat_path, node=host)
                jails.append(data)
        else:
            endpoint = "/jail/simple" if self.params["simple"] else "/jail"
            for host, items in self.client.fan_out_get(endpoint, node=self.node):
                for item in items if isinstance(items, list) else []:
                    if isinstance(item, dict):
                        row = dict(item)
                        row.setdefault("node", host)
                        jails.append(row)

        bootstraps: list[dict] = []
        if self.params.get("bootstrap_pool"):
            for host, items in self.client.fan_out_get(
                "/jail/bootstraps",
                params={"pool": self.params["bootstrap_pool"]},
                node=self.node,
            ):
                for b in items if isinstance(items, list) else []:
                    if isinstance(b, dict):
                        row = dict(b)
                        row.setdefault("node", host)
                        bootstraps.append(row)

        templates: list[dict] = []
        if self.params["include_templates"]:
            for host, items in self.client.fan_out_get("/jail/templates", node=self.node):
                for t in items if isinstance(items, list) else []:
                    if isinstance(t, dict):
                        row = dict(t)
                        row.setdefault("node", host)
                        templates.append(row)

        zfs_sources = None
        if self.params["include_zfs_sources"]:
            zfs_sources = self.client.get("/jail/zfs-sources", node=self.node)

        self.exit_json(
            changed=False,
            jails=jails,
            bootstraps=bootstraps,
            templates=templates,
            zfs_sources=zfs_sources,
        )


def main() -> None:
    SylveJailInfoModule()()


if __name__ == "__main__":
    main()
