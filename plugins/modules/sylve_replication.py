#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_replication
short_description: Manage Sylve HA replication policies, manual runs, failovers, and replication events
description:
  - Create, update, delete, run, or fail over cluster HA replication policies, and query replication events.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired replication policy state or action.
    type: str
    choices: [present, absent, run, failover, events]
    default: present
  policy_id:
    description: Replication policy numeric ID.
    type: int
    aliases: [id]
  event_id:
    description: Replication event ID when querying or waiting for an event.
    type: int
  name:
    description: Policy name.
    type: str
  guest_type:
    description: Guest type (C(vm) or C(jail)).
    type: str
  guest_id:
    description: VM RID or Jail CTID.
    type: int
  targets:
    description: "List of target node dicts (e.g. C([{'nodeId': 'uuid', 'weight': 100}]))."
    type: list
    elements: dict
  cron_expr:
    description: Cron schedule expression.
    type: str
    default: "*/15 * * * *"
  failover_mode:
    description: Policy failover mode (C(manual) or C(auto)) or failover action mode (C(safe) or C(force)).
    type: str
  target_node:
    description: Target node hostname or UUID when C(state=failover).
    type: str
  move_pinned_source:
    description: Update pinned source node during failover.
    type: bool
    default: true
  confirm_data_loss:
    description: Acknowledge potential data loss for forced failover.
    type: bool
    default: false
  enabled:
    description: Enable the policy.
    type: bool
    default: true
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Create an HA replication policy for VM 101
  sylve.cloud.sylve_replication:
    name: web-01-ha
    guest_type: vm
    guest_id: 101
    targets:
      - nodeId: node2-uuid
        weight: 100
    state: present
"""

RETURN = r"""
replication:
  description: Replication policy or event details.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    SylveModule,
    wait_for_replication_event,
)


class SylveReplicationModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": ["present", "absent", "run", "failover", "events"],
            "default": "present",
        },
        "policy_id": {"type": "int", "aliases": ["id"]},
        "event_id": {"type": "int"},
        "name": {"type": "str"},
        "guest_type": {"type": "str"},
        "guest_id": {"type": "int"},
        "targets": {"type": "list", "elements": "dict"},
        "cron_expr": {"type": "str", "default": "*/15 * * * *"},
        "failover_mode": {"type": "str"},
        "target_node": {"type": "str"},
        "move_pinned_source": {"type": "bool", "default": True},
        "confirm_data_loss": {"type": "bool", "default": False},
        "enabled": {"type": "bool", "default": True},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        pid = self.params.get("policy_id")
        ev_id = self.params.get("event_id")

        if state == "events":
            if ev_id is not None:
                if self.wait:
                    ev = wait_for_replication_event(
                        self.client,
                        ev_id,
                        timeout=self.timeout,
                        poll_interval=self.poll_interval,
                    )
                else:
                    ev = self.client.get(f"/cluster/replication/events/{ev_id}")
                self.exit_json(changed=False, replication=ev)
                return
            evs = self.client.get(
                "/cluster/replication/events",
                params={"policyId": pid} if pid is not None else None,
            )
            self.exit_json(changed=False, replication=evs)
            return

        policies = self.client.get("/cluster/replication/policies") or []
        name = self.params.get("name")
        existing = None
        for p in policies if isinstance(policies, list) else []:
            if not isinstance(p, dict):
                continue
            if pid is not None and p.get("id") == pid:
                existing = p
                break
            if name and str(p.get("name") or "").lower() == name.lower():
                existing = p
                pid = int(p["id"])
                break

        if state == "absent":
            if pid is None:
                self.exit_json(changed=False, replication={})
                return
            if not self.check_mode:
                self.client.delete(f"/cluster/replication/policies/{pid}")
            self.exit_json(changed=True, replication=existing or {"id": pid})
            return

        if state == "run":
            if pid is None:
                self.fail_json(msg="Replication policy not found.")
            if not self.check_mode:
                resp = self.client.post(f"/cluster/replication/policies/{pid}/run")
            else:
                resp = {"id": pid}
            self.exit_json(changed=True, replication=resp or {"id": pid})
            return

        if state == "failover":
            if pid is None:
                self.fail_json(msg="Replication policy not found for failover.")
            body = {
                "mode": self.params.get("failover_mode") or "safe",
                "movePinnedSource": self.params["move_pinned_source"],
                "confirmDataLoss": self.params["confirm_data_loss"],
            }
            if self.params.get("target_node"):
                tuuid, _ = self.client.resolve_node_uuid(self.params["target_node"])
                body["targetNodeId"] = tuuid
            if not self.check_mode:
                resp = self.client.post(
                    f"/cluster/replication/policies/{pid}/failover", json_body=body
                )
            else:
                resp = body
            self.exit_json(changed=True, replication=resp or body)
            return

        payload: dict = dict(self.params.get("data") or {})
        for src, dst in (
            ("name", "name"),
            ("guest_type", "guestType"),
            ("guest_id", "guestId"),
            ("targets", "targets"),
            ("cron_expr", "cronExpr"),
            ("failover_mode", "failoverMode"),
            ("enabled", "enabled"),
        ):
            if self.params.get(src) is not None:
                payload[dst] = self.params[src]

        if existing and pid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, replication=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/cluster/replication/policies/{pid}", json_body=payload
                )
            else:
                resp = payload
            self.exit_json(changed=True, replication=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/cluster/replication/policies", json_body=payload)
        else:
            resp = payload
        self.exit_json(changed=True, replication=resp or payload)


def main() -> None:
    SylveReplicationModule()()


if __name__ == "__main__":
    main()
