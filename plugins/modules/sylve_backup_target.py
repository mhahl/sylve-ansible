#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
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
    choices: [present, absent, validated, restored, info]
    default: present
  target_id:
    description: Backup target numeric ID.
    type: int
    aliases: [id]
  name:
    description: Backup target name.
    type: str
  ssh_host:
    description: Remote SSH host (e.g. C(backup@host)).
    type: str
  ssh_port:
    description: Remote SSH port.
    type: int
  backup_root:
    description: Remote ZFS dataset root path.
    type: str
  description:
    description: Backup target description.
    type: str
  enabled:
    description: Enable the backup target.
    type: bool
    default: true
  dataset_params:
    description: Query parameters when inspecting datasets/snapshots/metadata in C(state=info).
    type: dict
  data:
    description: Additional raw request fields (or restore payload for C(state=restored)).
    type: dict
"""

EXAMPLES = r"""
- name: Create a backup target
  sylve.cloud.sylve_backup_target:
    name: offsite-zfs
    ssh_host: root@backup.lan
    backup_root: tank/sylve-backups
    enabled: true
    state: present
"""

RETURN = r"""
target:
  description: Backup target details or info dictionary.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveBackupTargetModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "validated", "restored", "info"],
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

        if state == "info":
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
