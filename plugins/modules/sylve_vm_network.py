#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_vm_network
short_description: Manage network interfaces attached to a Sylve Bhyve VM
description:
  - Attach, update, or detach network interfaces on a Bhyve VM.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired network attachment state.
    type: str
    choices: [present, absent]
    default: present
  vm:
    description: VM RID or name.
    type: str
    required: true
  network_id:
    description: VM network attachment ID.
    type: int
  switch_name:
    description: Switch name to attach.
    type: str
    aliases: [switch]
  emulation:
    description: NIC emulation type (e.g. C(virtio-net), C(e1000)).
    type: str
  mac_id:
    description: MAC object ID.
    type: int
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Attach VM 101 to switch lan0
  sylve.cloud.sylve_vm_network:
    vm: 101
    switch_name: lan0
    emulation: virtio-net
    state: present
"""

RETURN = r"""
network:
  description: VM network attachment details.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveVMNetworkModule(SylveModule):
    argument_spec = {
        "state": {"type": "str", "choices": ["present", "absent"], "default": "present"},
        "vm": {"type": "str", "required": True},
        "network_id": {"type": "int"},
        "switch_name": {"type": "str", "aliases": ["switch"]},
        "emulation": {"type": "str"},
        "mac_id": {"type": "int"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        rid, host, _ = self.client.resolve_vm(self.params["vm"], node=self.node)
        vm_detail = self.client.get(f"/vm/{rid}", node=host) or {}
        networks = vm_detail.get("networks") or []
        net_id = self.params.get("network_id")
        existing = None
        for net in networks:
            if not isinstance(net, dict):
                continue
            if net_id is not None and net.get("id") == net_id:
                existing = net
                break
            if self.params.get("switch_name") and net.get("switchName") == self.params["switch_name"]:
                existing = net
                net_id = net.get("id")
                break

        if self.params["state"] == "absent":
            if net_id is None:
                self.exit_json(changed=False, network={})
                return
            if not self.check_mode:
                self.client.delete(f"/vm/{rid}/networks/{net_id}", node=host)
            self.exit_json(changed=True, network=existing or {"id": net_id})
            return

        payload: dict = dict(self.params.get("data") or {})
        if self.params.get("switch_name") is not None:
            payload["switchName"] = self.params["switch_name"]
        if self.params.get("emulation") is not None:
            payload["emulation"] = self.params["emulation"]
        if self.params.get("mac_id") is not None:
            payload["macId"] = self.params["mac_id"]

        if existing and net_id is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, network=existing)
                return
            if not self.check_mode:
                resp = self.client.patch(
                    f"/vm/{rid}/networks/{net_id}", json_body=payload, node=host
                )
            else:
                resp = payload
            self.exit_json(changed=True, network=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(f"/vm/{rid}/networks", json_body=payload, node=host)
        else:
            resp = payload
        self.exit_json(changed=True, network=resp or payload)


def main() -> None:
    SylveVMNetworkModule()()


if __name__ == "__main__":
    main()
