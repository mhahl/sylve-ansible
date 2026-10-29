#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_task
short_description: Query, wait for, validate, or cancel Sylve lifecycle and migration tasks
description:
- Query active or recent lifecycle tasks, wait for a task by ID, validate guest migration preflight, or cancel an active migration
  task.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  action:
    description: Task operation to perform.
    type: str
    choices:
    - active
    - recent
    - show
    - wait
    - validate_migration
    - cancel_migration
    default: recent
    required: false
  task_id:
    description: Lifecycle or migration task ID.
    type: int
    aliases:
    - id
    required: false
  guest_type:
    description: Guest type (C(vm) or C(jail)).
    type: str
    required: false
  guest_id:
    description: Guest RID or CTID.
    type: int
    required: false
  target_node:
    description: Target node hostname or UUID for C(action=validate_migration).
    type: str
    required: false
  limit:
    description: Maximum recent tasks to return.
    type: int
    default: 25
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
- name: Wait for lifecycle task 42 to complete
  sylve.cloud.sylve_task:
    action: wait
    task_id: 42

- name: Query, wait for, validate, or cancel Sylve lifecycle and migration tasks on a specific node using a named context
  sylve.cloud.sylve_task:
    context: prod
    node: node1.lan
    action: recent
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
task:
  description: Task details or task list.
  returned: always
  type: raw
  sample: '{"id": 42, "action": "start", "status": "completed"}'
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
