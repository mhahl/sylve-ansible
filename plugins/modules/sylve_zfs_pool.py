#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_zfs_pool
short_description: Manage Sylve ZFS storage pools, devices, scrubs, and scrub schedules
description:
- Create, edit, delete, scrub, detach/replace devices on ZFS pools, or manage ZFS pool scrub schedules.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired ZFS pool state or action.
    type: str
    choices:
    - present
    - absent
    - scrubbed
    - device_detached
    - device_replaced
    - scrub_schedule_present
    - scrub_schedule_absent
    default: present
    required: false
  name:
    description: ZFS pool name.
    type: str
    required: false
  guid:
    description: ZFS pool GUID.
    type: str
    required: false
  schedule_id:
    description: Scrub schedule ID when managing scrub schedules.
    type: int
    required: false
  cron_expr:
    description: Cron schedule expression for scrub schedules.
    type: str
    required: false
  properties:
    description: Pool properties dictionary.
    type: dict
    required: false
  vdevs:
    description: Pool vdev layout list when creating a pool.
    type: list
    elements: dict
    required: false
  device:
    description: Device identifier for C(device_detached) or old device for C(device_replaced).
    type: str
    required: false
  new_device:
    description: Replacement device identifier for C(device_replaced).
    type: str
    required: false
  data:
    description: Additional raw request body fields.
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
- name: Start a scrub on ZFS pool zroot
  sylve.cloud.sylve_zfs_pool:
    name: zroot
    state: scrubbed

- name: Manage Sylve ZFS storage pools, devices, scrubs, and scrub schedules on a specific node using a named context
  sylve.cloud.sylve_zfs_pool:
    context: prod
    node: node1.lan
    name: zroot
    state: scrubbed
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
pool:
  description: ZFS pool or scrub schedule details.
  returned: always
  type: dict
  sample: '{"name": "zroot", "state": "ONLINE"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveZFSPoolModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": [
                "present",
                "absent",
                "scrubbed",
                "device_detached",
                "device_replaced",
                "scrub_schedule_present",
                "scrub_schedule_absent",
            ],
            "default": "present",
        },
        "name": {"type": "str"},
        "guid": {"type": "str"},
        "schedule_id": {"type": "int"},
        "cron_expr": {"type": "str"},
        "properties": {"type": "dict"},
        "vdevs": {"type": "list", "elements": "dict"},
        "device": {"type": "str"},
        "new_device": {"type": "str"},
        "data": {"type": "dict"},
    }

    def _find_pool(self) -> tuple[str | None, dict]:
        pools = self.client.get("/zfs/pools", params={"all": True}, node=self.node) or []
        guid = self.params.get("guid")
        name = self.params.get("name")
        for p in pools if isinstance(pools, list) else []:
            if not isinstance(p, dict):
                continue
            p_guid = str(p.get("pool_guid") or p.get("guid") or "")
            p_name = str(p.get("name") or "")
            if guid and p_guid.lower() == guid.lower():
                return p_guid, p
            if name and p_name.lower() == name.lower():
                return p_guid, p
        return guid, {}

    def run(self) -> None:
        state = self.params["state"]
        payload: dict = dict(self.params.get("data") or {})

        if state in ("scrub_schedule_present", "scrub_schedule_absent"):
            scheds = self.client.get("/zfs/pools/scrub/schedules", node=self.node) or []
            sid = self.params.get("schedule_id")
            existing_s = None
            for s in scheds if isinstance(scheds, list) else []:
                if not isinstance(s, dict):
                    continue
                if sid is not None and s.get("id") == sid:
                    existing_s = s
                    break
                if self.params.get("name") and s.get("pool") == self.params["name"]:
                    existing_s = s
                    sid = int(s["id"])
                    break
            if state == "scrub_schedule_absent":
                if sid is None:
                    self.exit_json(changed=False, pool={})
                    return
                if not self.check_mode:
                    self.client.delete(f"/zfs/pools/scrub/schedules/{sid}", node=self.node)
                self.exit_json(changed=True, pool=existing_s or {"id": sid})
                return
            if self.params.get("name"):
                payload.setdefault("pool", self.params["name"])
            if self.params.get("guid"):
                payload.setdefault("guid", self.params["guid"])
            if self.params.get("cron_expr"):
                payload.setdefault("cronExpr", self.params["cron_expr"])
            if existing_s and sid is not None:
                if not self.subset_differs(payload, existing_s):
                    self.exit_json(changed=False, pool=existing_s)
                    return
                if not self.check_mode:
                    resp = self.client.put(
                        f"/zfs/pools/scrub/schedules/{sid}", json_body=payload, node=self.node
                    )
                else:
                    resp = payload
                self.exit_json(changed=True, pool=resp or payload)
                return
            if not self.check_mode:
                resp = self.client.post(
                    "/zfs/pools/scrub/schedules", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, pool=resp or payload)
            return

        guid, existing = self._find_pool()

        if state == "absent":
            if not guid or not existing:
                self.exit_json(changed=False, pool={})
                return
            if not self.check_mode:
                self.client.delete(f"/zfs/pools/{guid}", node=self.node)
            self.exit_json(changed=True, pool=existing)
            return

        if state == "scrubbed":
            if not guid:
                self.fail_json(msg="ZFS pool not found for scrub.")
            if not self.check_mode:
                self.client.post(f"/zfs/pools/{guid}/scrub", node=self.node)
            self.exit_json(changed=True, pool=existing or {"guid": guid})
            return

        if state == "device_detached":
            if not guid:
                self.fail_json(msg="ZFS pool not found for device detach.")
            if self.params.get("device"):
                payload["device"] = self.params["device"]
            if not self.check_mode:
                self.client.post(
                    f"/zfs/pools/{guid}/detach", json_body=payload, node=self.node
                )
            self.exit_json(changed=True, pool=payload)
            return

        if state == "device_replaced":
            if not guid:
                self.fail_json(msg="ZFS pool not found for device replace.")
            if self.params.get("device"):
                payload.setdefault("oldDevice", self.params["device"])
            if self.params.get("new_device"):
                payload.setdefault("newDevice", self.params["new_device"])
            if not self.check_mode:
                self.client.post(
                    f"/zfs/pools/{guid}/replace-device", json_body=payload, node=self.node
                )
            self.exit_json(changed=True, pool=payload)
            return

        if self.params.get("name"):
            payload["name"] = self.params["name"]
        if self.params.get("properties") is not None:
            payload["properties"] = self.params["properties"]
        if self.params.get("vdevs") is not None:
            payload["vdevs"] = self.params["vdevs"]

        if existing and guid:
            if not self.params.get("properties") and not self.params.get("data"):
                self.exit_json(changed=False, pool=existing)
                return
            if not self.check_mode:
                resp = self.client.patch(
                    f"/zfs/pools/{guid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, pool=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/zfs/pools", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, pool=resp or payload)


def main() -> None:
    SylveZFSPoolModule()()


if __name__ == "__main__":
    main()
