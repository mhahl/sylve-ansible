#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_jail_snapshot
short_description: Manage ZFS snapshots for a Sylve FreeBSD jail
description:
- Create, roll back to, or delete ZFS snapshots for a FreeBSD jail.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired snapshot state.
    type: str
    choices:
    - present
    - absent
    - rolled_back
    default: present
    required: false
  jail:
    description: Jail CTID or name.
    type: str
    required: true
  snapshot_id:
    description: Snapshot numeric ID.
    type: int
    required: false
  name:
    description: Snapshot name.
    type: str
    required: false
  description:
    description: Snapshot description.
    type: str
    default: ''
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
- name: Create a snapshot of jail app-01
  sylve.cloud.sylve_jail_snapshot:
    jail: app-01
    name: pre-deploy
    state: present

- name: Manage ZFS snapshots for a Sylve FreeBSD jail on a specific node using a named context
  sylve.cloud.sylve_jail_snapshot:
    context: prod
    node: node1.lan
    jail: app-01
    name: pre-deploy
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
snapshot:
  description: Jail snapshot details.
  returned: always
  type: dict
  sample: '{"id": 5, "name": "pre-deploy"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveJailSnapshotModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "rolled_back"],
            "default": "present",
        },
        "jail": {"type": "str", "required": True},
        "snapshot_id": {"type": "int"},
        "name": {"type": "str"},
        "description": {"type": "str", "default": ""},
    }

    def run(self) -> None:
        ctid, host, _ = self.client.resolve_jail(self.params["jail"], node=self.node)
        snaps = self.client.get(f"/jail/{ctid}/snapshots", node=host) or []
        snap_id = self.params.get("snapshot_id")
        name = self.params.get("name")
        existing = None
        for s in snaps if isinstance(snaps, list) else []:
            if not isinstance(s, dict):
                continue
            if snap_id is not None and s.get("id") == snap_id:
                existing = s
                break
            if name and name in (s.get("name"), s.get("snapshotName")):
                existing = s
                snap_id = s.get("id")
                break

        state = self.params["state"]
        if state == "absent":
            if snap_id is None:
                self.exit_json(changed=False, snapshot={})
                return
            if not self.check_mode:
                self.client.delete(f"/jail/{ctid}/snapshots/{snap_id}", node=host)
            self.exit_json(changed=True, snapshot=existing or {"id": snap_id})
            return

        if state == "rolled_back":
            if snap_id is None:
                self.fail_json(msg="Snapshot not found for rollback.")
            if not self.check_mode:
                self.client.post(f"/jail/{ctid}/snapshots/{snap_id}/rollback", node=host)
            self.exit_json(changed=True, snapshot=existing or {"id": snap_id})
            return

        if existing:
            self.exit_json(changed=False, snapshot=existing)
            return

        if not name:
            self.fail_json(msg="'name' is required when creating a jail snapshot.")
        body = {"name": name, "description": self.params["description"]}
        if not self.check_mode:
            resp = self.client.post(f"/jail/{ctid}/snapshots", json_body=body, node=host)
        else:
            resp = body
        self.exit_json(changed=True, snapshot=resp or body)


def main() -> None:
    SylveJailSnapshotModule()()


if __name__ == "__main__":
    main()
