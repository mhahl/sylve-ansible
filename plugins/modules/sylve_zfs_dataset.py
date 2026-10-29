#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_zfs_dataset
short_description: Manage Sylve ZFS filesystems and volumes
description:
  - Create, edit, flash, delete, or bulk-delete ZFS filesystems and volumes (zvols).
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired dataset state or action.
    type: str
    choices: [present, absent, flashed]
    default: present
  type:
    description: Dataset type.
    type: str
    choices: [filesystem, volume]
    default: filesystem
  parent:
    description: Parent dataset path when creating (e.g. C(zroot)).
    type: str
  name:
    description: Dataset leaf name (or full path for lookup).
    type: str
  guid:
    description: Dataset GUID.
    type: str
  guids:
    description: List of dataset GUIDs for bulk deletion (C(DELETE /zfs/datasets)).
    type: list
    elements: str
  size:
    description: Volume size (e.g. C(10G)) when C(type=volume).
    type: str
  properties:
    description: ZFS dataset properties dictionary.
    type: dict
  image_uuid:
    description: Image UUID when C(state=flashed) on a volume.
    type: str
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Create a ZFS filesystem zroot/appdata
  sylve.cloud.sylve_zfs_dataset:
    type: filesystem
    parent: zroot
    name: appdata
    state: present
"""

RETURN = r"""
dataset:
  description: ZFS dataset details.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveZFSDatasetModule(SylveModule):
    argument_spec = {
        "state": {"type": "str", "choices": ["present", "absent", "flashed"], "default": "present"},
        "type": {"type": "str", "choices": ["filesystem", "volume"], "default": "filesystem"},
        "parent": {"type": "str"},
        "name": {"type": "str"},
        "guid": {"type": "str"},
        "guids": {"type": "list", "elements": "str"},
        "size": {"type": "str"},
        "properties": {"type": "dict"},
        "image_uuid": {"type": "str"},
        "data": {"type": "dict"},
    }

    def _find_dataset(self, full_name: str | None) -> tuple[str | None, dict]:
        dtype = self.params["type"].upper()
        datasets = self.client.get("/zfs/datasets", params={"type": dtype}, node=self.node) or []
        guid = self.params.get("guid")
        for ds in datasets if isinstance(datasets, list) else []:
            if not isinstance(ds, dict):
                continue
            ds_guid = str(ds.get("guid") or "")
            ds_name = str(ds.get("name") or "")
            if guid and ds_guid.lower() == guid.lower():
                return ds_guid, ds
            if full_name and ds_name.lower() == full_name.lower():
                return ds_guid, ds
        return guid, {}

    def run(self) -> None:
        state = self.params["state"]
        dtype = self.params["type"]

        if state == "absent" and self.params.get("guids"):
            body = {"guids": self.params["guids"]}
            if not self.check_mode:
                self.client.delete("/zfs/datasets", json_body=body, node=self.node)
            self.exit_json(changed=True, dataset=body)
            return

        parent = self.params.get("parent")
        name = self.params.get("name")
        full_name = f"{parent}/{name}" if parent and name and "/" not in name else name
        guid, existing = self._find_dataset(full_name)

        if state == "absent":
            if not guid or not existing:
                self.exit_json(changed=False, dataset={})
                return
            if not self.check_mode:
                self.client.delete(f"/zfs/datasets/{dtype}/{guid}", node=self.node)
            self.exit_json(changed=True, dataset=existing)
            return

        payload: dict = dict(self.params.get("data") or {})

        if state == "flashed":
            if not guid:
                self.fail_json(msg="ZFS volume not found for flashing.")
            if self.params.get("image_uuid"):
                payload["uuid"] = self.params["image_uuid"]
            if not self.check_mode:
                resp = self.client.post(
                    f"/zfs/datasets/volume/{guid}/flash", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, dataset=resp or payload)
            return

        props = dict(self.params.get("properties") or {})
        if dtype == "volume" and self.params.get("size"):
            props.setdefault("volsize", self.params["size"])

        if existing and guid:
            if not props and not payload:
                self.exit_json(changed=False, dataset=existing)
                return
            payload.setdefault("properties", props)
            if not self.check_mode:
                resp = self.client.patch(
                    f"/zfs/datasets/{dtype}/{guid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, dataset=resp or payload)
            return

        if parent:
            payload["parent"] = parent
        if name:
            payload["name"] = name.split("/")[-1] if parent else name
        payload["properties"] = props

        if not self.check_mode:
            resp = self.client.post(
                f"/zfs/datasets/{dtype}", json_body=payload, node=self.node
            )
        else:
            resp = payload
        self.exit_json(changed=True, dataset=resp or payload)


def main() -> None:
    SylveZFSDatasetModule()()


if __name__ == "__main__":
    main()
