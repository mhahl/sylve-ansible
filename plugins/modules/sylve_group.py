#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_group
short_description: Manage Sylve authentication groups and group membership
description:
- List, create, or delete authentication groups, and replace group membership.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired group state.
    type: str
    choices:
    - present
    - absent
    - query
    default: present
    required: false
  group_id:
    description: Numeric group ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: Group name.
    type: str
    required: false
  members:
    description: List of user IDs or usernames belonging to the group.
    type: list
    elements: raw
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
- name: Create an operators group and set members
  sylve.cloud.sylve_group:
    name: operators
    members: [1, 2]
    state: present

- name: Manage Sylve authentication groups and group membership on a specific node using a named context
  sylve.cloud.sylve_group:
    context: prod
    node: node1.lan
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
group:
  description: Group details.
  returned: always
  type: raw
  sample: '{"id": 2, "name": "operators"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveGroupModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "query"],
            "default": "present",
        },
        "group_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "members": {"type": "list", "elements": "raw"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        groups = self.client.get("/auth/groups", node=self.node) or []
        if state == "query":
            self.exit_json(changed=False, group=groups)
            return

        gid = self.params.get("group_id")
        name = self.params.get("name")
        existing = None
        for g in groups if isinstance(groups, list) else []:
            if not isinstance(g, dict):
                continue
            if gid is not None and g.get("id") == gid:
                existing = g
                break
            if name and str(g.get("name") or "").lower() == name.lower():
                existing = g
                gid = int(g["id"])
                break

        if state == "absent":
            if gid is None:
                self.exit_json(changed=False, group={})
                return
            if not self.check_mode:
                self.client.delete(f"/auth/groups/{gid}", node=self.node)
            self.exit_json(changed=True, group=existing or {"id": gid})
            return

        changed = False
        payload: dict = dict(self.params.get("data") or {})
        if name:
            payload.setdefault("name", name)

        if existing is None:
            changed = True
            if not self.check_mode:
                resp = self.client.post("/auth/groups", json_body=payload, node=self.node)
                if isinstance(resp, dict) and resp.get("id") is not None:
                    gid = int(resp["id"])
                    existing = resp
            else:
                existing = payload

        if self.params.get("members") is not None and gid is not None:
            cur_members = existing.get("members") if isinstance(existing, dict) else None
            if cur_members != self.params["members"]:
                changed = True
                if not self.check_mode:
                    self.client.put(
                        f"/auth/groups/{gid}/members",
                        json_body={"members": self.params["members"]},
                        node=self.node,
                    )

        self.exit_json(changed=changed, group=existing or payload)


def main() -> None:
    SylveGroupModule()()


if __name__ == "__main__":
    main()
