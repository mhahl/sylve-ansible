# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import pytest

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    ContextConfig,
    ResourceNotFoundError,
    SessionExpiredError,
    SylveAPIError,
    SylveClient,
    SylveConfig,
    create_client_from_params,
    extract_token_expiry,
    load_config,
    normalize_server_url,
    parse_size,
    save_config,
    wait_for_lifecycle_task,
)


def _make_jwt(exp: int) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode().rstrip("=")
    payload = (
        base64.urlsafe_b64encode(json.dumps({"sub": "admin", "exp": exp}).encode())
        .decode()
        .rstrip("=")
    )
    return f"{header}.{payload}.sig"


class _FakeHTTPResponse:
    def __init__(self, status: int, body: Any) -> None:
        self.status = status
        if isinstance(body, (dict, list)):
            self._raw = json.dumps(body).encode("utf-8")
        elif isinstance(body, bytes):
            self._raw = body
        else:
            self._raw = str(body).encode("utf-8")

    def read(self) -> bytes:
        return self._raw


def test_parse_size() -> None:
    assert parse_size("2G") == 2 * 1024**3
    assert parse_size("512M") == 512 * 1024**2
    assert parse_size(1024) == 1024
    with pytest.raises(Exception):
        parse_size("invalid")


def test_config_roundtrip_and_cli_compatibility(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SYLVE_CONFIG", raising=False)
    monkeypatch.delenv("SYLVE_CONTEXT", raising=False)
    monkeypatch.delenv("SYLVE_SERVER", raising=False)
    monkeypatch.delenv("SYLVE_TOKEN", raising=False)

    token = _make_jwt(4102444800)  # 2100-01-01
    cfg = SylveConfig(
        current_context="prod",
        contexts={
            "prod": ContextConfig(
                server="sylve.example.test/api/",
                username="admin",
                token=token,
                expires_at=extract_token_expiry(token),
                hostname="node1.lan",
                node_id="uuid-1",
            )
        },
    )
    cfg_file = tmp_path / "config.yaml"
    save_config(cfg, cfg_file)
    assert (cfg_file.stat().st_mode & 0o777) == 0o600

    loaded = load_config(cfg_file)
    name, active = loaded.get_active_context()
    assert name == "prod"
    assert active.server == "https://sylve.example.test"
    assert not active.is_token_expired()


def test_auto_login_when_token_expired(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    expired_token = _make_jwt(1000)
    fresh_token = _make_jwt(4102444800)
    cfg = SylveConfig(
        current_context="lab",
        contexts={
            "lab": ContextConfig(
                server="https://lab.example.test",
                token=expired_token,
            )
        },
    )
    cfg_file = tmp_path / "config.yaml"
    save_config(cfg, cfg_file)

    calls: list[tuple[str, str]] = []

    def fake_open_url(url: str, method: str = "GET", **kwargs: Any) -> _FakeHTTPResponse:
        calls.append((method, url))
        if url.endswith("/api/auth/login"):
            return _FakeHTTPResponse(
                200,
                {
                    "status": "success",
                    "data": {
                        "token": fresh_token,
                        "hostname": "lab1.lan",
                        "nodeId": "node-lab-1",
                    },
                },
            )
        return _FakeHTTPResponse(200, {"status": "success", "data": {}})

    monkeypatch.setattr(
        "ansible_collections.sylve.cloud.plugins.module_utils.sylve.open_url",
        fake_open_url,
    )

    ctx_name, client = create_client_from_params(
        {
            "config_path": str(cfg_file),
            "username": "admin",
            "password": "secret",
            "save_token": True,
        }
    )
    assert ctx_name == "lab"
    assert client.context.token == fresh_token
    assert calls[0][0] == "POST"
    reloaded = load_config(cfg_file)
    assert reloaded.contexts["lab"].token == fresh_token


def test_client_routing_and_resolvers(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _make_jwt(4102444800)
    ctx = ContextConfig(server="https://cluster.test", token=token, hostname="node1.lan")
    client = SylveClient(ctx)

    captured_headers: list[dict[str, str]] = []

    def fake_open_url(
        url: str, method: str = "GET", headers: dict[str, str] | None = None, **kwargs: Any
    ) -> _FakeHTTPResponse:
        captured_headers.append(dict(headers or {}))
        if url.endswith("/api/cluster/nodes"):
            return _FakeHTTPResponse(
                200,
                {
                    "status": "success",
                    "data": [
                        {"nodeUUID": "u-1", "hostname": "node1.lan", "status": "online"},
                        {"nodeUUID": "u-2", "hostname": "node2.lan", "status": "online"},
                    ],
                },
            )
        if url.endswith("/api/cluster/resources"):
            return _FakeHTTPResponse(
                200,
                {
                    "status": "success",
                    "data": [
                        {
                            "nodeUUID": "u-2",
                            "hostname": "node2.lan",
                            "vms": [{"rid": 105, "name": "db-01", "state": 1}],
                            "jails": [{"ctId": 205, "name": "cache-01", "state": "RUNNING"}],
                        }
                    ],
                },
            )
        if url.endswith("/api/tasks/lifecycle/99"):
            return _FakeHTTPResponse(
                200,
                {"status": "success", "data": {"id": 99, "status": "completed"}},
            )
        return _FakeHTTPResponse(200, {"status": "success", "data": {"ok": True}})

    monkeypatch.setattr(
        "ansible_collections.sylve.cloud.plugins.module_utils.sylve.open_url",
        fake_open_url,
    )

    rid, host, _ = client.resolve_vm("db-01")
    assert (rid, host) == (105, "node2.lan")

    ctid, jhost, _ = client.resolve_jail("cache-01")
    assert (ctid, jhost) == (205, "node2.lan")

    uuid, nhost = client.resolve_node_uuid("u-2")
    assert (uuid, nhost) == ("u-2", "node2.lan")

    client.get("/vm/105", node="u-2")
    assert captured_headers[-1].get("X-Current-Hostname") == "node2.lan"

    task_res = wait_for_lifecycle_task(client, 99, timeout=5.0, poll_interval=0.01)
    assert task_res["status"] == "completed"

    with pytest.raises(ResourceNotFoundError):
        client.resolve_vm("nonexistent")
