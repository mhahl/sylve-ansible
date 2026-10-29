#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_backup_target
short_description: Manage Sylve cluster backup targets, validation, datasets, and restores
description:
- Create, update, validate, delete, or restore from cluster backup targets, and inspect target datasets/metadata/readiness.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired backup target state or action.
    type: str
    choices:
    - present
    - absent
    - validated
    - restored
    - query
    default: present
    required: false
  target_id:
    description: Backup target numeric ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: Backup target name.
    type: str
    required: false
  ssh_host:
    description: Remote SSH host (e.g. C(backup@host)).
    type: str
    required: false
  ssh_port:
    description: Remote SSH port.
    type: int
    required: false
  backup_root:
    description: Remote ZFS dataset root path.
    type: str
    required: false
  description:
    description: Backup target description.
    type: str
    required: false
  enabled:
    description: Enable the backup target.
    type: bool
    default: true
    required: false
  dataset_params:
    description: Query parameters when inspecting datasets/snapshots/metadata in C(state=query).
    type: dict
    required: false
  data:
    description: Additional raw request fields (or restore payload for C(state=restored)).
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
- name: Create a backup target
  sylve.cloud.sylve_backup_target:
    name: offsite-zfs
    ssh_host: root@backup.lan
    backup_root: tank/sylve-backups
    enabled: true
    state: present

- name: Manage Sylve cluster backup targets, validation, datasets, and restores on a specific node using a named context
  sylve.cloud.sylve_backup_target:
    context: prod
    node: node1.lan
    state: query
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
target:
  description: Backup target details or info dictionary.
  returned: always
  type: raw
  sample: '{"id": 1, "name": "offsite-zfs", "sshHost": "root@backup.lan"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveBackupTargetModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "validated", "restored", "query"],
            "default": "present",
        },
        "target_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "ssh_host": {"type": "str"},
        "ssh_port": {"type": "int"},
        "backup_root": {"type": "str"},
        "description": {"type": "str"},
        "enabled": {"type": "bool", "default": True},
        "dataset_params": {"type": "dict"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        targets = self.client.get("/cluster/backups/targets") or []
        tid = self.params.get("target_id")
        name = self.params.get("name")
        existing = None
        for t in targets if isinstance(targets, list) else []:
            if not isinstance(t, dict):
                continue
            if tid is not None and t.get("id") == tid:
                existing = t
                break
            if name and str(t.get("name") or "").lower() == name.lower():
                existing = t
                tid = int(t["id"])
                break

        if state == "query":
            if tid is None:
                self.exit_json(changed=False, target=targets)
                return
            qparams = self.params.get("dataset_params")
            info = {
                "target": existing,
                "readiness": self.client.get(f"/cluster/backups/targets/{tid}/readiness"),
                "running_jobs": self.client.get(
                    f"/cluster/backups/targets/{tid}/running-jobs"
                ),
                "datasets": self.client.get(f"/cluster/backups/targets/{tid}/datasets"),
            }
            if qparams:
                info["dataset_snapshots"] = self.client.get(
                    f"/cluster/backups/targets/{tid}/datasets/snapshots", params=qparams
                )
                info["vm_metadata"] = self.client.get(
                    f"/cluster/backups/targets/{tid}/datasets/vm-metadata", params=qparams
                )
                info["jail_metadata"] = self.client.get(
                    f"/cluster/backups/targets/{tid}/datasets/jail-metadata", params=qparams
                )
            self.exit_json(changed=False, target=info)
            return

        if state == "absent":
            if tid is None:
                self.exit_json(changed=False, target={})
                return
            if not self.check_mode:
                self.client.delete(f"/cluster/backups/targets/{tid}")
            self.exit_json(changed=True, target=existing or {"id": tid})
            return

        if state == "validated":
            if tid is None:
                self.fail_json(msg="Backup target not found for validation.")
            if not self.check_mode:
                resp = self.client.post(f"/cluster/backups/targets/{tid}/validate")
            else:
                resp = {"id": tid}
            self.exit_json(changed=True, target=resp or {"id": tid})
            return

        payload: dict = dict(self.params.get("data") or {})
        if state == "restored":
            if tid is None:
                self.fail_json(msg="Backup target not found for restore.")
            if not self.check_mode:
                resp = self.client.post(
                    f"/cluster/backups/targets/{tid}/restore", json_body=payload
                )
            else:
                resp = payload
            self.exit_json(changed=True, target=resp or payload)
            return

        for src, dst in (
            ("name", "name"),
            ("ssh_host", "sshHost"),
            ("ssh_port", "sshPort"),
            ("backup_root", "backupRoot"),
            ("description", "description"),
            ("enabled", "enabled"),
        ):
            if self.params.get(src) is not None:
                payload[dst] = self.params[src]

        if existing and tid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, target=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/cluster/backups/targets/{tid}", json_body=payload
                )
            else:
                resp = payload
            self.exit_json(changed=True, target=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/cluster/backups/targets", json_body=payload)
        else:
            resp = payload
        self.exit_json(changed=True, target=resp or payload)


def main() -> None:
    SylveBackupTargetModule()()


if __name__ == "__main__":
    main()
