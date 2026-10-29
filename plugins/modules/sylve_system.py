#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_system
short_description: Manage Sylve system initialization, pools, services, tunables, PCI passthrough, and files
description:
- Initialize Sylve, configure usable ZFS pools, control system services, set sysctl tunables, manage PCI passthrough (PPT)
  devices, run health checks, or manage remote files via file-explorer endpoints.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  action:
    description: System operation to perform.
    type: str
    choices:
    - info
    - initialize
    - set_pools
    - service
    - tunable_set
    - ppt_enable
    - ppt_import
    - ppt_prepare
    - ppt_disable
    - file_list
    - file_create
    - file_copy_move
    - file_delete
    - file_rename
    - file_upload
    - file_upload_revert
    - file_download
    - health
    default: info
    required: false
  pools:
    description: List of usable ZFS pool names for C(action=set_pools).
    type: list
    elements: str
    required: false
  service:
    description: Service name for C(action=service).
    type: str
    required: false
  ppt_id:
    description: PCI passthrough device ID for C(action=ppt_disable).
    type: int
    required: false
  path:
    description: Remote file or directory path for file-explorer operations.
    type: str
    required: false
  src:
    description: Local source file for C(action=file_upload).
    type: path
    required: false
  dest:
    description: Local destination file for C(action=file_download).
    type: path
    required: false
  data:
    description: Request payload dictionary.
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
- name: Configure usable ZFS pools
  sylve.cloud.sylve_system:
    action: set_pools
    pools: [zroot, tank]

- name: Manage Sylve system initialization, pools, services, tunables, PCI passthrough, and files on a specific node using a named context
  sylve.cloud.sylve_system:
    context: prod
    node: node1.lan
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
system:
  description: System operation result.
  returned: always
  type: raw
  sample: '{"pools": ["zroot", "tank"]}'
"""

from pathlib import Path
from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveSystemModule(SylveModule):
    argument_spec = {
        "action": {
            "type": "str",
            "choices": [
                "info",
                "initialize",
                "set_pools",
                "service",
                "tunable_set",
                "ppt_enable",
                "ppt_import",
                "ppt_prepare",
                "ppt_disable",
                "file_list",
                "file_create",
                "file_copy_move",
                "file_delete",
                "file_rename",
                "file_upload",
                "file_upload_revert",
                "file_download",
                "health",
            ],
            "default": "info",
        },
        "pools": {"type": "list", "elements": "str"},
        "service": {"type": "str"},
        "ppt_id": {"type": "int"},
        "path": {"type": "str"},
        "src": {"type": "path"},
        "dest": {"type": "path"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        act = self.params["action"]
        payload: dict = dict(self.params.get("data") or {})

        if act == "info":
            res = {
                "basic_settings": self.client.get("/basic/settings", node=self.node),
                "system_settings": self.client.get("/system/basic-settings", node=self.node),
                "pci_devices": self.client.get("/system/pci-devices", node=self.node),
                "ppt_devices": self.client.get("/system/ppt-devices", node=self.node),
                "tunables": self.client.get("/system/tunables/remote", node=self.node),
            }
            self.exit_json(changed=False, system=res)
            return

        if act == "health":
            res = {
                "basic": self.client.request("GET", "/health/basic", require_auth=False),
                "http": self.client.request("GET", "/health/http", require_auth=False),
            }
            self.exit_json(changed=False, system=res)
            return

        if act == "file_list":
            res = self.client.get(
                "/system/file-explorer",
                params={"id": self.params.get("path") or "/"},
                node=self.node,
            )
            self.exit_json(changed=False, system=res)
            return

        if self.check_mode:
            self.exit_json(changed=True, system=payload)
            return

        if act == "initialize":
            resp = self.client.request(
                "POST", "/basic/initialize", json_body=payload, require_auth=False
            )
        elif act == "set_pools":
            if self.params.get("pools") is not None:
                payload["pools"] = self.params["pools"]
            resp = self.client.put(
                "/system/basic-settings/pools", json_body=payload, node=self.node
            )
        elif act == "service":
            svc = self.params.get("service")
            resp = self.client.patch(
                f"/system/basic-settings/services/{svc}", json_body=payload, node=self.node
            )
        elif act == "tunable_set":
            resp = self.client.put("/system/tunables", json_body=payload, node=self.node)
        elif act == "ppt_enable":
            resp = self.client.post("/system/ppt-devices", json_body=payload, node=self.node)
        elif act == "ppt_import":
            resp = self.client.post(
                "/system/ppt-devices/import", json_body=payload, node=self.node
            )
        elif act == "ppt_prepare":
            resp = self.client.post(
                "/system/ppt-devices/prepare", json_body=payload, node=self.node
            )
        elif act == "ppt_disable":
            resp = self.client.delete(
                f"/system/ppt-devices/{self.params.get('ppt_id')}", node=self.node
            )
        elif act == "file_create":
            resp = self.client.post(
                "/system/file-explorer", json_body=payload, node=self.node
            )
        elif act == "file_copy_move":
            resp = self.client.post(
                "/system/file-explorer/copy-or-move-batch", json_body=payload, node=self.node
            )
        elif act == "file_delete":
            resp = self.client.post(
                "/system/file-explorer/delete", json_body=payload, node=self.node
            )
        elif act == "file_rename":
            resp = self.client.post(
                "/system/file-explorer/rename", json_body=payload, node=self.node
            )
        elif act == "file_upload":
            resp = self.client.post(
                "/system/file-explorer/upload",
                params={"path": self.params.get("path")},
                upload_file=self.params.get("src"),
                node=self.node,
            )
        elif act == "file_upload_revert":
            resp = self.client.delete(
                "/system/file-explorer/upload", json_body=payload, node=self.node
            )
        else:
            out_path = self.client.download_file(
                "/system/file-explorer/download",
                self.params.get("dest") or Path("download.bin"),
                params={"id": self.params.get("path")},
                node=self.node,
            )
            resp = {"dest": str(out_path)}

        self.exit_json(changed=True, system=resp or payload)


def main() -> None:
    SylveSystemModule()()


if __name__ == "__main__":
    main()
