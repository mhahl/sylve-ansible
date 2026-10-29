#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_backup_job
short_description: Manage Sylve scheduled backup jobs, runs, restores, snapshots, and events
description:
  - Create, update, delete, run, or restore from cluster backup jobs, and query backup job snapshots and events.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired backup job state or action.
    type: str
    choices: [present, absent, run, restored, snapshots, events]
    default: present
  job_id:
    description: Backup job numeric ID.
    type: int
    aliases: [id]
  event_id:
    description: Backup event ID when querying or waiting for an event.
    type: int
  remote_events:
    description: Query paginated remote backup events (C(/cluster/backups/events/remote)).
    type: bool
    default: false
  name:
    description: Backup job name.
    type: str
  target_id:
    description: Target backup storage ID.
    type: int
  mode:
    description: Backup mode (e.g. C(dataset), C(vm), C(jail)).
    type: str
  guest_type:
    description: Guest type (C(vm) or C(jail)).
    type: str
  guest_id:
    description: Guest RID or CTID.
    type: int
  runner_node_id:
    description: Runner node UUID.
    type: str
  cron_expr:
    description: Cron schedule expression.
    type: str
  enabled:
    description: Enable the backup job.
    type: bool
    default: true
  snapshot:
    description: Snapshot name to restore when C(state=restored).
    type: str
  encryption_key:
    description: Decryption key when C(state=restored).
    type: str
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Create a nightly backup job for VM 101
  sylve.cloud.sylve_backup_job:
    name: nightly-web-01
    target_id: 1
    mode: vm
    guest_type: vm
    guest_id: 101
    cron_expr: "0 2 * * *"
    state: present
"""

RETURN = r"""
backup_job:
  description: Backup job, snapshot list, or event details.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    SylveModule,
    wait_for_backup_event,
)


class SylveBackupJobModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "run", "restored", "snapshots", "events"],
            "default": "present",
        },
        "job_id": {"type": "int", "aliases": ["id"]},
        "event_id": {"type": "int"},
        "remote_events": {"type": "bool", "default": False},
        "name": {"type": "str"},
        "target_id": {"type": "int"},
        "mode": {"type": "str"},
        "guest_type": {"type": "str"},
        "guest_id": {"type": "int"},
        "runner_node_id": {"type": "str"},
        "cron_expr": {"type": "str"},
        "enabled": {"type": "bool", "default": True},
        "snapshot": {"type": "str"},
        "encryption_key": {"type": "str", "no_log": True},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        jid = self.params.get("job_id")
        ev_id = self.params.get("event_id")

        if state == "events":
            if ev_id is not None:
                if self.wait:
                    ev = wait_for_backup_event(
                        self.client,
                        ev_id,
                        timeout=self.timeout,
                        poll_interval=self.poll_interval,
                    )
                else:
                    ev = self.client.get(f"/cluster/backups/events/{ev_id}")
                self.exit_json(changed=False, backup_job=ev)
                return
            ep = (
                "/cluster/backups/events/remote"
                if self.params["remote_events"]
                else "/cluster/backups/events"
            )
            evs = self.client.get(ep, params={"jobId": jid} if jid is not None else None)
            self.exit_json(changed=False, backup_job=evs)
            return

        jobs = self.client.get("/cluster/backups/jobs") or []
        name = self.params.get("name")
        existing = None
        for j in jobs if isinstance(jobs, list) else []:
            if not isinstance(j, dict):
                continue
            if jid is not None and j.get("id") == jid:
                existing = j
                break
            if name and str(j.get("name") or "").lower() == name.lower():
                existing = j
                jid = int(j["id"])
                break

        if state == "snapshots":
            if jid is None:
                self.fail_json(msg="Backup job not found.")
            snaps = self.client.get(f"/cluster/backups/jobs/{jid}/snapshots")
            self.exit_json(changed=False, backup_job=snaps)
            return

        if state == "absent":
            if jid is None:
                self.exit_json(changed=False, backup_job={})
                return
            if not self.check_mode:
                self.client.delete(f"/cluster/backups/jobs/{jid}")
            self.exit_json(changed=True, backup_job=existing or {"id": jid})
            return

        if state == "run":
            if jid is None:
                self.fail_json(msg="Backup job not found.")
            if not self.check_mode:
                resp = self.client.post(f"/cluster/backups/jobs/{jid}/run")
            else:
                resp = {"id": jid}
            self.exit_json(changed=True, backup_job=resp or {"id": jid})
            return

        payload: dict = dict(self.params.get("data") or {})
        if state == "restored":
            if jid is None:
                self.fail_json(msg="Backup job not found for restore.")
            if self.params.get("snapshot"):
                payload["snapshot"] = self.params["snapshot"]
            if self.params.get("encryption_key"):
                payload["encryptionKey"] = self.params["encryption_key"]
            if not self.check_mode:
                resp = self.client.post(
                    f"/cluster/backups/jobs/{jid}/restore", json_body=payload
                )
            else:
                resp = payload
            self.exit_json(changed=True, backup_job=resp or payload)
            return

        for src, dst in (
            ("name", "name"),
            ("target_id", "targetId"),
            ("mode", "mode"),
            ("guest_type", "guestType"),
            ("guest_id", "guestId"),
            ("runner_node_id", "runnerNodeId"),
            ("cron_expr", "cronExpr"),
            ("enabled", "enabled"),
        ):
            if self.params.get(src) is not None:
                payload[dst] = self.params[src]

        if existing and jid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, backup_job=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/cluster/backups/jobs/{jid}", json_body=payload
                )
            else:
                resp = payload
            self.exit_json(changed=True, backup_job=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/cluster/backups/jobs", json_body=payload)
        else:
            resp = payload
        self.exit_json(changed=True, backup_job=resp or payload)


def main() -> None:
    SylveBackupJobModule()()


if __name__ == "__main__":
    main()
