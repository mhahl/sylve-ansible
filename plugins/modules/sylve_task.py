#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_task
short_description: Query, wait for, validate, or cancel Sylve lifecycle and migration tasks
description:
  - Query active or recent lifecycle tasks, wait for a task by ID, validate guest migration preflight, or cancel an active migration task.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  action:
    description: Task operation to perform.
    type: str
    choices: [active, recent, show, wait, validate_migration, cancel_migration]
    default: recent
  task_id:
    description: Lifecycle or migration task ID.
    type: int
    aliases: [id]
  guest_type:
    description: Guest type (C(vm) or C(jail)).
    type: str
  guest_id:
    description: Guest RID or CTID.
    type: int
  target_node:
    description: Target node hostname or UUID for C(action=validate_migration).
    type: str
  limit:
    description: Maximum recent tasks to return.
    type: int
    default: 25
"""

EXAMPLES = r"""
- name: Wait for lifecycle task 42 to complete
  sylve.cloud.sylve_task:
    action: wait
    task_id: 42
"""

RETURN = r"""
task:
  description: Task details or task list.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    SylveModule,
    wait_for_lifecycle_task,
)


class SylveTaskModule(SylveModule):
    argument_spec = {
        "action": {
            "type": "str",
            "choices": [
                "active",
                "recent",
                "show",
                "wait",
                "validate_migration",
                "cancel_migration",
            ],
            "default": "recent",
        },
        "task_id": {"type": "int", "aliases": ["id"]},
        "guest_type": {"type": "str"},
        "guest_id": {"type": "int"},
        "target_node": {"type": "str"},
        "limit": {"type": "int", "default": 25},
    }

    def run(self) -> None:
        act = self.params["action"]
        tid = self.params.get("task_id")
        gtype = self.params.get("guest_type")
        gid = self.params.get("guest_id")

        if act == "active":
            if gtype and gid is not None:
                res = self.client.get(
                    f"/tasks/lifecycle/active/{gtype}/{gid}", node=self.node
                )
            else:
                res = self.client.get(
                    "/tasks/lifecycle/active",
                    params={"guestType": gtype, "guestId": gid},
                    node=self.node,
                )
            self.exit_json(changed=False, task=res)
            return

        if act == "recent":
            res = self.client.get(
                "/tasks/lifecycle/recent",
                params={"guestType": gtype, "guestId": gid, "limit": self.params["limit"]},
                node=self.node,
            )
            self.exit_json(changed=False, task=res)
            return

        if act == "show":
            if tid is None:
                self.fail_json(msg="'task_id' is required for action=show.")
            res = self.client.get(f"/tasks/lifecycle/{tid}", node=self.node)
            self.exit_json(changed=False, task=res)
            return

        if act == "wait":
            if tid is None:
                self.fail_json(msg="'task_id' is required for action=wait.")
            res = wait_for_lifecycle_task(
                self.client,
                tid,
                node=self.node,
                timeout=self.timeout,
                poll_interval=self.poll_interval,
            )
            self.exit_json(changed=False, task=res)
            return

        if act == "validate_migration":
            if not gtype or gid is None or not self.params.get("target_node"):
                self.fail_json(
                    msg="guest_type, guest_id, and target_node are required for validate_migration."
                )
            tuuid, _ = self.client.resolve_node_uuid(self.params["target_node"])
            res = self.client.get(
                "/tasks/migration/validate",
                params={"guestType": gtype, "guestId": gid, "targetNodeUuid": tuuid},
                node=self.node,
            )
            self.exit_json(changed=False, task=res)
            return

        if tid is None:
            self.fail_json(msg="'task_id' is required for action=cancel_migration.")
        if not self.check_mode:
            resp = self.client.post(f"/tasks/migration/{tid}/cancel", node=self.node)
        else:
            resp = {"id": tid}
        self.exit_json(changed=True, task=resp or {"id": tid})


def main() -> None:
    SylveTaskModule()()


if __name__ == "__main__":
    main()
