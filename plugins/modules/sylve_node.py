#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_node
short_description: Manage Sylve cluster node maintenance drain, reboot, and host notes
description:
- Drain a cluster node for maintenance (failing over HA policies and migrating/stopping VMs and Jails), initiate a node reboot,
  or manage per-host notes.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  action:
    description: Node operation to perform.
    type: str
    choices:
    - drain
    - reboot
    - note_present
    - note_absent
    default: drain
    required: false
  target_node:
    description: Destination node hostname or UUID when C(action=drain). Auto-selects least-loaded node if omitted.
    type: str
    required: false
  stop_only:
    description: Gracefully stop all guests on the node instead of migrating them when C(action=drain).
    type: bool
    default: false
    required: false
  fallback_stop:
    description: Stop guests that fail migration preflight instead of failing the drain.
    type: bool
    default: false
    required: false
  running_only:
    description: Only drain currently running guests.
    type: bool
    default: false
    required: false
  note_id:
    description: Host note ID.
    type: int
    required: false
  ids:
    description: Host note IDs for bulk deletion (C(DELETE /info/notes)).
    type: list
    elements: int
    required: false
  title:
    description: Host note title.
    type: str
    required: false
  content:
    description: Host note content.
    type: str
    required: false
  timeout:
    description: HTTP request and task polling timeout in seconds. Raised for this module because drain operations chain failovers and migrations.
    type: float
    default: 1800.0
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
- name: Drain node1.lan for maintenance
  sylve.cloud.sylve_node:
    node: node1.lan
    action: drain
    target_node: node2.lan
    fallback_stop: true

- name: Drain node for maintenance on a specific node using a named context
  sylve.cloud.sylve_node:
    context: prod
    node: node1.lan
    action: drain
    target_node: node2.lan
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
node_result:
  description: Operation result.
  returned: always
  type: raw
  sample: '{"node": "node1.lan"}'
task:
  description: Completed lifecycle, migration, replication, or backup task details.
  returned: when a task is executed and C(wait=true)
  type: dict
  sample: '{"id": 42, "status": "completed"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    SylveError,
    SylveModule,
    format_vm_state,
)


