#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_notification
short_description: Manage Sylve notification transports, alert rules, and active notifications
description:
- List, create, update, bulk-update, test, or delete notification transports and rules, or count/dismiss active notifications.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  resource:
    description: Notification sub-resource to manage.
    type: str
    choices:
    - transport
    - rule
    - notification
    default: rule
    required: false
  state:
    description: Desired state or action.
    type: str
    choices:
    - present
    - absent
    - tested
    - dismissed
    - dismissed_all
    - bulk_updated
    - query
    default: present
    required: false
  id:
    description: Numeric transport, rule, or notification ID.
    type: int
    required: false
  ids:
    description: List of rule IDs for bulk deletion or bulk update.
    type: list
    elements: int
    required: false
  name:
    description: Transport or rule name.
    type: str
    required: false
  type:
    description: Transport type (e.g. C(webhook), C(smtp), C(discord)).
    type: str
    required: false
  enabled:
    description: Enable the transport or rule.
    type: bool
    required: false
  data:
    description: Request payload dictionary.
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
- name: Create a webhook notification transport
  sylve.cloud.sylve_notification:
    resource: transport
    name: ops-webhook
    type: webhook
    enabled: true
    data:
      url: https://hooks.example.com/sylve
    state: present

- name: Manage Sylve notification transports, alert rules, and active notifications on a specific node using a named context
  sylve.cloud.sylve_notification:
    context: prod
    node: node1.lan
    resource: notification
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
notification:
  description: Notification transport, rule, or alert result.
  returned: always
  type: raw
  sample: '{"id": 1, "name": "ops-webhook"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveNotificationModule(SylveModule):
    argument_spec = {
        "resource": {
            "type": "str",
            "choices": ["transport", "rule", "notification"],
            "default": "rule",
        },
        "state": {
            "type": "str",
            "choices": [
                "present",
                "absent",
                "tested",
                "dismissed",
                "dismissed_all",
                "bulk_updated",
                "query",
            ],
            "default": "present",
        },
        "id": {"type": "int"},
        "ids": {"type": "list", "elements": "int"},
        "name": {"type": "str"},
        "type": {"type": "str"},
        "enabled": {"type": "bool"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        resource = self.params["resource"]
        state = self.params["state"]
        item_id = self.params.get("id")
        name = self.params.get("name")
        payload: dict = dict(self.params.get("data") or {})

        if resource == "notification":
            if state == "query":
                res = {
                    "items": self.client.get("/notifications", node=self.node),
                    "count": self.client.get("/notifications/count", node=self.node),
                }
                self.exit_json(changed=False, notification=res)
                return
            if state == "dismissed_all":
                if not self.check_mode:
                    self.client.post("/notifications/dismiss-all", node=self.node)
                self.exit_json(changed=True, notification={"dismissed_all": True})
                return
            if item_id is None:
                self.fail_json(msg="'id' is required to dismiss a notification.")
            if not self.check_mode:
                self.client.post(f"/notifications/{item_id}/dismiss", node=self.node)
            self.exit_json(changed=True, notification={"id": item_id})
            return

        base_path = (
            "/notifications/transports" if resource == "transport" else "/notifications/rules"
        )
        items = self.client.get(base_path, node=self.node) or []
        if state == "query":
            self.exit_json(changed=False, notification=items)
            return

        if resource == "rule" and state == "bulk_updated":
            if self.params.get("ids"):
                payload.setdefault("ids", self.params["ids"])
            if not self.check_mode:
                if "ids" in payload:
                    resp = self.client.post(
                        "/notifications/rules/bulk-update", json_body=payload, node=self.node
                    )
                else:
                    resp = self.client.put(
                        "/notifications/rules", json_body=payload, node=self.node
                    )
            else:
                resp = payload
            self.exit_json(changed=True, notification=resp or payload)
            return

        if resource == "rule" and state == "absent" and self.params.get("ids"):
            body = {"ids": self.params["ids"]}
            if not self.check_mode:
                self.client.post(
                    "/notifications/rules/bulk-delete", json_body=body, node=self.node
                )
            self.exit_json(changed=True, notification=body)
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

        if state == "tested":
            if resource == "transport":
                if item_id is None:
                    self.fail_json(msg="Notification transport not found for testing.")
                if not self.check_mode:
                    resp = self.client.post(
                        f"/notifications/transports/{item_id}/test",
                        json_body=payload,
                        node=self.node,
                    )
                else:
                    resp = {"id": item_id}
            else:
                if item_id is not None:
                    payload.setdefault("id", item_id)
                if not self.check_mode:
                    resp = self.client.post(
                        "/notifications/rules/test", json_body=payload, node=self.node
                    )
                else:
                    resp = payload
            self.exit_json(changed=True, notification=resp or payload)
            return

        if state == "absent":
            if item_id is None:
                self.exit_json(changed=False, notification={})
                return
            if not self.check_mode:
                self.client.delete(f"{base_path}/{item_id}", node=self.node)
            self.exit_json(changed=True, notification=existing or {"id": item_id})
            return

        for key in ("name", "type", "enabled"):
            if self.params.get(key) is not None:
                payload[key] = self.params[key]

        if existing and item_id is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, notification=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"{base_path}/{item_id}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, notification=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(base_path, json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, notification=resp or payload)


def main() -> None:
    SylveNotificationModule()()


if __name__ == "__main__":
    main()
