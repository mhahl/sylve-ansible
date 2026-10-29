#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_vm_template
short_description: Manage Sylve Bhyve VM templates
description:
  - Capture a shut-off VM as a reusable template, deploy VMs from a template, or delete a VM template.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired template state or action.
    type: str
    choices: [present, deployed, absent]
    default: present
  template_id:
    description: VM template numeric ID.
    type: int
  name:
    description: Template name (for capture or lookup) or deployed VM name.
    type: str
  source_vm:
    description: Shut-off source VM RID or name when capturing a template (C(state=present)).
    type: str
  deploy_options:
    description: Deployment payload when C(state=deployed) (e.g. C(mode), C(rid), C(name), C(startRid), C(count), C(namePrefix), C(storagePools)).
    type: dict
"""

EXAMPLES = r"""
- name: Capture VM 101 as a template
  sylve.cloud.sylve_vm_template:
    name: freebsd-14-base
    source_vm: 101
    state: present
"""

RETURN = r"""
template:
  description: VM template representation or deployment response.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveVMTemplateModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "deployed", "absent"],
            "default": "present",
        },
        "template_id": {"type": "int"},
        "name": {"type": "str"},
        "source_vm": {"type": "str"},
        "deploy_options": {"type": "dict"},
    }

    def _find_template(self) -> tuple[int | None, str | None, dict]:
        tid = self.params.get("template_id")
        name = self.params.get("name")
        for host, items in self.client.fan_out_get("/vm/templates", node=self.node):
            for t in items if isinstance(items, list) else []:
                if not isinstance(t, dict):
                    continue
                if tid is not None and t.get("id") == tid:
                    detail = self.client.get(f"/vm/templates/{tid}", node=host)
                    return int(tid), host, detail if isinstance(detail, dict) else t
                if name and str(t.get("name") or "").lower() == name.lower():
                    found_id = int(t["id"])
                    detail = self.client.get(f"/vm/templates/{found_id}", node=host)
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
                self.client.delete(f"/vm/templates/{tid}", node=host)
            self.exit_json(changed=True, template=existing)
            return

        if state == "deployed":
            if tid is None:
                self.fail_json(msg="VM template not found for deployment.")
            body = dict(self.params.get("deploy_options") or {})
            if self.params.get("name") and "name" not in body:
                body["name"] = self.params["name"]
            body.setdefault("mode", "single")
            if self.check_mode:
                self.exit_json(changed=True, template=body)
                return
            resp = self.client.post(f"/vm/templates/{tid}/vms", json_body=body, node=host)
            task = self.wait_task(resp, node=host)
            self.exit_json(changed=True, template=resp or body, task=task)
            return

        if existing:
            self.exit_json(changed=False, template=existing)
            return

        if not self.params.get("source_vm") or not self.params.get("name"):
            self.fail_json(msg="Both 'source_vm' and 'name' are required to capture a VM template.")
        rid, vm_host, _ = self.client.resolve_vm(self.params["source_vm"], node=self.node)
        body = {"name": self.params["name"]}
        if self.check_mode:
            self.exit_json(changed=True, template=body)
            return
        resp = self.client.post(f"/vm/{rid}/templates", json_body=body, node=vm_host)
        task = self.wait_task(resp, node=vm_host)
        self.exit_json(changed=True, template=resp or body, task=task)


def main() -> None:
    SylveVMTemplateModule()()


if __name__ == "__main__":
    main()
