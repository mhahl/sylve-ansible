#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_zfs_snapshot
short_description: Manage Sylve ZFS dataset snapshots and periodic snapshot schedules
description:
  - Create, roll back to, or delete ZFS dataset snapshots, or manage periodic snapshot schedules.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired snapshot or periodic schedule state.
    type: str
    choices:
      - present
      - absent
      - rolled_back
      - periodic_present
      - periodic_absent
    default: present
  dataset:
    description: Target dataset name or GUID.
    type: str
  name:
    description: Snapshot name (after C(@)) or full snapshot name (C(dataset@snap)).
    type: str
  guid:
    description: Snapshot or dataset GUID.
    type: str
  recursive:
    description: Create or delete snapshot recursively.
    type: bool
    default: false
  destroy_more_recent:
    description: Destroy newer snapshots during rollback.
    type: bool
    default: false
  periodic_id:
    description: Periodic snapshot schedule ID.
    type: int
  ids:
    description: List of periodic schedule IDs for bulk deletion.
    type: list
    elements: int
  prefix:
    description: Snapshot prefix for periodic schedules.
    type: str
  cron_expr:
    description: Cron expression for periodic schedules.
    type: str
  keep_last:
    description: Number of snapshots to retain for periodic schedules.
    type: int
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Create a ZFS snapshot of zroot/appdata
  sylve.cloud.sylve_zfs_snapshot:
    dataset: zroot/appdata
    name: daily-01
    recursive: true
    state: present
"""

RETURN = r"""
snapshot:
  description: Snapshot or periodic schedule details.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveZFSSnapshotModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": [
                "present",
                "absent",
                "rolled_back",
                "periodic_present",
                "periodic_absent",
            ],
            "default": "present",
        },
        "dataset": {"type": "str"},
        "name": {"type": "str"},
        "guid": {"type": "str"},
        "recursive": {"type": "bool", "default": False},
        "destroy_more_recent": {"type": "bool", "default": False},
        "periodic_id": {"type": "int"},
        "ids": {"type": "list", "elements": "int"},
        "prefix": {"type": "str"},
        "cron_expr": {"type": "str"},
        "keep_last": {"type": "int"},
        "data": {"type": "dict"},
    }

    def _resolve_guid(self, ident: str, dtype: str | None = None) -> tuple[str | None, dict]:
        params = {"type": dtype} if dtype else None
        items = self.client.get("/zfs/datasets", params=params, node=self.node) or []
        for ds in items if isinstance(items, list) else []:
            if not isinstance(ds, dict):
                continue
            g = str(ds.get("guid") or "")
            n = str(ds.get("name") or "")
            if ident.lower() in (g.lower(), n.lower()):
                return g, ds
        return None, {}

    def run(self) -> None:
        state = self.params["state"]
        payload: dict = dict(self.params.get("data") or {})

        if state in ("periodic_present", "periodic_absent"):
            if state == "periodic_absent" and self.params.get("ids"):
                body = {"ids": self.params["ids"]}
                if not self.check_mode:
                    self.client.delete(
                        "/zfs/datasets/snapshot/periodic", json_body=body, node=self.node
                    )
                self.exit_json(changed=True, snapshot=body)
                return

            jobs = self.client.get("/zfs/datasets/snapshot/periodic", node=self.node) or []
            pid = self.params.get("periodic_id")
            existing_p = None
            for j in jobs if isinstance(jobs, list) else []:
                if not isinstance(j, dict):
                    continue
                if pid is not None and j.get("id") == pid:
                    existing_p = j
                    break
                if (
                    self.params.get("prefix")
                    and j.get("prefix") == self.params["prefix"]
                    and (not self.params.get("guid") or j.get("guid") == self.params["guid"])
                ):
                    existing_p = j
                    pid = int(j["id"])
                    break

            if state == "periodic_absent":
                if pid is None:
                    self.exit_json(changed=False, snapshot={})
                    return
                if not self.check_mode:
                    self.client.delete(f"/zfs/datasets/snapshot/periodic/{pid}", node=self.node)
                self.exit_json(changed=True, snapshot=existing_p or {"id": pid})
                return

            for src, dst in (
                ("guid", "guid"),
                ("prefix", "prefix"),
                ("cron_expr", "cronExpr"),
                ("keep_last", "keepLast"),
                ("recursive", "recursive"),
            ):
                if self.params.get(src) is not None:
                    payload[dst] = self.params[src]
            if not payload.get("guid") and self.params.get("dataset"):
                ds_guid, _ = self._resolve_guid(self.params["dataset"])
                if ds_guid:
                    payload["guid"] = ds_guid

            if existing_p and pid is not None:
                if not self.subset_differs(payload, existing_p):
                    self.exit_json(changed=False, snapshot=existing_p)
                    return
                if not self.check_mode:
                    resp = self.client.patch(
                        f"/zfs/datasets/snapshot/periodic/{pid}",
                        json_body=payload,
                        node=self.node,
                    )
                else:
                    resp = payload
                self.exit_json(changed=True, snapshot=resp or payload)
                return

            if not self.check_mode:
                resp = self.client.post(
                    "/zfs/datasets/snapshot/periodic", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, snapshot=resp or payload)
            return

        dataset = self.params.get("dataset")
        name = self.params.get("name")
        snap_full = f"{dataset}@{name}" if dataset and name and "@" not in name else (name or "")
        snap_guid = self.params.get("guid")
        existing_snap = {}
        if snap_full or snap_guid:
            snap_guid, existing_snap = self._resolve_guid(
                snap_guid or snap_full, dtype="SNAPSHOT"
            )

        if state == "absent":
            if not snap_guid:
                self.exit_json(changed=False, snapshot={})
                return
            if not self.check_mode:
                self.client.delete(
                    f"/zfs/datasets/snapshot/{snap_guid}",
                    params={"recursive": self.params["recursive"]},
                    node=self.node,
                )
            self.exit_json(changed=True, snapshot=existing_snap or {"guid": snap_guid})
            return

        if state == "rolled_back":
            if not snap_guid:
                self.fail_json(msg="ZFS snapshot not found for rollback.")
            body = {"destroyMoreRecent": self.params["destroy_more_recent"]}
            if not self.check_mode:
                self.client.post(
                    f"/zfs/datasets/snapshot/{snap_guid}/rollback",
                    json_body=body,
                    node=self.node,
                )
            self.exit_json(changed=True, snapshot=existing_snap or {"guid": snap_guid})
            return

        if existing_snap:
            self.exit_json(changed=False, snapshot=existing_snap)
            return

        ds_ident = dataset or (snap_full.split("@")[0] if "@" in snap_full else "")
        snap_short = name.split("@")[-1] if name else ""
        ds_guid, _ = self._resolve_guid(ds_ident) if ds_ident else (self.params.get("guid"), {})
        if not ds_guid or not snap_short:
            self.fail_json(msg="Dataset (or guid) and snapshot name are required.")

        body = {
            "guid": ds_guid,
            "name": snap_short,
            "recursive": self.params["recursive"],
        }
        if not self.check_mode:
            resp = self.client.post("/zfs/datasets/snapshot", json_body=body, node=self.node)
        else:
            resp = body
        self.exit_json(changed=True, snapshot=resp or body)


def main() -> None:
    SylveZFSSnapshotModule()()


if __name__ == "__main__":
    main()