class SylveNodeModule(SylveModule):
    default_timeout = 1800.0
    argument_spec = {
        "action": {
            "type": "str",
            "choices": ["drain", "reboot", "note_present", "note_absent"],
            "default": "drain",
        },
        "target_node": {"type": "str"},
        "stop_only": {"type": "bool", "default": False},
        "fallback_stop": {"type": "bool", "default": False},
        "running_only": {"type": "bool", "default": False},
        "note_id": {"type": "int"},
        "ids": {"type": "list", "elements": "int"},
        "title": {"type": "str"},
        "content": {"type": "str"},
    }

    def _drain_node(self) -> None:
        source_ident = self.node or self.client.context.hostname
        if not source_ident:
            self.fail_json(msg="'node' is required for action=drain.")
        source_uuid, source_host = self.client.resolve_node_uuid(source_ident)
        all_nodes = self.client.get_cluster_nodes(refresh=True)
        candidates = [
            n
            for n in all_nodes
            if str(n.get("hostname") or "").lower() != source_host.lower()
            and str(n.get("status") or "online").lower() == "online"
        ]

        dest_uuid, dest_host = "", ""
        if self.params.get("target_node") and not self.params["stop_only"]:
            dest_uuid, dest_host = self.client.resolve_node_uuid(self.params["target_node"])
        elif candidates and not self.params["stop_only"]:
            best = min(
                candidates,
                key=lambda n: (
                    float(n.get("memoryUsage") or 0.0) * 0.7
                    + float(n.get("cpuUsage") or 0.0) * 0.3,
                    len(n.get("guestIDs") or []),
                ),
            )
            dest_uuid = str(best.get("nodeUUID") or best.get("nodeUuid") or "")
            dest_host = str(best.get("hostname") or "")

        resources = self.client.get_cluster_resources(refresh=True)
        vms, jails = [], []
        for entry in resources:
            if str(entry.get("hostname") or "").lower() == source_host.lower():
                vms = [v for v in (entry.get("vms") or []) if isinstance(v, dict)]
                jails = [j for j in (entry.get("jails") or []) if isinstance(j, dict)]
                break

        policies_by_guest: dict[tuple[str, int], dict] = {}
        try:
            for pol in self.client.get("/cluster/replication/policies") or []:
                if isinstance(pol, dict) and pol.get("enabled", True):
                    active_node = str(pol.get("activeNodeId") or pol.get("sourceNodeId") or "")
                    if active_node.lower() == source_uuid.lower():
                        policies_by_guest[
                            (str(pol.get("guestType") or "").lower(), int(pol.get("guestId") or 0))
                        ] = pol
        except SylveError:
            pass

        guests: list[tuple[str, int, str, bool]] = []
        for vm in vms:
            rid = int(vm.get("rid") or 0)
            st = format_vm_state(vm.get("state"))
            guests.append(("vm", rid, str(vm.get("name") or rid), st in ("RUNNING", "PAUSED")))
        for jail in jails:
            ctid = int(jail.get("ctId") or 0)
            st = str(jail.get("state") or "").upper()
            guests.append(("jail", ctid, str(jail.get("name") or ctid), st in ("RUNNING", "ACTIVE")))

        plan: list[dict] = []
        changed = False
        for gtype, gid, gname, is_running in guests:
            if self.params["running_only"] and not is_running:
                continue
            pol = policies_by_guest.get((gtype, gid))
            if not self.params["stop_only"] and pol is not None:
                pol_id = int(pol["id"])
                changed = True
                if not self.check_mode:
                    self.client.post(
                        f"/cluster/replication/policies/{pol_id}/failover",
                        json_body={
                            "targetNodeId": dest_uuid,
                            "mode": "safe",
                            "movePinnedSource": True,
                            "confirmDataLoss": False,
                        },
                    )
                plan.append(
                    {"guest_type": gtype, "guest_id": gid, "name": gname, "action": "ha-failover"}
                )
                continue

            if not self.params["stop_only"] and dest_uuid:
                try:
                    self.client.get(
                        "/tasks/migration/validate",
                        params={
                            "guestType": gtype,
                            "guestId": gid,
                            "targetNodeUuid": dest_uuid,
                        },
                        node=source_host,
                    )
                    changed = True
                    if not self.check_mode:
                        endpoint = (
                            f"/vm/{gid}/migrations" if gtype == "vm" else f"/jail/{gid}/migrations"
                        )
                        resp = self.client.post(
                            endpoint,
                            json_body={"targetNodeUuid": dest_uuid},
                            node=source_host,
                        )
                        self.wait_task(resp, node=source_host)
                    plan.append(
                        {
                            "guest_type": gtype,
                            "guest_id": gid,
                            "name": gname,
                            "action": "migrate",
                            "target": dest_host,
                        }
                    )
                    continue
                except SylveError:
                    if not self.params["fallback_stop"]:
                        raise

            if is_running and (self.params["stop_only"] or self.params["fallback_stop"]):
                act = "shutdown" if gtype == "vm" else "stop"
                changed = True
                if not self.check_mode:
                    endpoint = (
                        f"/vm/{gid}/actions/{act}"
                        if gtype == "vm"
                        else f"/jail/{gid}/actions/{act}"
                    )
                    resp = self.client.post(endpoint, node=source_host)
                    self.wait_task(resp, node=source_host)
                plan.append({"guest_type": gtype, "guest_id": gid, "name": gname, "action": act})

        self.exit_json(changed=changed, plan=plan, node_result={"node": source_host})

    def run(self) -> None:
        act = self.params["action"]
        if act == "drain":
            self._drain_node()
            return

        if act == "reboot":
            if not self.check_mode:
                self.client.post("/basic/system/reboot", node=self.node)
            self.exit_json(changed=True, node_result={"rebooted": True})
            return

        if act == "note_absent" and self.params.get("ids"):
            body = {"ids": self.params["ids"]}
            if not self.check_mode:
                self.client.delete("/info/notes", json_body=body, node=self.node)
            self.exit_json(changed=True, node_result=body)
            return

        notes = self.client.get("/info/notes", node=self.node) or []
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
                self.exit_json(changed=False, node_result={})
                return
            if not self.check_mode:
                self.client.delete(f"/info/notes/{nid}", node=self.node)
            self.exit_json(changed=True, node_result=existing or {"id": nid})
            return

        payload = {
            "title": title or (existing.get("title") if existing else ""),
            "content": (
                self.params["content"]
                if self.params.get("content") is not None
                else (existing.get("content") if existing else "")
            ),
        }
        if existing and nid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, node_result=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/info/notes/{nid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, node_result=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/info/notes", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, node_result=resp or payload)


def main() -> None:
    SylveNodeModule()()


if __name__ == "__main__":
    main()
