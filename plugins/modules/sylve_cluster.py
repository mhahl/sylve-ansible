#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_cluster
short_description: Manage Sylve cluster formation, membership, resynchronization, and cluster notes
description:
- Initialize a cluster, join an existing cluster, accept a pending join, leave/reset a node, remove a peer node, resynchronize
  Raft state, sync intra-cluster health, or manage cluster-wide notes.
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
    required: false
  ip:
    description: Bootstrap Raft IP address for C(action=create).
    type: str
    required: false
  leader_ip:
    description: Cluster leader IP for C(action=join).
    type: str
    required: false
  node_ip:
    description: Joining node Raft IP for C(action=join).
    type: str
    required: false
  node_id:
    description: Node UUID or hostname for C(join) or C(remove_node).
    type: str
    required: false
  cluster_key:
    description: Cluster join key for C(action=join).
    type: str
    required: false
  retain_guests:
    description: Retain local VM and jail registrations when leaving or removing a node.
    type: bool
    default: true
    required: false
  force:
    description: Force local cluster reset or force-remove an externally fenced peer node.
    type: bool
    default: false
    required: false
  note_id:
    description: Cluster note ID.
    type: int
    required: false
  ids:
    description: List of cluster note IDs for bulk deletion.
    type: list
    elements: int
    required: false
  title:
    description: Cluster note title.
    type: str
    required: false
  content:
    description: Cluster note content.
    type: str
    required: false
  data:
    description: Additional raw request body fields.
    type: dict
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
- module: sylve.cloud.sylve_api
  description: Execute any Sylve REST API endpoint directly.
- name: sylve.cloud collection README
  link: https://github.com/mhahl/sylve-ansible
  description: Authentication, configuration, and inventory plugin usage.
"""

EXAMPLES = r"""
- name: Initialize a new Sylve cluster
  sylve.cloud.sylve_cluster:
    action: create
    ip: 10.0.0.10

- name: Manage Sylve cluster formation, membership, resynchronization, and cluster notes on a specific node using a named context
  sylve.cloud.sylve_cluster:
    context: prod
    node: node1.lan
    action: sync_health
    data: {}
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
cluster:
  description: Cluster or note operation result.
  returned: always
  type: raw
  sample: '{"enabled": true, "leaderId": "node-1"}'
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
