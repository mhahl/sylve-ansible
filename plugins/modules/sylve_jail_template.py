#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
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
    choices: [present, deployed, absent]
    default: present
  template_id:
    description: Jail template numeric ID.
    type: int
  name:
    description: Template name (for capture or lookup) or deployed jail name.
    type: str
  source_jail:
    description: Source jail CTID or name when capturing a template (C(state=present)).
    type: str
  deploy_options:
    description: Deployment payload when C(state=deployed).
    type: dict
"""

EXAMPLES = r"""
- name: Capture jail 201 as a template
  sylve.cloud.sylve_jail_template:
    name: web-jail-template
    source_jail: 201
    state: present
"""

RETURN = r"""
template:
  description: Jail template representation or deployment response.
  returned: always
  type: dict
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
