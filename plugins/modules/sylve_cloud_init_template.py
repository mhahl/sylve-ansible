#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
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
    choices:
    - present
    - absent
    - query
    default: present
    required: false
  template_id:
    description: Numeric cloud-init template ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: Cloud-init template name.
    type: str
    required: false
  user_data:
    description: Cloud-init user-data YAML string (sent as C(user)).
    type: str
    required: false
  meta_data:
    description: Cloud-init meta-data YAML string (sent as C(meta)).
    type: str
    required: false
  network_config:
    description: Cloud-init network-config YAML string (sent as C(networkConfig)).
    type: str
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
    network_config: |
      version: 1
      config:
        - type: physical
          name: eth0
          subnets:
            - type: dhcp
    state: present

- name: Manage reusable Sylve cloud-init templates on a specific node using a named context
  sylve.cloud.sylve_cloud_init_template:
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
template:
  description: Cloud-init template details.
  returned: always
  type: raw
  sample: '{"id": 2, "name": "base-ssh"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveCloudInitTemplateModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "query"],
            "default": "present",
        },
        "template_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "user_data": {"type": "str"},
        "meta_data": {"type": "str"},
        "network_config": {"type": "str"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        templates = self.client.get("/utilities/cloud-init/templates", node=self.node) or []
        if state == "query":
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
            ("user_data", "user"),
            ("meta_data", "meta"),
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
