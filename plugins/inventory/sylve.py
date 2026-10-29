# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
name: sylve
short_description: Sylve dynamic inventory source for nodes, Bhyve VMs, and FreeBSD Jails
description:
  - Discovers Sylve cluster nodes, Bhyve virtual machines, and FreeBSD jails using the same C(~/.config/sylve/config.yaml)
    configuration and environment variables as C(sylve-cli).
  - Populates host variables and groups (C(sylve_nodes), C(sylve_vms), C(sylve_jails), C(sylve_node_<node>), C(sylve_state_<state>)).
extends_documentation_fragment:
  - constructed
options:
  plugin:
    description: Token that ensures this is a source file for the C(sylve) plugin.
    required: true
    choices: ['sylve.cloud.sylve', 'sylve']
  config_path:
    description: Path to C(config.yaml).
    type: path
  context:
    description: Named Sylve context to use.
    type: str
  server:
    description: Override Sylve server URL.
    type: str
  token:
    description: Override Bearer token.
    type: str
  username:
    description: Username for login if token is missing/expired.
    type: str
  password:
    description: Password for login if token is missing/expired.
    type: str
  auth_type:
    description: Authentication provider (C(sylve) or C(pam)).
    type: str
    default: sylve
  validate_certs:
    description: Validate TLS certificates.
    type: bool
  ca_cert:
    description: Custom CA certificate path.
    type: path
  include_nodes:
    description: Add Sylve cluster nodes to the inventory.
    type: bool
    default: true
  include_vms:
    description: Add Bhyve VMs to the inventory.
    type: bool
    default: true
  include_jails:
    description: Add FreeBSD jails to the inventory.
    type: bool
    default: true
  resolve_guest_ips:
    description: Query QEMU guest-agent (C(/vm/{rid}/guest-agent)) and jail guest-info (C(/jail/{ctid}/guest-info)) for running guest IPs.
    type: bool
    default: true
