#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_jail_template
short_description: Manage Sylve FreeBSD jail templates
description:
- Capture a jail as a template, deploy jails from a template, or delete a jail template.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired template state or action.
    type: str
    choices:
    - present
    - deployed
    - absent
    default: present
    required: false
  template_id:
    description: Jail template numeric ID.
    type: int
    required: false
  name:
    description: Template name (for capture or lookup) or deployed jail name.
    type: str
    required: false
  source_jail:
    description: Source jail CTID or name when capturing a template (C(state=present)).
    type: str
    required: false
  deploy_options:
    description: Deployment payload when C(state=deployed).
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
- name: Capture jail 201 as a template
  sylve.cloud.sylve_jail_template:
    name: web-jail-template
    source_jail: 201
    state: present

- name: Manage Sylve FreeBSD jail templates on a specific node using a named context
  sylve.cloud.sylve_jail_template:
    context: prod
    node: node1.lan
    name: web-jail-template
    source_jail: app-01
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
template:
  description: Jail template representation or deployment response.
  returned: always
  type: dict
  sample: '{"id": 3, "name": "web-jail-template"}'
task:
  description: Completed lifecycle, migration, replication, or backup task details.
  returned: when a task is executed and C(wait=true)
  type: dict
  sample: '{"id": 42, "status": "completed"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveJailTemplateModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "deployed", "absent"],
            "default": "present",
        },
        "template_id": {"type": "int"},
        "name": {"type": "str"},
        "source_jail": {"type": "str"},
        "deploy_options": {"type": "dict"},
    }

    def _find_template(self) -> tuple[int | None, str | None, dict]:
        tid = self.params.get("template_id")
        name = self.params.get("name")
        for host, items in self.client.fan_out_get("/jail/templates", node=self.node):
            for t in items if isinstance(items, list) else []:
                if not isinstance(t, dict):
                    continue
                if tid is not None and t.get("id") == tid:
                    detail = self.client.get(f"/jail/templates/{tid}", node=host)
                    return int(tid), host, detail if isinstance(detail, dict) else t
                if name and str(t.get("name") or "").lower() == name.lower():
                    found_id = int(t["id"])
                    detail = self.client.get(f"/jail/templates/{found_id}", node=host)
                    return found_id, host, detail if isinstance(detail, dict) else t
        return None, self.client.resolve_node_hostname(self.node), {}

    def run(self) -> None:
        state = self.params["state"]
        tid, host, existing = self._find_template()

        if state == "absent":
            if tid is None:
                self.exit_json(changed=False, template={})
                return
            if not self.check_mode:
                self.client.delete(f"/jail/templates/{tid}", node=host)
            self.exit_json(changed=True, template=existing)
            return

        if state == "deployed":
            if tid is None:
                self.fail_json(msg="Jail template not found for deployment.")
            body = dict(self.params.get("deploy_options") or {})
            if self.params.get("name") and "name" not in body:
                body["name"] = self.params["name"]
            body.setdefault("mode", "single")
            if self.check_mode:
                self.exit_json(changed=True, template=body)
                return
            resp = self.client.post(f"/jail/templates/{tid}/jails", json_body=body, node=host)
            task = self.wait_task(resp, node=host)
            self.exit_json(changed=True, template=resp or body, task=task)
            return

        if existing:
            self.exit_json(changed=False, template=existing)
            return

        if not self.params.get("source_jail") or not self.params.get("name"):
            self.fail_json(
                msg="Both 'source_jail' and 'name' are required to capture a jail template."
            )
        ctid, j_host, _ = self.client.resolve_jail(self.params["source_jail"], node=self.node)
        body = {"name": self.params["name"]}
        if self.check_mode:
            self.exit_json(changed=True, template=body)
            return
        resp = self.client.post(f"/jail/{ctid}/templates", json_body=body, node=j_host)
        task = self.wait_task(resp, node=j_host)
        self.exit_json(changed=True, template=resp or body, task=task)


def main() -> None:
    SylveJailTemplateModule()()


if __name__ == "__main__":
    main()
