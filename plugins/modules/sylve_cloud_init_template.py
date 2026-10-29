#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_cloud_init_template
short_description: Manage reusable Sylve cloud-init templates
description:
  - List, create, update, or delete reusable cloud-init templates on Sylve.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired template state.
    type: str
    choices: [present, absent, info]
    default: present
  template_id:
    description: Numeric cloud-init template ID.
    type: int
    aliases: [id]
  name:
    description: Cloud-init template name.
    type: str
  description:
    description: Template description.
    type: str
  user_data:
    description: Cloud-init user-data YAML string.
    type: str
  meta_data:
    description: Cloud-init meta-data YAML string.
    type: str
  network_config:
    description: Cloud-init network-config YAML string.
    type: str
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Create a reusable cloud-init template
  sylve.cloud.sylve_cloud_init_template:
    name: base-ssh
    user_data: |
      #cloud-config
      users:
        - name: freebsd
          sudo: ALL=(ALL) NOPASSWD:ALL
    meta_data: |
      instance-id: base-ssh
    state: present
"""

RETURN = r"""
template:
  description: Cloud-init template details.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveCloudInitTemplateModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "info"],
            "default": "present",
        },
        "template_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "description": {"type": "str"},
        "user_data": {"type": "str"},
        "meta_data": {"type": "str"},
        "network_config": {"type": "str"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        templates = self.client.get("/utilities/cloud-init/templates", node=self.node) or []
        if state == "info":
            self.exit_json(changed=False, template=templates)
            return

        tid = self.params.get("template_id")
        name = self.params.get("name")
        existing = None
        for t in templates if isinstance(templates, list) else []:
            if not isinstance(t, dict):
                continue
            if tid is not None and t.get("id") == tid:
                existing = t
                break
            if name and str(t.get("name") or "").lower() == name.lower():
                existing = t
                tid = int(t["id"])
                break

        if state == "absent":
            if tid is None:
                self.exit_json(changed=False, template={})
                return
            if not self.check_mode:
                self.client.delete(
                    f"/utilities/cloud-init/templates/{tid}", node=self.node
                )
            self.exit_json(changed=True, template=existing or {"id": tid})
            return

        payload: dict = dict(self.params.get("data") or {})
        for src, dst in (
            ("name", "name"),
            ("description", "description"),
            ("user_data", "userData"),
            ("meta_data", "metaData"),
            ("network_config", "networkConfig"),
        ):
            if self.params.get(src) is not None:
                payload[dst] = self.params[src]

        if existing and tid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, template=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/utilities/cloud-init/templates/{tid}",
                    json_body=payload,
                    node=self.node,
                )
            else:
                resp = payload
            self.exit_json(changed=True, template=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(
                "/utilities/cloud-init/templates", json_body=payload, node=self.node
            )
        else:
            resp = payload
        self.exit_json(changed=True, template=resp or payload)


def main() -> None:
    SylveCloudInitTemplateModule()()


if __name__ == "__main__":
    main()
