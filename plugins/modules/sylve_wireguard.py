#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_wireguard
short_description: Manage Sylve WireGuard VPN server, server peers, and outbound clients
description:
  - Initialize, update, enable/disable, or delete the WireGuard server, server peers, and outbound WireGuard clients.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  component:
    description: WireGuard component to manage.
    type: str
    choices: [server, peer, client]
    default: client
  state:
    description: Desired state.
    type: str
    choices: [present, absent, enabled, disabled]
    default: present
  id:
    description: Peer ID or Client ID.
    type: int
  name:
    description: Peer or client name.
    type: str
  endpoint:
    description: Remote WireGuard endpoint (host:port) for C(component=client).
    type: str
  allowed_ips:
    description: List of allowed IP CIDRs.
    type: list
    elements: str
  port:
    description: Listen port for C(component=server).
    type: int
  addresses:
    description: Server tunnel addresses for C(component=server).
    type: list
    elements: str
  enabled:
    description: Enabled flag.
    type: bool
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Initialize WireGuard server
  sylve.cloud.sylve_wireguard:
    component: server
    port: 51820
    addresses: ["10.99.0.1/24"]
    state: present
"""

RETURN = r"""
wireguard:
  description: WireGuard resource representation.
  returned: always
  type: dict
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveWireGuardModule(SylveModule):
    argument_spec = {
        "component": {
            "type": "str",
            "choices": ["server", "peer", "client"],
            "default": "client",
        },
        "state": {
            "type": "str",
            "choices": ["present", "absent", "enabled", "disabled"],
            "default": "present",
        },
        "id": {"type": "int"},
        "name": {"type": "str"},
        "endpoint": {"type": "str"},
        "allowed_ips": {"type": "list", "elements": "str"},
        "port": {"type": "int"},
        "addresses": {"type": "list", "elements": "str"},
        "enabled": {"type": "bool"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        comp = self.params["component"]
        state = self.params["state"]
        payload: dict = dict(self.params.get("data") or {})

        for src, dst in (
            ("name", "name"),
            ("endpoint", "endpoint"),
            ("allowed_ips", "allowedIPs"),
            ("port", "port"),
            ("addresses", "addresses"),
            ("enabled", "enabled"),
        ):
            if self.params.get(src) is not None:
                payload[dst] = self.params[src]

        if comp == "server":
            current = self.client.get("/network/wireguard/server", node=self.node) or {}
            if state == "absent":
                if not current:
                    self.exit_json(changed=False, wireguard={})
                    return
                if not self.check_mode:
                    self.client.delete("/network/wireguard/server", node=self.node)
                self.exit_json(changed=True, wireguard=current)
                return
            if state in ("enabled", "disabled"):
                body = {"enabled": state == "enabled"}
                if not self.check_mode:
                    resp = self.client.patch(
                        "/network/wireguard/server", json_body=body, node=self.node
                    )
                else:
                    resp = body
                self.exit_json(changed=True, wireguard=resp or body)
                return
            is_initialized = bool(
                isinstance(current, dict) and (current.get("id") or current.get("publicKey"))
            )
            if not is_initialized:
                if not self.check_mode:
                    resp = self.client.post(
                        "/network/wireguard/server", json_body=payload, node=self.node
                    )
                else:
                    resp = payload
                self.exit_json(changed=True, wireguard=resp or payload)
                return
            if not self.subset_differs(payload, current):
                self.exit_json(changed=False, wireguard=current)
                return
            if not self.check_mode:
                resp = self.client.put(
                    "/network/wireguard/server", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, wireguard=resp or payload)
            return

        if comp == "peer":
            srv = self.client.get("/network/wireguard/server", node=self.node) or {}
            peers = (srv.get("peers") if isinstance(srv, dict) else None) or []
            item_id = self.params.get("id")
            name = self.params.get("name")
            existing = None
            for p in peers if isinstance(peers, list) else []:
                if not isinstance(p, dict):
                    continue
                if item_id is not None and p.get("id") == item_id:
                    existing = p
                    break
                if name and str(p.get("name") or "").lower() == name.lower():
                    existing = p
                    item_id = int(p["id"])
                    break
            base_create = "/network/wireguard/server/peer"
            base_item = "/network/wireguard/server/peer"
        else:
            clients = self.client.get("/network/wireguard/clients", node=self.node) or []
            item_id = self.params.get("id")
            name = self.params.get("name")
            existing = None
            for c in clients if isinstance(clients, list) else []:
                if not isinstance(c, dict):
                    continue
                if item_id is not None and c.get("id") == item_id:
                    existing = c
                    break
                if name and str(c.get("name") or "").lower() == name.lower():
                    existing = c
                    item_id = int(c["id"])
                    break
            base_create = "/network/wireguard/clients"
            base_item = "/network/wireguard/clients"

        if state == "absent":
            if item_id is None:
                self.exit_json(changed=False, wireguard={})
                return
            if not self.check_mode:
                self.client.delete(f"{base_item}/{item_id}", node=self.node)
            self.exit_json(changed=True, wireguard=existing or {"id": item_id})
            return

        if state in ("enabled", "disabled"):
            if item_id is None:
                self.fail_json(msg=f"WireGuard {comp} not found to set state={state}.")
            body = {"enabled": state == "enabled"}
            if not self.check_mode:
                resp = self.client.patch(
                    f"{base_item}/{item_id}", json_body=body, node=self.node
                )
            else:
                resp = body
            self.exit_json(changed=True, wireguard=resp or body)
            return

        if existing and item_id is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, wireguard=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"{base_item}/{item_id}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, wireguard=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post(base_create, json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, wireguard=resp or payload)


def main() -> None:
    SylveWireGuardModule()()


if __name__ == "__main__":
    main()
