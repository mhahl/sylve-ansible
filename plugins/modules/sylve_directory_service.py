#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_directory_service
short_description: Manage Sylve Active Directory and Kerberos directory services
description:
- Configure Active Directory (check, enable/disable, join, leave, status), Kerberos realms (discover, CRUD), Kerberos keytabs
  (CRUD), Kerberos settings, and query directory principals.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  service:
    description: Directory service component to manage.
    type: str
    choices:
    - active_directory
    - kerberos_realm
    - kerberos_keytab
    - kerberos_settings
    - principals
    default: active_directory
    required: false
  action:
    description: Operation to perform.
    type: str
    choices:
    - info
    - present
    - absent
    - check
    - enabled
    - join
    - leave
    - discover
    default: present
    required: false
  id:
    description: Numeric Kerberos realm or keytab ID.
    type: int
    required: false
  name:
    description: Realm or keytab name.
    type: str
    required: false
  enabled:
    description: Enable or disable Active Directory when C(action=enabled).
    type: bool
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
- name: Query Active Directory status
  sylve.cloud.sylve_directory_service:
    service: active_directory
    action: info

- name: Manage Sylve Active Directory and Kerberos directory services on a specific node using a named context
  sylve.cloud.sylve_directory_service:
    context: prod
    node: node1.lan
    service: active_directory
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
directory_service:
  description: Directory service configuration or operation result.
  returned: always
  type: raw
  sample: '{"enabled": true}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveDirectoryServiceModule(SylveModule):
    argument_spec = {
        "service": {
            "type": "str",
            "choices": [
                "active_directory",
                "kerberos_realm",
                "kerberos_keytab",
                "kerberos_settings",
                "principals",
            ],
            "default": "active_directory",
        },
        "action": {
            "type": "str",
            "choices": [
                "info",
                "present",
                "absent",
                "check",
                "enabled",
                "join",
                "leave",
                "discover",
            ],
            "default": "present",
        },
        "id": {"type": "int"},
        "name": {"type": "str"},
        "enabled": {"type": "bool"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        svc = self.params["service"]
        act = self.params["action"]
        item_id = self.params.get("id")
        name = self.params.get("name")
        payload: dict = dict(self.params.get("data") or {})

        if svc == "principals":
            res = self.client.get("/directory-services/principals", node=self.node)
            self.exit_json(changed=False, directory_service=res)
            return

        if svc == "active_directory":
            if act == "info":
                res = {
                    "config": self.client.get(
                        "/directory-services/active-directory", node=self.node
                    ),
                    "status": self.client.get(
                        "/directory-services/active-directory/status", node=self.node
                    ),
                }
                self.exit_json(changed=False, directory_service=res)
                return
            if act == "check":
                res = self.client.post(
                    "/directory-services/active-directory/check",
                    json_body=payload,
                    node=self.node,
                )
                self.exit_json(changed=False, directory_service=res)
                return
            if self.check_mode:
                self.exit_json(changed=True, directory_service=payload)
                return
            if act == "enabled":
                body = {"enabled": bool(self.params.get("enabled", True))}
                resp = self.client.put(
                    "/directory-services/active-directory/enabled",
                    json_body=body,
                    node=self.node,
                )
            elif act == "join":
                resp = self.client.post(
                    "/directory-services/active-directory/join",
                    json_body=payload,
                    node=self.node,
                )
            elif act == "leave":
                resp = self.client.post(
                    "/directory-services/active-directory/leave",
                    json_body=payload,
                    node=self.node,
                )
            else:
                resp = self.client.put(
                    "/directory-services/active-directory",
                    json_body=payload,
                    node=self.node,
                )
            self.exit_json(changed=True, directory_service=resp or payload)
            return

        if svc == "kerberos_settings":
            current = self.client.get(
                "/directory-services/kerberos/settings", node=self.node
            ) or {}
            if act == "info" or (
                isinstance(current, dict) and not self.subset_differs(payload, current)
            ):
                self.exit_json(changed=False, directory_service=current)
                return
            if not self.check_mode:
                resp = self.client.put(
                    "/directory-services/kerberos/settings",
                    json_body=payload,
                    node=self.node,
                )
            else:
                resp = payload
            self.exit_json(changed=True, directory_service=resp or payload)
            return

        if svc == "kerberos_realm" and act == "discover":
            res = self.client.post(
                "/directory-services/kerberos/realms/discover",
                json_body=payload,
                node=self.node,
            )
            self.exit_json(changed=False, directory_service=res)
            return

        base_path = (
            "/directory-services/kerberos/realms"
            if svc == "kerberos_realm"
            else "/directory-services/kerberos/keytabs"
        )
        items = self.client.get(base_path, node=self.node) or []
        if act == "info":
            self.exit_json(changed=False, directory_service=items)
            return

        existing = None
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            if item_id is not None and item.get("id") == item_id:
                existing = item
                break
            if name and str(item.get("name") or item.get("realm") or "").lower() == name.lower():
                existing = item
                item_id = int(item["id"])
                break

        if act == "absent":
            if item_id is None:
                self.exit_json(changed=False, directory_service={})
                return
            if not self.check_mode:
                self.client.delete(f"{base_path}/{item_id}", node=self.node)
            self.exit_json(changed=True, directory_service=existing or {"id": item_id})
            return

        if name:
            payload.setdefault("realm" if svc == "kerberos_realm" else "name", name)

        if existing and item_id is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, directory_service=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"{base_path}/{item_id}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, directory_service=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(base_path, json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, directory_service=resp or payload)


def main() -> None:
    SylveDirectoryServiceModule()()


if __name__ == "__main__":
    main()
