#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_api
short_description: Execute any Sylve Swagger HTTP API request directly
description:
- Universal module for invoking any Sylve REST API endpoint (GET, POST, PUT, PATCH, DELETE), including file uploads, binary
  downloads, and unauthenticated endpoints.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  method:
    description: HTTP method.
    type: str
    choices:
    - GET
    - POST
    - PUT
    - PATCH
    - DELETE
    default: GET
    required: false
  path:
    description: API path without the C(/api) prefix (e.g. C(/cluster/nodes), C(/auth/preferences)).
    type: str
    required: true
  params:
    description: Query parameters dictionary.
    type: dict
    required: false
  body:
    description: JSON request body.
    type: raw
    aliases:
    - data
    required: false
  upload_file:
    description: Local file path to upload via multipart form-data.
    type: path
    required: false
  output_file:
    description: Local destination path to stream a binary download to.
    type: path
    required: false
  require_auth:
    description: Whether to attach the Bearer token header.
    type: bool
    default: true
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
- name: sylve.cloud collection README
  link: https://github.com/mhahl/sylve-ansible
  description: Authentication, configuration, and inventory plugin usage.
"""

EXAMPLES = r"""
- name: Query user preferences via sylve_api
  sylve.cloud.sylve_api:
    method: GET
    path: /auth/preferences
  register: prefs

- name: Execute any Sylve Swagger HTTP API request directly on a specific node using a named context
  sylve.cloud.sylve_api:
    context: prod
    node: node1.lan
    method: GET
    path: /cluster/nodes
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
data:
  description: Unwrapped response data from the Sylve API.
  returned: always
  type: raw
  sample: '{"nodes": [{"hostname": "node1.lan", "status": "online"}]}'
task:
  description: Completed lifecycle, migration, replication, or backup task details.
  returned: when a task is executed and C(wait=true)
  type: dict
  sample: '{"id": 42, "status": "completed"}'
"""

from pathlib import Path
from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveAPIModule(SylveModule):
    argument_spec = {
        "method": {
            "type": "str",
            "choices": ["GET", "POST", "PUT", "PATCH", "DELETE"],
            "default": "GET",
        },
        "path": {"type": "str", "required": True},
        "params": {"type": "dict"},
        "body": {"type": "raw", "aliases": ["data"]},
        "upload_file": {"type": "path"},
        "output_file": {"type": "path"},
        "require_auth": {"type": "bool", "default": True},
    }

    def run(self) -> None:
        method = self.params["method"].upper()
        path = self.params["path"]
        is_mutating = method in ("POST", "PUT", "PATCH", "DELETE")

        if self.check_mode and is_mutating:
            self.exit_json(changed=True, data={"method": method, "path": path})
            return

        if self.params.get("output_file"):
            out = self.client.download_file(
                path,
                Path(self.params["output_file"]),
                params=self.params.get("params"),
                node=self.node,
            )
            self.exit_json(changed=True, data={"output_file": str(out)})
            return

        res = self.client.request(
            method,
            path,
            params=self.params.get("params"),
            json_body=self.params.get("body"),
            upload_file=self.params.get("upload_file"),
            node=self.node,
            require_auth=self.params["require_auth"],
        )
        task = self.wait_task(res, node=self.node) if is_mutating else None
        self.exit_json(changed=is_mutating, data=res, task=task)


def main() -> None:
    SylveAPIModule()()


if __name__ == "__main__":
    main()
