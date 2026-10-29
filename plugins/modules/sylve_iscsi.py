#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_iscsi
short_description: Manage Sylve iSCSI global config, initiators, targets, LUNs, and portals
description:
- Query or configure iSCSI global settings, initiators (and connect), targets, target LUNs, target portals, status, and target
  sessions.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  resource:
    description: iSCSI sub-resource to manage.
    type: str
    choices:
    - config
    - initiator
    - target
    - lun
    - portal
    - status
    - sessions
    default: target
    required: false
  state:
    description: Desired state or action.
    type: str
    choices:
    - present
    - absent
    - connected
    - query
    default: present
    required: false
  id:
    description: Initiator ID, Target ID, LUN ID, or Portal ID.
    type: int
    required: false
  target_id:
    description: Parent Target ID when managing C(lun) or C(portal).
    type: int
    required: false
  name:
    description: Resource name or IQN.
    type: str
    required: false
  data:
    description: Request body fields.
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
- name: Create an iSCSI target
  sylve.cloud.sylve_iscsi:
    resource: target
    name: iqn.2026-01.lan.sylve:storage01
    state: present

- name: Manage Sylve iSCSI global config, initiators, targets, LUNs, and portals on a specific node using a named context
  sylve.cloud.sylve_iscsi:
    context: prod
    node: node1.lan
    resource: status
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
iscsi:
  description: iSCSI resource details.
  returned: always
  type: raw
  sample: '{"id": 1, "name": "iqn.2026-01.lan.sylve:storage01"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveISCSIModule(SylveModule):
    argument_spec = {
        "resource": {
            "type": "str",
            "choices": [
                "config",
                "initiator",
                "target",
                "lun",
                "portal",
                "status",
                "sessions",
            ],
            "default": "target",
        },
        "state": {
            "type": "str",
            "choices": ["present", "absent", "connected", "query"],
            "default": "present",
        },
        "id": {"type": "int"},
        "target_id": {"type": "int"},
        "name": {"type": "str"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        res_type = self.params["resource"]
        state = self.params["state"]
        item_id = self.params.get("id")
        target_id = self.params.get("target_id")
        name = self.params.get("name")
        payload: dict = dict(self.params.get("data") or {})
        if name:
            payload.setdefault("name", name)

        if res_type == "status":
            self.exit_json(changed=False, iscsi=self.client.get("/iscsi/status", node=self.node))
            return

        if res_type == "sessions":
            self.exit_json(
                changed=False, iscsi=self.client.get("/iscsi/target-sessions", node=self.node)
            )
            return

        if res_type == "config":
            current = self.client.get("/iscsi/config", node=self.node) or {}
            if state == "query" or (
                isinstance(current, dict) and not self.subset_differs(payload, current)
            ):
                self.exit_json(changed=False, iscsi=current)
                return
            if not self.check_mode:
                resp = self.client.put("/iscsi/config", json_body=payload, node=self.node)
            else:
                resp = payload
            self.exit_json(changed=True, iscsi=resp or payload)
            return

        if res_type in ("lun", "portal"):
            if target_id is None:
                self.fail_json(msg="'target_id' is required for LUN and portal operations.")
            sub = "luns" if res_type == "lun" else "portals"
            if state == "absent":
                if item_id is None:
                    self.exit_json(changed=False, iscsi={})
                    return
                if not self.check_mode:
                    self.client.delete(
                        f"/iscsi/targets/{target_id}/{sub}/{item_id}", node=self.node
                    )
                self.exit_json(changed=True, iscsi={"id": item_id})
                return
            if not self.check_mode:
                resp = self.client.post(
                    f"/iscsi/targets/{target_id}/{sub}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, iscsi=resp or payload)
            return

        base_path = "/iscsi/initiators" if res_type == "initiator" else "/iscsi/targets"
        items = self.client.get(base_path, node=self.node) or []
        if state == "query":
            self.exit_json(changed=False, iscsi=items)
            return

        existing = None
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            if item_id is not None and item.get("id") == item_id:
                existing = item
                break
            if name and str(item.get("name") or "").lower() == name.lower():
                existing = item
                item_id = int(item["id"])
                break

        if state == "connected" and res_type == "initiator":
            if item_id is None:
                self.fail_json(msg="iSCSI initiator not found to connect.")
            if not self.check_mode:
                resp = self.client.post(f"/iscsi/initiators/{item_id}/connect", node=self.node)
            else:
                resp = {"id": item_id}
            self.exit_json(changed=True, iscsi=resp or {"id": item_id})
            return

        if state == "absent":
            if item_id is None:
                self.exit_json(changed=False, iscsi={})
                return
            if not self.check_mode:
                self.client.delete(f"{base_path}/{item_id}", node=self.node)
            self.exit_json(changed=True, iscsi=existing or {"id": item_id})
            return

        if existing and item_id is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, iscsi=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"{base_path}/{item_id}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, iscsi=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(base_path, json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, iscsi=resp or payload)


def main() -> None:
    SylveISCSIModule()()


if __name__ == "__main__":
    main()
