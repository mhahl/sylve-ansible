#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_zfs_info
short_description: Gather information about Sylve ZFS pools, datasets, snapshots, scrubs, and dashboard metrics
description:
- Query ZFS pools, pool status, scrub runs, scrub schedules, disk usage, datasets, paginated datasets, periodic snapshot schedules,
  and dashboard metrics.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  gather:
    description: List of ZFS sections to query.
    type: list
    elements: str
    default:
    - pools
    - datasets
    - periodic_snapshots
    required: false
  all_pools:
    description: Include pools not marked usable in Sylve settings.
    type: bool
    default: false
    required: false
  pool_guid:
    description: Pool GUID to fetch detailed status (C(/zfs/pools/{guid}/status)) and scrub runs (C(/zfs/pools/{guid}/scrub/runs)).
    type: str
    required: false
  dataset_type:
    description: Filter datasets by type (C(FILESYSTEM), C(VOLUME), C(SNAPSHOT), C(ALL)).
    type: str
    required: false
  paginated_params:
    description: Query parameters for C(/zfs/datasets/paginated).
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
- name: Gather ZFS pools and datasets
  sylve.cloud.sylve_zfs_info:
    gather: [pools, datasets, disks_usage, scrub_schedules]
  register: zfs_info

- name: Gather information about Sylve ZFS pools, datasets, snapshots, scrubs, and dashboard metrics on a specific node using a named context
  sylve.cloud.sylve_zfs_info:
    context: prod
    node: node1.lan
    gather: [pools, datasets]
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
zfs_info:
  description: Dictionary of gathered ZFS data.
  returned: always
  type: dict
  sample: '{"pools": [{"name": "zroot", "state": "ONLINE"}]}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveZFSInfoModule(SylveModule):
    argument_spec = {
        "gather": {
            "type": "list",
            "elements": "str",
            "default": ["pools", "datasets", "periodic_snapshots"],
        },
        "all_pools": {"type": "bool", "default": False},
        "pool_guid": {"type": "str"},
        "dataset_type": {"type": "str"},
        "paginated_params": {"type": "dict"},
    }

    def run(self) -> None:
        gather = set(self.params.get("gather") or [])
        out: dict = {}

        if "pools" in gather or "all" in gather:
            params = {"all": True} if self.params["all_pools"] else None
            out["pools"] = self.client.get("/zfs/pools", params=params, node=self.node)

        if self.params.get("pool_guid"):
            pguid = self.params["pool_guid"]
            out["pool_status"] = self.client.get(f"/zfs/pools/{pguid}/status", node=self.node)
            out["pool_scrub_runs"] = self.client.get(
                f"/zfs/pools/{pguid}/scrub/runs", node=self.node
            )

        if "disks_usage" in gather or "all" in gather:
            out["disks_usage"] = self.client.get("/zfs/pools/disks-usage", node=self.node)

        if "scrub_schedules" in gather or "all" in gather:
            out["scrub_schedules"] = self.client.get(
                "/zfs/pools/scrub/schedules", node=self.node
            )

        if "datasets" in gather or "all" in gather:
            params = (
                {"type": self.params["dataset_type"].upper()}
                if self.params.get("dataset_type")
                else None
            )
            out["datasets"] = self.client.get("/zfs/datasets", params=params, node=self.node)

        if "datasets_paginated" in gather or self.params.get("paginated_params"):
            out["datasets_paginated"] = self.client.get(
                "/zfs/datasets/paginated",
                params=self.params.get("paginated_params"),
                node=self.node,
            )

        if "periodic_snapshots" in gather or "all" in gather:
            out["periodic_snapshots"] = self.client.get(
                "/zfs/datasets/snapshot/periodic", node=self.node
            )

        if "dashboard" in gather or "all" in gather:
            out["dashboard_snapshot"] = self.client.get(
                "/zfs/dashboard/snapshot", node=self.node
            )
            out["dashboard_history"] = self.client.get(
                "/zfs/dashboard/history", node=self.node
            )
            out["dashboard_delta"] = self.client.get(
                "/zfs/dashboard/history/delta", node=self.node
            )

        self.exit_json(changed=False, zfs_info=out)


def main() -> None:
    SylveZFSInfoModule()()


if __name__ == "__main__":
    main()
