#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_disk
short_description: Manage Sylve host disks, GPT partition tables, partitions, and SMART self-tests
description:
- Query disks, initialize or clear GPT partition tables, create/delete partitions, run/abort SMART self-tests, and manage
  SMART schedules.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  action:
    description: Disk or SMART operation to perform.
    type: str
    choices:
    - info
    - gpt_init
    - gpt_clear
    - partition_create
    - partition_delete
    - smart_info
    - smart_start
    - smart_abort
    - smart_schedules
    - smart_schedule_present
    - smart_schedule_absent
    default: info
    required: false
  device:
    description: Disk device name (e.g. C(nda0), C(ada0)).
    type: str
    required: false
  partition:
    description: Partition identifier (e.g. C(nda0p1)) for C(action=partition_delete).
    type: str
    required: false
  schedule_id:
    description: SMART schedule ID.
    type: int
    required: false
  data:
    description: Request body for partition creation, SMART self-test, or SMART schedule.
    type: dict
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
- name: Initialize GPT partition table on ada1
  sylve.cloud.sylve_disk:
    action: gpt_init
    device: ada1

- name: Manage Sylve host disks, GPT partition tables, partitions, and SMART self-tests on a specific node using a named context
  sylve.cloud.sylve_disk:
    context: prod
    node: node1.lan
    action: info
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
disk:
  description: Disk, partition, or SMART operation result.
  returned: always
  type: raw
  sample: '{"device": "ada1", "smartStatus": "PASSED"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveDiskModule(SylveModule):
    argument_spec = {
        "action": {
            "type": "str",
            "choices": [
                "info",
                "gpt_init",
                "gpt_clear",
                "partition_create",
                "partition_delete",
                "smart_info",
                "smart_start",
                "smart_abort",
                "smart_schedules",
                "smart_schedule_present",
                "smart_schedule_absent",
            ],
            "default": "info",
        },
        "device": {"type": "str"},
        "partition": {"type": "str"},
        "schedule_id": {"type": "int"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        act = self.params["action"]
        dev = self.params.get("device")
        part = self.params.get("partition")
        sid = self.params.get("schedule_id")
        body = dict(self.params.get("data") or {})
        if dev and "device" not in body:
            body.setdefault("device", dev)

        if act == "info":
            res = self.client.get("/disk", node=self.node)
            self.exit_json(changed=False, disk=res)
            return

        if act == "smart_info":
            res = self.client.get("/disk/smart/self-test", node=self.node)
            self.exit_json(changed=False, disk=res)
            return

        if act == "smart_schedules":
            res = self.client.get("/disk/smart/self-test/schedules", node=self.node)
            self.exit_json(changed=False, disk=res)
            return

        if self.check_mode:
            self.exit_json(changed=True, disk=body)
            return

        if act == "gpt_init":
            resp = self.client.post(f"/disk/{dev}/partition-table", json_body=body, node=self.node)
        elif act == "gpt_clear":
            resp = self.client.delete(f"/disk/{dev}/partition-table", node=self.node)
        elif act == "partition_create":
            resp = self.client.post(f"/disk/{dev}/partitions", json_body=body, node=self.node)
        elif act == "partition_delete":
            resp = self.client.delete(f"/disk/partitions/{part}", node=self.node)
        elif act == "smart_start":
            resp = self.client.post("/disk/smart/self-test", json_body=body, node=self.node)
        elif act == "smart_abort":
            resp = self.client.post("/disk/smart/self-test/abort", json_body=body, node=self.node)
        elif act == "smart_schedule_present":
            if sid is not None:
                resp = self.client.put(
                    f"/disk/smart/self-test/schedules/{sid}", json_body=body, node=self.node
                )
            else:
                resp = self.client.post(
                    "/disk/smart/self-test/schedules", json_body=body, node=self.node
                )
        else:
            resp = self.client.delete(
                f"/disk/smart/self-test/schedules/{sid}", node=self.node
            )

        self.exit_json(changed=True, disk=resp or body)


def main() -> None:
    SylveDiskModule()()


if __name__ == "__main__":
    main()
