#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_vm_storage
short_description: Manage storage volumes attached to a Sylve Bhyve VM
description:
- Attach, create from image, update, or detach storage volumes on a Bhyve VM.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired storage state.
    type: str
    choices:
    - present
    - from_image
    - absent
    default: present
    required: false
  vm:
    description: VM RID or name.
    type: str
    required: true
  storage_id:
    description: Storage attachment ID (required for update or delete when name is not matched).
    type: int
    required: false
  name:
    description: Storage volume name.
    type: str
    required: false
  type:
    description: Storage backend type (C(zvol), C(raw), C(image), C(filesystem)).
    type: str
    required: false
  pool:
    description: ZFS pool name.
    type: str
    required: false
  size:
    description: Disk size (bytes or human-readable like C(20G)).
    type: raw
    required: false
  emulation:
    description: Disk emulation type (C(virtio-blk), C(nvme), C(ahci-hd), C(ahci-cd)).
    type: str
    required: false
  image_uuid:
    description: Download/image UUID when C(state=from_image) or C(type=image).
    type: str
    required: false
  boot_order:
    description: Disk boot order.
    type: int
    required: false
  data:
    description: Additional raw request body fields.
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
- name: Attach a 50G NVMe zvol to VM 101
  sylve.cloud.sylve_vm_storage:
    vm: 101
    name: data-disk
    pool: zroot
    type: zvol
    size: 50G
    emulation: nvme
    state: present

- name: Manage storage volumes attached to a Sylve Bhyve VM on a specific node using a named context
  sylve.cloud.sylve_vm_storage:
    context: prod
    node: node1.lan
    vm: web-01
    name: data-disk
    pool: zroot
    size: 50G
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
storage:
  description: Storage operation result.
  returned: always
  type: dict
  sample: '{"id": 2, "name": "data-disk", "size": 53687091200}'
task:
  description: Completed lifecycle, migration, replication, or backup task details.
  returned: when a task is executed and C(wait=true)
  type: dict
  sample: '{"id": 42, "status": "completed"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    SylveModule,
    parse_size,
)


class SylveVMStorageModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "from_image", "absent"],
            "default": "present",
        },
        "vm": {"type": "str", "required": True},
        "storage_id": {"type": "int"},
        "name": {"type": "str"},
        "type": {"type": "str"},
        "pool": {"type": "str"},
        "size": {"type": "raw"},
        "emulation": {"type": "str"},
        "image_uuid": {"type": "str"},
        "boot_order": {"type": "int"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        rid, host, _ = self.client.resolve_vm(self.params["vm"], node=self.node)
        vm_detail = self.client.get(f"/vm/{rid}", node=host) or {}
        storages = vm_detail.get("storages") or []
        storage_id = self.params.get("storage_id")
        existing = None
        for st in storages:
            if not isinstance(st, dict):
                continue
            if storage_id is not None and st.get("id") == storage_id:
                existing = st
                break
            if self.params.get("name") and st.get("name") == self.params["name"]:
                existing = st
                storage_id = st.get("id")
                break

        state = self.params["state"]
        if state == "absent":
            if storage_id is None:
                self.exit_json(changed=False, storage={})
                return
            if not self.check_mode:
                self.client.delete(f"/vm/{rid}/storage/{storage_id}", node=host)
            self.exit_json(changed=True, storage=existing or {"id": storage_id})
            return

        payload: dict = dict(self.params.get("data") or {})
        if self.params.get("name") is not None:
            payload["name"] = self.params["name"]
        if self.params.get("type") is not None:
            payload["type"] = self.params["type"]
        if self.params.get("pool") is not None:
            payload["pool"] = self.params["pool"]
        if self.params.get("size") is not None:
            payload["size"] = parse_size(self.params["size"], "size")
        if self.params.get("emulation") is not None:
            payload["emulation"] = self.params["emulation"]
        if self.params.get("image_uuid") is not None:
            payload["uuid"] = self.params["image_uuid"]
        if self.params.get("boot_order") is not None:
            payload["bootOrder"] = self.params["boot_order"]

        if state == "from_image":
            if self.check_mode:
                self.exit_json(changed=True, storage=payload)
                return
            resp = self.client.post(f"/vm/{rid}/storage/from-image", json_body=payload, node=host)
            self.wait_task(resp, node=host)
            self.exit_json(changed=True, storage=resp or payload)
            return

        if existing and storage_id is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, storage=existing)
                return
            if not self.check_mode:
                resp = self.client.patch(
                    f"/vm/{rid}/storage/{storage_id}", json_body=payload, node=host
                )
            else:
                resp = payload
            self.exit_json(changed=True, storage=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(f"/vm/{rid}/storage", json_body=payload, node=host)
        else:
            resp = payload
        self.exit_json(changed=True, storage=resp or payload)


def main() -> None:
    SylveVMStorageModule()()


if __name__ == "__main__":
    main()