"""

EXAMPLES = r"""
# sylve.yml
plugin: sylve.cloud.sylve
context: prod
include_nodes: true
include_vms: true
include_jails: true
"""

import re
from typing import Any

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    SylveError,
    create_client_from_params,
    format_vm_state,
)


def _safe_group(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.strip().lower())


def _extract_first_ip(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    for iface in data.get("interfaces") or data.get("networkInterfaces") or []:
        if not isinstance(iface, dict):
            continue
        if str(iface.get("name") or "").startswith("lo"):
            continue
        for addr in iface.get("ipAddresses") or iface.get("ipv4") or iface.get("addresses") or []:
            if isinstance(addr, dict):
                ip = str(addr.get("ip") or addr.get("ipAddress") or addr.get("address") or "")
            else:
                ip = str(addr or "")
            ip = ip.split("/")[0].strip()
            if ip and not ip.startswith(("127.", "::1", "fe80:")):
                return ip
    return None


class InventoryModule(BaseInventoryPlugin, Constructable):
    NAME = "sylve.cloud.sylve"

    def verify_file(self, path: str) -> bool:
        if super().verify_file(path):
            return path.endswith(("sylve.yml", "sylve.yaml"))
        return False

    def _add_host_with_vars(
        self, hostname: str, groups: list[str], hostvars: dict[str, Any], strict: bool
    ) -> None:
        self.inventory.add_host(hostname)
        for g in groups:
            self.inventory.add_group(g)
            self.inventory.add_child(g, hostname)
        for k, v in hostvars.items():
            self.inventory.set_variable(hostname, k, v)
        self._set_composite_vars(self.get_option("compose"), hostvars, hostname, strict=strict)
        self._add_host_to_composed_groups(
            self.get_option("groups"), hostvars, hostname, strict=strict
        )
        self._add_host_to_keyed_groups(
            self.get_option("keyed_groups"), hostvars, hostname, strict=strict
        )

    def parse(self, inventory: Any, loader: Any, path: str, cache: bool = True) -> None:
        super().parse(inventory, loader, path, cache)
        self._read_config_data(path)
        strict = bool(self.get_option("strict"))

        params = {
            "config_path": self.get_option("config_path"),
            "context": self.get_option("context"),
            "server": self.get_option("server"),
            "token": self.get_option("token"),
            "username": self.get_option("username"),
            "password": self.get_option("password"),
            "auth_type": self.get_option("auth_type") or "sylve",
            "validate_certs": self.get_option("validate_certs"),
            "ca_cert": self.get_option("ca_cert"),
        }
        _, client = create_client_from_params(params)
        resolve_ips = bool(self.get_option("resolve_guest_ips"))

        try:
            if self.get_option("include_nodes"):
                for node in client.get_cluster_nodes(refresh=True):
                    host = str(node.get("hostname") or "")
                    if not host:
                        continue
                    hvars = {
                        "sylve_type": "node",
                        "sylve_node_uuid": node.get("nodeUUID") or node.get("nodeUuid"),
                        "sylve_status": node.get("status") or "online",
                        "sylve_node": host,
                        "sylve_raw": node,
                    }
                    self._add_host_with_vars(
                        host,
                        ["sylve_nodes", f"sylve_status_{_safe_group(str(hvars['sylve_status']))}"],
                        hvars,
                        strict,
                    )

            if self.get_option("include_vms") or self.get_option("include_jails"):
                for node_res in client.get_cluster_resources(refresh=True):
                    node_host = str(node_res.get("hostname") or "local")
                    node_group = f"sylve_node_{_safe_group(node_host)}"

                    if self.get_option("include_vms"):
                        for vm in node_res.get("vms") or []:
                            if not isinstance(vm, dict):
                                continue
                            rid = vm.get("rid")
                            name = str(vm.get("name") or f"vm-{rid}")
                            state_str = format_vm_state(vm.get("state"))
                            hvars = {
                                "sylve_type": "vm",
                                "sylve_rid": rid,
                                "sylve_name": name,
                                "sylve_node": node_host,
                                "sylve_state": state_str.lower(),
                                "sylve_raw": vm,
                            }
                            if resolve_ips and state_str == "RUNNING" and rid is not None:
                                try:
                                    ga = client.get(f"/vm/{rid}/guest-agent", node=node_host)
                                    ip = _extract_first_ip(ga)
                                    if ip:
                                        hvars["ansible_host"] = ip
                                except SylveError:
                                    pass
                            self._add_host_with_vars(
                                name,
                                [
                                    "sylve_vms",
                                    node_group,
                                    f"sylve_state_{_safe_group(state_str)}",
                                ],
                                hvars,
                                strict,
                            )

                    if self.get_option("include_jails"):
                        for jail in node_res.get("jails") or []:
                            if not isinstance(jail, dict):
                                continue
                            ctid = jail.get("ctId")
                            name = str(jail.get("name") or f"jail-{ctid}")
                            state_str = str(jail.get("state") or "UNKNOWN").upper()
                            hvars = {
                                "sylve_type": "jail",
                                "sylve_ctid": ctid,
                                "sylve_name": name,
                                "sylve_node": node_host,
                                "sylve_state": state_str.lower(),
                                "sylve_raw": jail,
                            }
                            if resolve_ips and state_str in ("RUNNING", "ACTIVE") and ctid is not None:
                                try:
                                    gi = client.get(f"/jail/{ctid}/guest-info", node=node_host)
                                    ip = _extract_first_ip(gi)
                                    if ip:
                                        hvars["ansible_host"] = ip
                                except SylveError:
                                    pass
                            self._add_host_with_vars(
                                name,
                                [
                                    "sylve_jails",
                                    node_group,
                                    f"sylve_state_{_safe_group(state_str)}",
                                ],
                                hvars,
                                strict,
                            )
        finally:
            client.close()
