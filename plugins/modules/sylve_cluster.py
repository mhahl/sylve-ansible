#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_cluster
short_description: Manage Sylve cluster formation, membership, resynchronization, and cluster notes
description:
  - Initialize a cluster, join an existing cluster, accept a pending join, leave/reset a node, remove a peer node,
    resynchronize Raft state, sync intra-cluster health, or manage cluster-wide notes.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  action:
    description: Cluster operation to perform.
    type: str
    choices:
      - create
      - join
      - accept_join
      - leave
      - remove_node
      - resync
      - sync_health
      - note_present
      - note_absent
    default: create
  ip:
    description: Bootstrap Raft IP address for C(action=create).
    type: str
  leader_ip:
    description: Cluster leader IP for C(action=join).
    type: str
  node_ip:
    description: Joining node Raft IP for C(action=join).
    type: str
  node_id:
    description: Node UUID or hostname for C(join) or C(remove_node).
    type: str
  cluster_key:
    description: Cluster join key for C(action=join).
    type: str
  retain_guests:
    description: Retain local VM and jail registrations when leaving or removing a node.
    type: bool
    default: true
  force:
    description: Force local cluster reset or force-remove an externally fenced peer node.
    type: bool
    default: false
  note_id:
    description: Cluster note ID.
    type: int
  ids:
    description: List of cluster note IDs for bulk deletion.
    type: list
    elements: int
  title:
    description: Cluster note title.
    type: str
  content:
    description: Cluster note content.
    type: str
  data:
    description: Additional raw request body fields.
    type: dict
"""

EXAMPLES = r"""
- name: Initialize a new Sylve cluster
  sylve.cloud.sylve_cluster:
    action: create
    ip: 10.0.0.10
"""

RETURN = r"""
cluster:
  description: Cluster or note operation result.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveClusterModule(SylveModule):
    argument_spec = {
        "action": {
            "type": "str",
            "choices": [
                "create",
                "join",
                "accept_join",
                "leave",
                "remove_node",
                "resync",
                "sync_health",
                "note_present",
                "note_absent",
            ],
            "default": "create",
        },
        "ip": {"type": "str"},
        "leader_ip": {"type": "str"},
        "node_ip": {"type": "str"},
        "node_id": {"type": "str"},
        "cluster_key": {"type": "str", "no_log": True},
        "retain_guests": {"type": "bool", "default": True},
        "force": {"type": "bool", "default": False},
        "note_id": {"type": "int"},
        "ids": {"type": "list", "elements": "int"},
        "title": {"type": "str"},
        "content": {"type": "str"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        act = self.params["action"]
        payload: dict = dict(self.params.get("data") or {})

        if act == "create":
            status = self.client.get("/cluster") or {}
            cfg = status.get("cluster") if isinstance(status, dict) else {}
            if isinstance(cfg, dict) and cfg.get("enabled"):
                self.exit_json(changed=False, cluster=status)
                return
            if self.params.get("ip"):
                payload["ip"] = self.params["ip"]
            if not self.check_mode:
                resp = self.client.post("/cluster", json_body=payload)
            else:
                resp = payload
            self.exit_json(changed=True, cluster=resp or payload)
            return

        if act == "join":
            for src, dst in (
                ("leader_ip", "leaderIp"),
                ("node_ip", "nodeIp"),
                ("node_id", "nodeId"),
                ("cluster_key", "clusterKey"),
            ):
                if self.params.get(src) is not None:
                    payload[dst] = self.params[src]
            if not self.check_mode:
                resp = self.client.post("/cluster/join", json_body=payload)
            else:
                resp = payload
            self.exit_json(changed=True, cluster=resp or payload)
            return

        if act == "accept_join":
            if not self.check_mode:
                resp = self.client.post("/cluster/accept-join", json_body=payload)
            else:
                resp = payload
            self.exit_json(changed=True, cluster=resp or payload)
            return

        if act == "leave":
            if not self.check_mode:
                if self.params["force"]:
                    resp = self.client.delete(
                        "/cluster/reset-node/force",
                        json_body={
                            "acknowledgeMembershipRepair": True,
                            "nodeExternallyFenced": True,
                        },
                    )
                else:
                    resp = self.client.delete(
                        "/cluster/reset-node",
                        json_body={"retainGuests": self.params["retain_guests"]},
                    )
            else:
                resp = {"action": "leave"}
            self.exit_json(changed=True, cluster=resp or {})
            return

        if act == "remove_node":
            target = self.params.get("node_id")
            if not target:
                self.fail_json(msg="'node_id' is required for action=remove_node.")
            uuid, _ = self.client.resolve_node_uuid(target)
            if not self.check_mode:
                if self.params["force"]:
                    resp = self.client.post(
                        "/cluster/remove-node/force",
                        json_body={"nodeId": uuid, "targetExternallyFenced": True},
                    )
                else:
                    resp = self.client.post(
                        "/cluster/remove-node",
                        json_body={
                            "nodeId": uuid,
                            "retainGuests": self.params["retain_guests"],
                        },
                    )
            else:
                resp = {"nodeId": uuid}
            self.exit_json(changed=True, cluster=resp or {"nodeId": uuid})
            return

        if act == "resync":
            if not self.check_mode:
                resp = self.client.post("/cluster/resync-state")
            else:
                resp = {}
            self.exit_json(changed=True, cluster=resp or {})
            return

        if act == "sync_health":
            if not self.check_mode:
                resp = self.client.post("/intra-cluster/sync-health", json_body=payload)
            else:
                resp = payload
            self.exit_json(changed=True, cluster=resp or payload)
            return

        if act == "note_absent" and self.params.get("ids"):
            body = {"ids": self.params["ids"]}
            if not self.check_mode:
                self.client.post("/cluster/notes/bulk-delete", json_body=body)
            self.exit_json(changed=True, cluster=body)
            return

        notes = self.client.get("/cluster/notes") or []
        nid = self.params.get("note_id")
        title = self.params.get("title")
        existing = None
        for n in notes if isinstance(notes, list) else []:
            if not isinstance(n, dict):
                continue
            if nid is not None and n.get("id") == nid:
                existing = n
                break
            if title and str(n.get("title") or "").lower() == title.lower():
                existing = n
                nid = int(n["id"])
                break

        if act == "note_absent":
            if nid is None:
                self.exit_json(changed=False, cluster={})
                return
            if not self.check_mode:
                self.client.delete(f"/cluster/notes/{nid}")
            self.exit_json(changed=True, cluster=existing or {"id": nid})
            return

        if title is not None:
            payload["title"] = title
        if self.params.get("content") is not None:
            payload["content"] = self.params["content"]

        if existing and nid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, cluster=existing)
                return
            if not self.check_mode:
                resp = self.client.put(f"/cluster/notes/{nid}", json_body=payload)
            else:
                resp = payload
            self.exit_json(changed=True, cluster=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/cluster/notes", json_body=payload)
        else:
            resp = payload
        self.exit_json(changed=True, cluster=resp or payload)


def main() -> None:
    SylveClusterModule()()


if __name__ == "__main__":
    main()
