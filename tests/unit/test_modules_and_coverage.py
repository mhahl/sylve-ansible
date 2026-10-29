# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    ContextConfig,
    SylveClient,
)
from ansible_collections.sylve.cloud.plugins.modules import (
    sylve_api,
    sylve_jail,
    sylve_switch,
    sylve_vm,
    sylve_zfs_pool,
)

SWAGGER_PATH = Path("/home/mhahl/Developer/sylve-cli/docs/swagger.json")


class AnsibleExitJson(Exception):
    def __init__(self, kwargs: dict[str, Any]) -> None:
        self.kwargs = kwargs


class AnsibleFailJson(Exception):
    def __init__(self, kwargs: dict[str, Any]) -> None:
        self.kwargs = kwargs


def _run_module(
    monkeypatch: pytest.MonkeyPatch,
    module_cls: Any,
    params: dict[str, Any],
    fake_client: Any,
    check_mode: bool = False,
) -> dict[str, Any]:
    full_params = {
        "config_path": None,
        "context": None,
        "auth": None,
        "server": "https://sylve.test",
        "token": "tok",
        "username": None,
        "password": None,
        "auth_type": "sylve",
        "save_token": False,
        "node": "node1.lan",
        "validate_certs": True,
        "ca_cert": None,
        "timeout": 10.0,
        "wait": True,
        "poll_interval": 0.01,
    }
    for k, spec in module_cls.argument_spec.items():
        full_params[k] = spec.get("default")
    full_params.update(params)

    class _DummyAnsibleModule:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.params = full_params
            self.check_mode = check_mode

        def exit_json(self, **kwargs: Any) -> None:
            raise AnsibleExitJson(kwargs)

        def fail_json(self, **kwargs: Any) -> None:
            raise AnsibleFailJson(kwargs)

    monkeypatch.setattr(
        "ansible_collections.sylve.cloud.plugins.module_utils.sylve.AnsibleModule",
        _DummyAnsibleModule,
    )
    inst = module_cls()
    inst._client = fake_client
    with pytest.raises(AnsibleExitJson) as exc_info:
        inst()
    return exc_info.value.kwargs


class _MockClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Any]] = []
        self.context = ContextConfig(server="https://sylve.test", hostname="node1.lan")

    def close(self) -> None:
        pass

    def resolve_node_hostname(self, node: str | None = None) -> str:
        return node or "node1.lan"

    def resolve_vm(self, ident: Any, node: str | None = None) -> tuple[int, str, dict]:
        return 101, "node1.lan", {"rid": 101, "name": "web-01", "state": 5}

    def resolve_jail(self, ident: Any, node: str | None = None) -> tuple[int, str, dict]:
        return 201, "node1.lan", {"ctId": 201, "name": "app-01", "state": "STOPPED"}

    def get(self, path: str, **kwargs: Any) -> Any:
        self.calls.append(("GET", path, kwargs))
        if path == "/vm/101":
            return {"rid": 101, "name": "web-01", "cpuCores": 2, "ram": 2 * 1024**3, "state": 5}
        if path == "/jail/201":
            return {"ctId": 201, "name": "app-01", "cores": 2, "state": "STOPPED"}
        if path == "/network/switch":
            return {"standard": [{"id": 1, "name": "lan0", "mtu": 1500, "ports": ["em0"]}], "manual": []}
        if path == "/zfs/pools":
            return [{"name": "zroot", "pool_guid": "g-1"}]
        return {}

    def post(self, path: str, **kwargs: Any) -> Any:
        self.calls.append(("POST", path, kwargs))
        return {"taskId": 10, "outcome": "queued"}

    def put(self, path: str, **kwargs: Any) -> Any:
        self.calls.append(("PUT", path, kwargs))
        return {}

    def patch(self, path: str, **kwargs: Any) -> Any:
        self.calls.append(("PATCH", path, kwargs))
        return {}

    def delete(self, path: str, **kwargs: Any) -> Any:
        self.calls.append(("DELETE", path, kwargs))
        return {}

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        self.calls.append((method, path, kwargs))
        return {"ok": True}


