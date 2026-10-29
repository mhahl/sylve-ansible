#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_samba
short_description: Manage Sylve Samba global configuration, shares, and audit logs
description:
- Query or update Samba global configuration, create/update/enable/disable/delete Samba shares, or fetch Samba audit logs.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  resource:
    description: Samba component to manage.
    type: str
    choices:
    - share
    - config
    - audit_logs
    default: share
    required: false
  state:
    description: Desired share state.
    type: str
    choices:
    - present
    - absent
    - enabled
    - disabled
    - query
    default: present
    required: false
  share_id:
    description: Numeric Samba share ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: Samba share name.
    type: str
    required: false
  dataset:
    description: ZFS dataset or path backing the share.
    type: str
    required: false
  enabled:
    description: Enable or disable the share.
    type: bool
    required: false
  data:
    description: Additional raw request fields (or full body for C(resource=config)).
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
- name: Create a Samba share
  sylve.cloud.sylve_samba:
    resource: share
    name: media
    dataset: zroot/media
    enabled: true
    state: present

- name: Manage Sylve Samba global configuration, shares, and audit logs on a specific node using a named context
  sylve.cloud.sylve_samba:
    context: prod
    node: node1.lan
    resource: share
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
samba:
  description: Samba share, global config, or audit logs.
  returned: always
  type: raw
  sample: '{"id": 1, "name": "media", "enabled": true}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveSambaModule(SylveModule):
    argument_spec = {
        "resource": {
            "type": "str",
            "choices": ["share", "config", "audit_logs"],
            "default": "share",
        },
        "state": {
            "type": "str",
            "choices": ["present", "absent", "enabled", "disabled", "query"],
            "default": "present",
        },
        "share_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "dataset": {"type": "str"},
        "enabled": {"type": "bool"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        resource = self.params["resource"]
        state = self.params["state"]
        payload: dict = dict(self.params.get("data") or {})

        if resource == "audit_logs":
            logs = self.client.get("/samba/audit-logs", node=self.node)
            self.exit_json(changed=False, samba=logs)
            return

        if resource == "config":
            current = self.client.get("/samba/config", node=self.node) or {}
            if state == "query" or (
                isinstance(current, dict) and not self.subset_differs(payload, current)
            ):
                self.exit_json(changed=False, samba=current)
                return
            if not self.check_mode:
                resp = self.client.put("/samba/config", json_body=payload, node=self.node)
            else:
                resp = payload
            self.exit_json(changed=True, samba=resp or payload)
            return

        shares = self.client.get("/samba/shares", node=self.node) or []
        if state == "query":
            self.exit_json(changed=False, samba=shares)
            return

        sid = self.params.get("share_id")
        name = self.params.get("name")
        existing = None
        for sh in shares if isinstance(shares, list) else []:
            if not isinstance(sh, dict):
                continue
            if sid is not None and sh.get("id") == sid:
                existing = sh
                break
            if name and str(sh.get("name") or "").lower() == name.lower():
                existing = sh
                sid = int(sh["id"])
                break

        if state == "absent":
            if sid is None:
                self.exit_json(changed=False, samba={})
                return
            if not self.check_mode:
                self.client.delete(f"/samba/shares/{sid}", node=self.node)
            self.exit_json(changed=True, samba=existing or {"id": sid})
            return

        if state in ("enabled", "disabled"):
            if sid is None:
                self.fail_json(msg="Samba share not found.")
            body = {"enabled": state == "enabled"}
            if not self.check_mode:
                resp = self.client.put(
                    f"/samba/shares/{sid}/enabled", json_body=body, node=self.node
                )
            else:
                resp = body
            self.exit_json(changed=True, samba=resp or body)
            return

        for key in ("name", "dataset", "enabled"):
            if self.params.get(key) is not None:
                payload[key] = self.params[key]

        if existing and sid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, samba=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/samba/shares/{sid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, samba=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/samba/shares", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, samba=resp or payload)


def main() -> None:
    SylveSambaModule()()


if __name__ == "__main__":
    main()
