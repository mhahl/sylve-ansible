# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

import pytest

from ansible_collections.sylve.cloud.plugins.inventory.sylve import (
    InventoryModule,
    _extract_first_ip,
    _safe_group,
)
from ansible.parsing.dataloader import DataLoader


class _FakeInventory:
    def __init__(self) -> None:
        self.hosts: dict[str, dict[str, Any]] = {}
        self.groups: dict[str, list[str]] = {}

    def add_host(self, hostname: str, **kwargs: Any) -> None:
        self.hosts.setdefault(hostname, {"groups": [], "vars": {}})

    def add_group(self, group: str) -> None:
        self.groups.setdefault(group, [])

    def add_child(self, group: str, hostname: str) -> None:
        self.groups.setdefault(group, []).append(hostname)
        self.hosts.setdefault(hostname, {"groups": [], "vars": {}})["groups"].append(group)

    def set_variable(self, hostname: str, key: str, value: Any) -> None:
        self.hosts.setdefault(hostname, {"groups": [], "vars": {}})["vars"][key] = value


class _FakeClient:
    def get_cluster_nodes(self, refresh: bool = False) -> list[dict[str, Any]]:
        return [{"hostname": "node1.lan", "nodeUUID": "u-1", "status": "online"}]

    def get_cluster_resources(self, refresh: bool = False) -> list[dict[str, Any]]:
        return [
            {
                "hostname": "node1.lan",
                "vms": [{"rid": 101, "name": "web-01", "state": 1}],
                "jails": [{"ctId": 201, "name": "app-01", "state": "RUNNING"}],
            }
        ]

    def get(self, path: str, **kwargs: Any) -> Any:
        return {
            "interfaces": [
                {"name": "lo0", "ipAddresses": [{"ip": "127.0.0.1"}]},
                {"name": "vtnet0", "ipAddresses": [{"ip": "10.0.0.5/24"}]},
            ]
        }

    def close(self) -> None:
        pass


def test_safe_group_and_ip_extraction() -> None:
    assert _safe_group("Node1.LAN") == "node1_lan"
    assert (
        _extract_first_ip({"interfaces": [{"name": "vtnet0", "ipAddresses": ["10.0.0.5/24"]}]})
        == "10.0.0.5"
    )
    assert _extract_first_ip({"interfaces": [{"name": "lo0", "ipAddresses": ["127.0.0.1"]}]}) is None
    assert _extract_first_ip({}) is None


def test_inventory_populates_nodes_vms_and_jails(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    options: dict[str, Any] = {
        "config_path": None,
        "context": "prod",
        "server": None,
        "token": "tok",
        "username": None,
        "password": None,
        "auth_type": "sylve",
        "validate_certs": True,
        "ca_cert": None,
        "include_nodes": True,
        "include_vms": True,
        "include_jails": True,
        "resolve_guest_ips": True,
        "strict": False,
        "compose": {},
        "groups": {},
        "keyed_groups": {},
    }
    monkeypatch.setattr(
        InventoryModule, "get_option", lambda self, key: options.get(key)
    )
    monkeypatch.setattr(
        "ansible_collections.sylve.cloud.plugins.inventory.sylve.create_client_from_params",
        lambda params: ("prod", _FakeClient()),
    )

    cfg = tmp_path / "sylve.yml"
    cfg.write_text("plugin: sylve.cloud.sylve\n", encoding="utf-8")

    inventory = _FakeInventory()
    InventoryModule().parse(inventory, loader=DataLoader(), path=str(cfg))

    assert "node1.lan" in inventory.hosts
    assert "web-01" in inventory.hosts
    assert "app-01" in inventory.hosts
    assert "sylve_nodes" in inventory.groups
    assert "sylve_vms" in inventory.groups
    assert "sylve_jails" in inventory.groups
    assert inventory.hosts["web-01"]["vars"]["ansible_host"] == "10.0.0.5"
    assert inventory.hosts["app-01"]["vars"]["ansible_host"] == "10.0.0.5"
    assert inventory.hosts["node1.lan"]["vars"]["sylve_type"] == "node"
