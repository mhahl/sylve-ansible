#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
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
    choices:
    - present
    - absent
    - run
    - restored
    - snapshots
    - events
    default: present
    required: false
  job_id:
    description: Backup job numeric ID.
    type: int
    aliases:
    - id
    required: false
  event_id:
    description: Backup event ID when querying or waiting for an event.
    type: int
    required: false
  remote_events:
    description: Query paginated remote backup events (C(/cluster/backups/events/remote)).
    type: bool
    default: false
    required: false
  name:
    description: Backup job name.
    type: str
    required: false
  target_id:
    description: Target backup storage ID.
    type: int
    required: false
  mode:
    description: Backup mode (e.g. C(dataset), C(vm), C(jail)).
    type: str
    required: false
  guest_type:
    description: Guest type (C(vm) or C(jail)).
    type: str
    required: false
  guest_id:
    description: Guest RID or CTID.
    type: int
    required: false
  runner_node_id:
    description: Runner node UUID.
    type: str
    required: false
  cron_expr:
    description: Cron schedule expression.
    type: str
    required: false
  enabled:
    description: Enable the backup job.
    type: bool
    default: true
    required: false
  snapshot:
    description: Snapshot name to restore when C(state=restored).
    type: str
    required: false
  encryption_key:
    description: Decryption key when C(state=restored).
    type: str
    required: false
  data:
    description: Additional raw request fields.
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
- name: Create a nightly backup job for VM 101
  sylve.cloud.sylve_backup_job:
    name: nightly-web-01
    target_id: 1
    mode: vm
    guest_type: vm
    guest_id: 101
    cron_expr: "0 2 * * *"
    state: present

- name: Manage Sylve scheduled backup jobs, runs, restores, snapshots, and events on a specific node using a named context
  sylve.cloud.sylve_backup_job:
    context: prod
    node: node1.lan
    state: events
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
backup_job:
  description: Backup job, snapshot list, or event details.
  returned: always
  type: raw
  sample: '{"id": 3, "name": "nightly-web-01", "lastStatus": "success"}'
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