def test_vm_module_idempotent_and_start(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ansible_collections.sylve.cloud.plugins.module_utils.sylve.wait_for_lifecycle_task",
        lambda *a, **kw: {"id": 10, "status": "completed"},
    )
    client = _MockClient()
    res = _run_module(
        monkeypatch,
        sylve_vm.SylveVMModule,
        {"name": "web-01", "cpu_cores": 2, "ram": "2G", "state": "present"},
        client,
    )
    assert res["changed"] is False

    res_start = _run_module(
        monkeypatch,
        sylve_vm.SylveVMModule,
        {"name": "web-01", "state": "started"},
        client,
    )
    assert res_start["changed"] is True
    assert any(c[0] == "POST" and c[1] == "/vm/101/actions/start" for c in client.calls)


def test_jail_and_switch_check_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _MockClient()
    res = _run_module(
        monkeypatch,
        sylve_jail.SylveJailModule,
        {"name": "app-01", "cores": 4, "state": "started"},
        client,
        check_mode=True,
    )
    assert res["changed"] is True
    assert not any(c[0] in ("PUT", "POST") for c in client.calls)

    sw_res = _run_module(
        monkeypatch,
        sylve_switch.SylveSwitchModule,
        {"name": "lan0", "ports": ["em0"], "mtu": 1500, "state": "present"},
        client,
    )
    assert sw_res["changed"] is False


def test_zfs_pool_scrub_and_generic_api(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _MockClient()
    res = _run_module(
        monkeypatch,
        sylve_zfs_pool.SylveZFSPoolModule,
        {"name": "zroot", "state": "scrubbed"},
        client,
    )
    assert res["changed"] is True
    assert any(c[0] == "POST" and c[1] == "/zfs/pools/g-1/scrub" for c in client.calls)

    api_res = _run_module(
        monkeypatch,
        sylve_api.SylveAPIModule,
        {"method": "GET", "path": "/auth/preferences"},
        client,
    )
    assert api_res["changed"] is False
    assert api_res["data"] == {"ok": True}


@pytest.mark.skipif(not SWAGGER_PATH.exists(), reason="swagger.json not present")
def test_all_swagger_paths_covered() -> None:
    spec = json.loads(SWAGGER_PATH.read_text(encoding="utf-8"))
    swagger_paths = set(spec.get("paths", {}).keys())
    assert len(swagger_paths) == 336

    modules_dir = Path(__file__).resolve().parents[2] / "plugins"
    source_text = "\n".join(
        p.read_text(encoding="utf-8") for p in modules_dir.rglob("*.py")
    )

    covered_prefixes = (
        "/auth/",
        "/basic/",
        "/certificates",
        "/cluster",
        "/directory-services/",
        "/disk",
        "/dynamic-dns/",
        "/events/stream",
        "/health/",
        "/info/",
        "/intra-cluster/",
        "/iscsi/",
        "/jail",
        "/mdns/",
        "/network/",
        "/notifications",
        "/samba/",
        "/system/",
        "/tasks/",
        "/utilities/",
        "/vm",
        "/vnc/",
        "/zfs/",
    )
    unmapped = [
        p for p in swagger_paths if not p.startswith(covered_prefixes)
    ]
    assert not unmapped, f"Unmapped Swagger prefixes: {unmapped}"
    assert "class SylveAPIModule" in source_text


def test_all_modules_and_inventory_import_and_docs_valid() -> None:
    import importlib
    import yaml

    root = Path(__file__).resolve().parents[2]
    mod_files = sorted((root / "plugins" / "modules").glob("sylve_*.py"))
    assert len(mod_files) == 45

    runtime = yaml.safe_load((root / "meta" / "runtime.yml").read_text(encoding="utf-8"))
    assert set(runtime["action_groups"]["sylve"]) == {mf.stem for mf in mod_files}

    for mf in mod_files:
        mod_name = f"ansible_collections.sylve.cloud.plugins.modules.{mf.stem}"
        mod = importlib.import_module(mod_name)
        doc = yaml.safe_load(mod.DOCUMENTATION)
        assert isinstance(doc, dict) and doc.get("module") == mf.stem
        assert yaml.safe_load(mod.EXAMPLES) is not None
        assert isinstance(yaml.safe_load(mod.RETURN), dict)

    inv_mod = importlib.import_module("ansible_collections.sylve.cloud.plugins.inventory.sylve")
    inv_doc = yaml.safe_load(inv_mod.DOCUMENTATION)
    assert inv_doc.get("name") == "sylve"

