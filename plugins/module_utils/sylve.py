# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

import base64
import json
import os
import re
import stat
import tempfile
import time
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.urls import open_url

TERMINAL_TASK_STATUSES = {
    "success",
    "completed",
    "failed",
    "error",
    "cancelled",
    "canceled",
    "aborted",
    "interrupted",
}
FAILURE_TASK_STATUSES = {"failed", "error", "cancelled", "canceled", "aborted", "interrupted"}

_SIZE_RE = re.compile(r"^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]*)\s*$")
_SIZE_UNITS = {
    "": 1,
    "b": 1,
    "byte": 1,
    "bytes": 1,
    "k": 1024,
    "kb": 1024,
    "kib": 1024,
    "m": 1024**2,
    "mb": 1024**2,
    "mib": 1024**2,
    "g": 1024**3,
    "gb": 1024**3,
    "gib": 1024**3,
    "t": 1024**4,
    "tb": 1024**4,
    "tib": 1024**4,
    "p": 1024**5,
    "pb": 1024**5,
    "pib": 1024**5,
}


class SylveError(Exception):
    """Base exception for Sylve Ansible errors."""


class SessionExpiredError(SylveError):
    """Raised when the stored JWT token is missing, expired, or rejected with 401."""


class SylveAPIError(SylveError):
    """Raised when the Sylve API returns an error status or non-2xx HTTP code."""

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        error_code: str = "",
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.data = data


class ResourceNotFoundError(SylveError):
    """Raised when a VM, Jail, Node, or other resource cannot be found."""


def parse_size(value: Any, field_name: str = "size") -> int:
    """Parse a byte size integer or human-readable string like 2G or 512M."""
    if isinstance(value, bool):
        raise SylveError(f"Invalid {field_name}: {value!r}. Use a size like 2G or 512M.")
    if isinstance(value, (int, float)):
        size = int(value)
    else:
        text = str(value).strip()
        match = _SIZE_RE.match(text)
        if match is None:
            raise SylveError(f"Invalid {field_name}: '{value}'. Use a size like 2G or 512M.")
        number = float(match.group("value"))
        unit = match.group("unit").lower()
        if unit not in _SIZE_UNITS:
            raise SylveError(f"Invalid {field_name} unit '{unit}'. Use B, K, M, G, or T.")
        size = int(number * _SIZE_UNITS[unit])
    if size <= 0:
        raise SylveError(f"{field_name} must be greater than zero.")
    return size


def format_vm_state(state: Any) -> str:
    """Normalize libvirt/bhyve numeric or string VM state."""
    if isinstance(state, str) and not state.isdigit():
        return state.strip().upper()
    mapping = {
        0: "NOSTATE",
        1: "RUNNING",
        2: "BLOCKED",
        3: "PAUSED",
        4: "SHUTDOWN",
        5: "SHUTOFF",
        6: "CRASHED",
        7: "PMSUSPENDED",
    }
    try:
        return mapping.get(int(state), "UNKNOWN")
    except (TypeError, ValueError):
        return "UNKNOWN"


def get_default_config_path() -> Path:
    """Return default config path ($SYLVE_CONFIG, $XDG_CONFIG_HOME/sylve/config.yaml, or ~/.config/sylve/config.yaml)."""
    env_path = os.environ.get("SYLVE_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "sylve" / "config.yaml"


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode a JWT payload without verifying its signature."""
    if not token or "." not in token:
        return {}
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload_b64 = parts[1]
    padding = "=" * ((4 - len(payload_b64) % 4) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload_b64 + padding)
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}


def extract_token_expiry(token: str) -> str | None:
    """Extract the JWT exp claim as an ISO-8601 UTC timestamp."""
    payload = decode_jwt_payload(token)
    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and exp > 0:
        dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    return None


def parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware UTC datetime."""
    if not value:
        return None
    try:
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def normalize_server_url(server: str) -> str:
    """Normalize a Sylve server URL."""
    s = server.strip()
    if not s:
        raise ValueError("Server URL cannot be empty")
    if not s.startswith(("http://", "https://")):
        s = f"https://{s}"
    s = s.rstrip("/")
    if s.endswith("/api"):
        s = s[:-4]
    return s


@dataclass
class ContextConfig:
    """Represents a single Sylve server/cluster login context."""

    server: str
    username: str = ""
    auth_type: str = "sylve"
    node_id: str = ""
    hostname: str = ""
    token: str = ""
    expires_at: str | None = None
    verify_ssl: bool = True
    ca_cert: str | None = None
    default_node: str | None = None

    def get_expiry_datetime(self) -> datetime | None:
        dt = parse_iso_datetime(self.expires_at)
        if dt is not None:
            return dt
        if self.token:
            return parse_iso_datetime(extract_token_expiry(self.token))
        return None

    def is_token_expired(self, skew_seconds: int = 0) -> bool:
        if not self.token:
            return True
        exp = self.get_expiry_datetime()
        if exp is None:
            return False
        now = datetime.now(timezone.utc)
        return (exp.timestamp() - now.timestamp()) <= skew_seconds


@dataclass
class SylveConfig:
    """Top-level configuration holding named contexts and active context."""

    current_context: str = ""
    contexts: dict[str, ContextConfig] = field(default_factory=dict)

    def get_active_context(
        self,
        context_override: str | None = None,
        server_override: str | None = None,
        token_override: str | None = None,
        node_override: str | None = None,
        verify_override: bool | None = None,
        ca_cert_override: str | None = None,
    ) -> tuple[str, ContextConfig]:
        ctx_name = context_override or os.environ.get("SYLVE_CONTEXT") or self.current_context
        env_server = server_override or os.environ.get("SYLVE_SERVER")
        env_token = token_override or os.environ.get("SYLVE_TOKEN")
        env_node = node_override or os.environ.get("SYLVE_NODE")
        env_insecure = os.environ.get("SYLVE_INSECURE", "").lower() in ("1", "true", "yes")

        if not ctx_name or ctx_name not in self.contexts:
            if env_server:
                verify_ssl = (
                    verify_override
                    if verify_override is not None
                    else (not env_insecure)
                )
                return (
                    ctx_name or "env",
                    ContextConfig(
                        server=normalize_server_url(env_server),
                        token=env_token or "",
                        expires_at=extract_token_expiry(env_token) if env_token else None,
                        verify_ssl=verify_ssl,
                        ca_cert=ca_cert_override,
                        default_node=env_node,
                    ),
                )
            if not self.contexts:
                raise SylveError(
                    "Not logged in to any Sylve server. Run 'sylve login <server-url>' or pass server/token."
                )
            if ctx_name and ctx_name not in self.contexts:
                raise SylveError(
                    f"Context '{ctx_name}' not found in configuration. "
                    f"Available contexts: {', '.join(sorted(self.contexts.keys()))}"
                )
            ctx_name = next(iter(self.contexts.keys()))

        ctx = self.contexts[ctx_name]
        if verify_override is not None:
            verify_ssl = verify_override
        elif env_insecure:
            verify_ssl = False
        else:
            verify_ssl = ctx.verify_ssl

        resolved = ContextConfig(
            server=normalize_server_url(env_server) if env_server else ctx.server,
            username=ctx.username,
            auth_type=ctx.auth_type,
            node_id=ctx.node_id,
            hostname=ctx.hostname,
            token=env_token if env_token else ctx.token,
            expires_at=extract_token_expiry(env_token) if env_token else ctx.expires_at,
            verify_ssl=verify_ssl,
            ca_cert=ca_cert_override or ctx.ca_cert,
            default_node=env_node if env_node else ctx.default_node,
        )
        return ctx_name, resolved


def load_config(path: Path | str | None = None) -> SylveConfig:
    """Load Sylve configuration from disk."""
    cfg_path = Path(path).expanduser() if path else get_default_config_path()
    if not cfg_path.exists():
        return SylveConfig()
    try:
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise SylveError(f"Failed to parse configuration file {cfg_path}: {exc}") from exc

    if not isinstance(raw, dict):
        return SylveConfig()

    current_context = str(raw.get("current_context") or "")
    raw_contexts = raw.get("contexts") or {}
    contexts: dict[str, ContextConfig] = {}

    if isinstance(raw_contexts, dict):
        for name, cdata in raw_contexts.items():
            if not isinstance(cdata, dict) or not cdata.get("server"):
                continue
            contexts[str(name)] = ContextConfig(
                server=normalize_server_url(str(cdata.get("server", ""))),
                username=str(cdata.get("username") or ""),
                auth_type=str(cdata.get("auth_type") or "sylve"),
                node_id=str(cdata.get("node_id") or ""),
                hostname=str(cdata.get("hostname") or ""),
                token=str(cdata.get("token") or ""),
                expires_at=cdata.get("expires_at"),
                verify_ssl=bool(cdata.get("verify_ssl", True)),
                ca_cert=cdata.get("ca_cert"),
                default_node=cdata.get("default_node"),
            )

    return SylveConfig(current_context=current_context, contexts=contexts)


def save_config(config: SylveConfig, path: Path | str | None = None) -> Path:
    """Atomically persist configuration with mode 0600."""
    cfg_path = Path(path).expanduser() if path else get_default_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(cfg_path.parent, stat.S_IRWXU)
    except OSError:
        pass

    payload = {
        "current_context": config.current_context,
        "contexts": {name: asdict(ctx) for name, ctx in config.contexts.items()},
    }
    serialized = yaml.safe_dump(payload, sort_keys=False)

    fd, tmp_name = tempfile.mkstemp(dir=str(cfg_path.parent), prefix=".sylve-cfg-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(serialized)
        os.chmod(tmp_name, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_name, cfg_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    return cfg_path


def _encode_multipart_file(field_name: str, file_path: Path) -> tuple[bytes, str]:
    boundary = f"----SylveAnsibleBoundary{int(time.time() * 1000)}"
    content = file_path.read_bytes()
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return header + content + footer, f"multipart/form-data; boundary={boundary}"


class SylveClient:
    """HTTP client for the Sylve API using Ansible open_url with multi-node cluster support."""

    def __init__(
        self,
        context: ContextConfig,
        node_override: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.context = context
        self.node_override = node_override
        self.timeout = timeout
        self._base_url = f"{normalize_server_url(context.server)}/api"
        self._nodes_cache: list[dict[str, Any]] | None = None
        self._resources_cache: list[dict[str, Any]] | None = None

    def close(self) -> None:
        pass

    def __enter__(self) -> SylveClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _ensure_valid_token(self) -> None:
        if not self.context.token:
            raise SessionExpiredError(
                "No authentication token found. Log in with 'sylve login' or provide token/username+password."
            )
        if self.context.is_token_expired():
            exp_dt = self.context.get_expiry_datetime()
            exp_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S UTC") if exp_dt else "unknown time"
            raise SessionExpiredError(
                f"Authentication token expired at {exp_str}. Re-authenticate with 'sylve login'."
            )

    def _build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        rel = path if path.startswith("/") else f"/{path}"
        url = f"{self._base_url}{rel}"
        if params:
            clean = {
                k: (str(v).lower() if isinstance(v, bool) else v)
                for k, v in params.items()
                if v is not None
            }
            if clean:
                url = f"{url}?{urllib.parse.urlencode(clean, doseq=True)}"
        return url

    def _open(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        data: bytes | None = None,
    ) -> tuple[int, bytes]:
        ca_path = (
            str(Path(self.context.ca_cert).expanduser())
            if self.context.verify_ssl and self.context.ca_cert
            else None
        )
        try:
            resp = open_url(
                url,
                method=method.upper(),
                headers=headers,
                data=data,
                validate_certs=self.context.verify_ssl,
                ca_path=ca_path,
                timeout=self.timeout,
                follow_redirects="all",
            )
            status = getattr(resp, "status", None) or getattr(resp, "code", 200)
            return int(status), resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            return int(exc.code), body
        except urllib.error.URLError as exc:
            raise SylveError(f"Connection error talking to {self.context.server}: {exc}") from exc
        except Exception as exc:
            raise SylveError(f"Error talking to {self.context.server}: {exc}") from exc

    def resolve_node_hostname(self, node_identifier: str | None = None) -> str | None:
        target = node_identifier or self.node_override or self.context.default_node
        if not target:
            return None
        target = target.strip()
        if not target or target.lower() == "all":
            return None
        try:
            nodes = self.get_cluster_nodes()
        except SylveError:
            return target
        for n in nodes:
            hostname = str(n.get("hostname") or "")
            uuid = str(n.get("nodeUUID") or n.get("nodeUuid") or n.get("id") or "")
            if target.lower() in (hostname.lower(), uuid.lower()):
                return hostname or target
        return target

    def resolve_node_uuid(self, node_identifier: str) -> tuple[str, str]:
        target = node_identifier.strip()
        nodes = self.get_cluster_nodes()
        for n in nodes:
            hostname = str(n.get("hostname") or "")
            uuid = str(n.get("nodeUUID") or n.get("nodeUuid") or "")
            if target.lower() in (hostname.lower(), uuid.lower()):
                return uuid, hostname
        raise ResourceNotFoundError(
            f"Cluster node '{node_identifier}' not found. "
            f"Available nodes: {', '.join(str(n.get('hostname')) for n in nodes)}"
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        upload_file: Path | str | None = None,
        upload_field: str = "filepond",
        headers: dict[str, str] | None = None,
        node: str | None = None,
        require_auth: bool = True,
        unwrap_data: bool = True,
        resolve_node: bool = True,
    ) -> Any:
        req_headers: dict[str, str] = {"Accept": "application/json"}
        if require_auth:
            self._ensure_valid_token()
            req_headers["Authorization"] = f"Bearer {self.context.token}"

        resolved_host = self.resolve_node_hostname(node) if require_auth and resolve_node else None
        if resolved_host:
            req_headers["X-Current-Hostname"] = resolved_host

        body_bytes: bytes | None = None
        if upload_file is not None:
            body_bytes, content_type = _encode_multipart_file(upload_field, Path(upload_file))
            req_headers["Content-Type"] = content_type
        elif json_body is not None:
            body_bytes = json.dumps(json_body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        if headers:
            req_headers.update(headers)

        url = self._build_url(path, params)
        status_code, raw_bytes = self._open(method, url, req_headers, body_bytes)

        if status_code == 401 and require_auth:
            raise SessionExpiredError(
                "Server rejected authentication token (HTTP 401 Unauthorized). "
                "Please re-authenticate with 'sylve login'."
            )

        payload: Any = None
        if raw_bytes:
            text = raw_bytes.decode("utf-8", errors="replace")
            try:
                payload = json.loads(text)
            except ValueError:
                payload = text

        if status_code >= 400:
            err_msg = f"HTTP {status_code}"
            err_code = ""
            err_data = None
            if isinstance(payload, dict):
                err_code = str(payload.get("error") or payload.get("message") or "")
                err_msg = str(payload.get("message") or payload.get("error") or err_msg)
                err_data = payload.get("data")
                if err_code and err_code != err_msg:
                    err_msg = f"{err_msg} ({err_code})"
            elif isinstance(payload, str) and payload.strip():
                err_msg = payload.strip()
            raise SylveAPIError(
                message=err_msg,
                status_code=status_code,
                error_code=err_code,
                data=err_data,
            )

        if isinstance(payload, dict) and payload.get("status") == "error":
            err_code = str(payload.get("error") or "")
            err_msg = str(payload.get("message") or err_code or "API Error")
            raise SylveAPIError(
                message=err_msg,
                status_code=status_code,
                error_code=err_code,
                data=payload.get("data"),
            )

        if unwrap_data and isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        node: str | None = None,
        unwrap_data: bool = True,
    ) -> Any:
        return self.request("GET", path, params=params, node=node, unwrap_data=unwrap_data)

    def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        upload_file: Path | str | None = None,
        node: str | None = None,
        unwrap_data: bool = True,
    ) -> Any:
        return self.request(
            "POST",
            path,
            params=params,
            json_body=json_body,
            upload_file=upload_file,
            node=node,
            unwrap_data=unwrap_data,
        )

    def put(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        node: str | None = None,
        unwrap_data: bool = True,
    ) -> Any:
        return self.request(
            "PUT",
            path,
            params=params,
            json_body=json_body,
            node=node,
            unwrap_data=unwrap_data,
        )

    def patch(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        node: str | None = None,
        unwrap_data: bool = True,
    ) -> Any:
        return self.request(
            "PATCH",
            path,
            params=params,
            json_body=json_body,
            node=node,
            unwrap_data=unwrap_data,
        )

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        node: str | None = None,
        unwrap_data: bool = True,
    ) -> Any:
        return self.request(
            "DELETE",
            path,
            params=params,
            json_body=json_body,
            node=node,
            unwrap_data=unwrap_data,
        )

    def download_file(
        self,
        path: str,
        destination: Path | str,
        *,
        params: dict[str, Any] | None = None,
        node: str | None = None,
    ) -> Path:
        self._ensure_valid_token()
        headers = {"Accept": "*/*", "Authorization": f"Bearer {self.context.token}"}
        resolved_host = self.resolve_node_hostname(node)
        if resolved_host:
            headers["X-Current-Hostname"] = resolved_host
        url = self._build_url(path, params)
        status_code, raw_bytes = self._open("GET", url, headers)
        if status_code >= 400:
            raise SylveError(f"HTTP {status_code} downloading {path}.")
        target = Path(destination).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw_bytes)
        return target

    def login(
        self,
        username: str,
        password: str,
        auth_type: str = "sylve",
        remember: bool = True,
    ) -> ContextConfig:
        data = self.request(
            "POST",
            "/auth/login",
            json_body={
                "username": username,
                "password": password,
                "authType": auth_type,
                "remember": remember,
            },
            require_auth=False,
        )
        if not isinstance(data, dict) or not data.get("token"):
            raise SylveError("Login response did not contain a valid token.")
        token = str(data["token"])
        self.context.username = username
        self.context.auth_type = auth_type
        self.context.token = token
        self.context.hostname = str(data.get("hostname") or "")
        self.context.node_id = str(data.get("nodeId") or "")
        self.context.expires_at = extract_token_expiry(token)
        return self.context

    def get_cluster_nodes(self, refresh: bool = False) -> list[dict[str, Any]]:
        if self._nodes_cache is not None and not refresh:
            return self._nodes_cache

        nodes: list[dict[str, Any]] = []
        try:
            raw = self.request("GET", "/cluster/nodes", node=None, resolve_node=False)
            if isinstance(raw, list):
                nodes = [n for n in raw if isinstance(n, dict)]
        except SylveError:
            nodes = []

        if not nodes:
            try:
                info = self.request("GET", "/info/node", node=None, resolve_node=False)
                if isinstance(info, dict):
                    nodes = [
                        {
                            "nodeUUID": self.context.node_id or "local",
                            "hostname": info.get("hostname")
                            or self.context.hostname
                            or "localhost",
                            "status": "online",
                            "cpu": info.get("logicalCores") or 0,
                            "cpuUsage": info.get("cpuUsage") or 0.0,
                            "memory": info.get("ramTotal") or 0,
                            "memoryUsage": info.get("ramUsage") or 0.0,
                            "disk": info.get("diskTotal") or 0,
                            "diskUsage": info.get("diskUsage") or 0.0,
                            "guestIDs": info.get("guestIds") or [],
                            "sylveVersion": info.get("sylveVersion") or "",
                            "sylveCommit": info.get("sylveCommit") or "",
                        }
                    ]
            except SylveError:
                if self.context.hostname:
                    nodes = [
                        {
                            "nodeUUID": self.context.node_id or "local",
                            "hostname": self.context.hostname,
                            "status": "online",
                        }
                    ]

        self._nodes_cache = nodes
        return nodes

    def get_online_nodes(self, refresh: bool = False) -> list[dict[str, Any]]:
        nodes = self.get_cluster_nodes(refresh=refresh)
        online = [n for n in nodes if str(n.get("status") or "online").strip().lower() == "online"]
        return online or nodes

    def get_cluster_resources(self, refresh: bool = False) -> list[dict[str, Any]]:
        if self._resources_cache is not None and not refresh:
            return self._resources_cache

        resources: list[dict[str, Any]] = []
        try:
            raw = self.request("GET", "/cluster/resources", node=None)
            if isinstance(raw, list):
                resources = [r for r in raw if isinstance(r, dict)]
        except SylveError:
            resources = []

        if not resources:
            vms: list[Any] = []
            jails: list[Any] = []
            try:
                v_raw = self.get("/vm/simple")
                if isinstance(v_raw, list):
                    vms = v_raw
            except SylveError:
                pass
            try:
                j_raw = self.get("/jail/simple")
                if isinstance(j_raw, list):
                    jails = j_raw
            except SylveError:
                pass
            hostname = self.context.hostname or "localhost"
            nodes = self.get_cluster_nodes()
            if nodes and nodes[0].get("hostname"):
                hostname = str(nodes[0]["hostname"])
            resources = [
                {
                    "nodeUUID": self.context.node_id or "local",
                    "hostname": hostname,
                    "vms": vms,
                    "jails": jails,
                    "vmTemplates": [],
                    "jailTemplates": [],
                }
            ]

        self._resources_cache = resources
        return resources

    def fan_out_get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        node: str | None = None,
    ) -> list[tuple[str, Any]]:
        target = self.resolve_node_hostname(node)
        if target:
            data = self.get(path, params=params, node=target)
            return [(target, data)]

        online_nodes = self.get_online_nodes()
        if len(online_nodes) <= 1:
            host = (
                str(online_nodes[0].get("hostname"))
                if online_nodes and online_nodes[0].get("hostname")
                else (self.context.hostname or "local")
            )
            data = self.get(path, params=params, node=None)
            return [(host, data)]

        results: list[tuple[int, str, Any]] = []
        with ThreadPoolExecutor(max_workers=min(8, len(online_nodes))) as pool:
            futures = {
                pool.submit(self.get, path, params=params, node=str(n.get("hostname"))): (
                    idx,
                    str(n.get("hostname")),
                )
                for idx, n in enumerate(online_nodes)
                if n.get("hostname")
            }
            for fut in as_completed(futures):
                idx, host = futures[fut]
                try:
                    data = fut.result()
                    results.append((idx, host, data))
                except SylveError:
                    continue

        results.sort(key=lambda item: item[0])
        return [(host, data) for _, host, data in results]

    def resolve_vm(
        self,
        identifier: str | int,
        node: str | None = None,
    ) -> tuple[int, str, dict[str, Any]]:
        ident_str = str(identifier).strip()
        is_numeric = ident_str.isdigit()
        target_host = self.resolve_node_hostname(node)

        matches: list[tuple[int, str, dict[str, Any]]] = []
        for node_res in self.get_cluster_resources(refresh=True):
            host = str(node_res.get("hostname") or "")
            if target_host and host.lower() != target_host.lower():
                continue
            for vm in node_res.get("vms") or []:
                if not isinstance(vm, dict):
                    continue
                rid = vm.get("rid")
                name = str(vm.get("name") or "")
                if (
                    (is_numeric and str(rid) == ident_str) or (name.lower() == ident_str.lower())
                ) and rid is not None:
                    matches.append((int(rid), host, vm))

        if not matches and target_host:
            try:
                vms = self.get("/vm/simple", node=target_host)
                if isinstance(vms, list):
                    for vm in vms:
                        rid = vm.get("rid")
                        name = str(vm.get("name") or "")
                        if (
                            (is_numeric and str(rid) == ident_str)
                            or (name.lower() == ident_str.lower())
                        ) and rid is not None:
                            matches.append((int(rid), target_host, vm))
            except SylveError:
                pass

        if not matches:
            scope = f" on node '{target_host}'" if target_host else " in cluster"
            raise ResourceNotFoundError(f"VM '{identifier}' not found{scope}.")

        if len(matches) > 1:
            locs = ", ".join(f"{m[2].get('name')}(rid={m[0]}, node={m[1]})" for m in matches)
            raise SylveError(
                f"Multiple VMs match '{identifier}': {locs}. Specify the numeric RID or pass 'node'."
            )

        return matches[0]

    def resolve_jail(
        self,
        identifier: str | int,
        node: str | None = None,
    ) -> tuple[int, str, dict[str, Any]]:
        ident_str = str(identifier).strip()
        is_numeric = ident_str.isdigit()
        target_host = self.resolve_node_hostname(node)

        matches: list[tuple[int, str, dict[str, Any]]] = []
        for node_res in self.get_cluster_resources(refresh=True):
            host = str(node_res.get("hostname") or "")
            if target_host and host.lower() != target_host.lower():
                continue
            for jail in node_res.get("jails") or []:
                if not isinstance(jail, dict):
                    continue
                ctid = jail.get("ctId")
                name = str(jail.get("name") or "")
                if (
                    (is_numeric and str(ctid) == ident_str) or (name.lower() == ident_str.lower())
                ) and ctid is not None:
                    matches.append((int(ctid), host, jail))

        if not matches and target_host:
            try:
                jails = self.get("/jail/simple", node=target_host)
                if isinstance(jails, list):
                    for jail in jails:
                        ctid = jail.get("ctId")
                        name = str(jail.get("name") or "")
                        if (
                            (is_numeric and str(ctid) == ident_str)
                            or (name.lower() == ident_str.lower())
                        ) and ctid is not None:
                            matches.append((int(ctid), target_host, jail))
            except SylveError:
                pass

        if not matches:
            scope = f" on node '{target_host}'" if target_host else " in cluster"
            raise ResourceNotFoundError(f"Jail '{identifier}' not found{scope}.")

        if len(matches) > 1:
            locs = ", ".join(f"{m[2].get('name')}(ctid={m[0]}, node={m[1]})" for m in matches)
            raise SylveError(
                f"Multiple Jails match '{identifier}': {locs}. Specify the numeric CTID or pass 'node'."
            )

        return matches[0]


def wait_for_lifecycle_task(
    client: SylveClient,
    task_id: int,
    node: str | None = None,
    timeout: float = 600.0,
    poll_interval: float = 1.5,
) -> dict[str, Any]:
    """Poll a lifecycle task until it reaches a terminal status."""
    deadline = time.monotonic() + timeout
    last_task: dict[str, Any] = {"id": task_id, "status": "queued"}
    while time.monotonic() < deadline:
        data = client.get(f"/tasks/lifecycle/{task_id}", node=node)
        if isinstance(data, dict):
            last_task = data
            status = str(data.get("status") or "").strip().lower()
            if status in TERMINAL_TASK_STATUSES:
                if status in FAILURE_TASK_STATUSES:
                    err_detail = data.get("error") or data.get("message") or status
                    raise SylveError(f"Task #{task_id} {status}: {err_detail}")
                return data
        time.sleep(poll_interval)
    raise SylveError(
        f"Timed out waiting for lifecycle task #{task_id} after {int(timeout)}s "
        f"(last status: {last_task.get('status')})."
    )


def wait_for_replication_event(
    client: SylveClient,
    event_id: int,
    node_id: str | None = None,
    timeout: float = 1800.0,
    poll_interval: float = 2.0,
) -> dict[str, Any]:
    """Poll a replication event until it reaches a terminal status."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        params = {"nodeId": node_id} if node_id else None
        data = client.get(f"/cluster/replication/events/{event_id}/progress", params=params)
        if isinstance(data, dict):
            event_value = data.get("event")
            ev = event_value if isinstance(event_value, dict) else data
            status = str(ev.get("status") or "").strip().lower()
            if status in TERMINAL_TASK_STATUSES:
                if status in FAILURE_TASK_STATUSES:
                    err_detail = ev.get("error") or ev.get("message") or status
                    raise SylveError(f"Replication event #{event_id} {status}: {err_detail}")
                return ev
        time.sleep(poll_interval)
    raise SylveError(f"Timed out waiting for replication event #{event_id}.")


def wait_for_backup_event(
    client: SylveClient,
    event_id: int,
    node_id: str | None = None,
    timeout: float = 3600.0,
    poll_interval: float = 2.0,
) -> dict[str, Any]:
    """Poll a backup event until it reaches a terminal status."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        params = {"nodeId": node_id} if node_id else None
        data = client.get(f"/cluster/backups/events/{event_id}/progress", params=params)
        if isinstance(data, dict):
            event_value = data.get("event")
            ev = event_value if isinstance(event_value, dict) else data
            status = str(ev.get("status") or "").strip().lower()
            if status in TERMINAL_TASK_STATUSES:
                if status in FAILURE_TASK_STATUSES:
                    err_detail = ev.get("error") or status
                    raise SylveError(f"Backup event #{event_id} {status}: {err_detail}")
                return ev
        time.sleep(poll_interval)
    raise SylveError(f"Timed out waiting for backup event #{event_id}.")


def sylve_argument_spec(**kwargs: Any) -> dict[str, Any]:
    """Return common Sylve connection/authentication argument_spec merged with module kwargs."""
    spec: dict[str, Any] = {
        "config_path": {"type": "path"},
        "context": {"type": "str", "aliases": ["cloud"]},
        "auth": {
            "type": "dict",
            "options": {
                "server": {"type": "str"},
                "token": {"type": "str", "no_log": True},
                "username": {"type": "str"},
                "password": {"type": "str", "no_log": True},
                "auth_type": {"type": "str", "choices": ["sylve", "pam"], "default": "sylve"},
                "save_token": {"type": "bool", "default": False},
            },
        },
        "server": {"type": "str", "aliases": ["api_url", "endpoint"]},
        "token": {"type": "str", "no_log": True},
        "username": {"type": "str", "fallback": (env_fallback, ["SYLVE_USERNAME"])},
        "password": {
            "type": "str",
            "no_log": True,
            "fallback": (env_fallback, ["SYLVE_PASSWORD"]),
        },
        "auth_type": {
            "type": "str",
            "choices": ["sylve", "pam"],
            "default": "sylve",
            "fallback": (env_fallback, ["SYLVE_AUTH_TYPE"]),
        },
        "save_token": {"type": "bool", "default": False},
        "node": {"type": "str"},
        "validate_certs": {"type": "bool", "aliases": ["verify"]},
        "ca_cert": {"type": "path"},
        "timeout": {"type": "float", "default": 60.0},
        "wait": {"type": "bool", "default": True},
        "poll_interval": {"type": "float", "default": 1.5},
    }
    spec.update(kwargs)
    return spec


def create_client_from_params(params: dict[str, Any]) -> tuple[str, SylveClient]:
    """Create a connected SylveClient from Ansible module or inventory parameters."""
    auth = params.get("auth") or {}
    cfg_path = params.get("config_path")
    config = load_config(cfg_path)

    server = params.get("server") or auth.get("server")
    token = params.get("token") or auth.get("token")
    username = params.get("username") or auth.get("username")
    password = params.get("password") or auth.get("password")
    auth_type = params.get("auth_type") or auth.get("auth_type") or "sylve"
    save_token = bool(params.get("save_token") or auth.get("save_token"))
    node = params.get("node")
    validate_certs = params.get("validate_certs")
    ca_cert = params.get("ca_cert")
    timeout = float(params.get("timeout") or 60.0)

    ctx_name, ctx = config.get_active_context(
        context_override=params.get("context"),
        server_override=server,
        token_override=token,
        node_override=node,
        verify_override=validate_certs,
        ca_cert_override=ca_cert,
    )

    client = SylveClient(ctx, node_override=node, timeout=timeout)
    if ctx.is_token_expired() and username and password:
        client.login(username=username, password=password, auth_type=auth_type)
        if save_token:
            config.contexts[ctx_name] = client.context
            if not config.current_context:
                config.current_context = ctx_name
            save_config(config, cfg_path)

    return ctx_name, client


class SylveModule:
    """Base class for Sylve Ansible modules, modeled after OpenStackModule in openstack.cloud."""

    argument_spec: dict[str, Any] = {}
    module_kwargs: dict[str, Any] = {}
    requires_auth: bool = True

    def __init__(self) -> None:
        merged_kwargs: dict[str, Any] = {"supports_check_mode": True}
        merged_kwargs.update(self.module_kwargs)
        self.ansible = AnsibleModule(
            sylve_argument_spec(**self.argument_spec),
            **merged_kwargs,
        )
        self.params: dict[str, Any] = self.ansible.params
        self.check_mode: bool = self.ansible.check_mode
        self.node: str | None = self.params.get("node")
        self.wait: bool = bool(self.params.get("wait", True))
        self.timeout: float = float(self.params.get("timeout") or 60.0)
        self.poll_interval: float = float(self.params.get("poll_interval") or 1.5)
        self.context_name: str = ""
        self._client: SylveClient | None = None

    @property
    def client(self) -> SylveClient:
        if self._client is None:
            self.context_name, self._client = create_client_from_params(self.params)
        return self._client

    def exit_json(self, **kwargs: Any) -> None:
        self.ansible.exit_json(**kwargs)

    def fail_json(self, msg: str, **kwargs: Any) -> None:
        self.ansible.fail_json(msg=msg, **kwargs)

    def wait_task(self, resp: Any, node: str | None = None) -> dict[str, Any] | None:
        if not self.wait or not isinstance(resp, dict):
            return None
        task_id = resp.get("taskId")
        if task_id:
            return wait_for_lifecycle_task(
                self.client,
                int(task_id),
                node=node or self.node,
                timeout=self.timeout,
                poll_interval=self.poll_interval,
            )
        return None

    def subset_differs(self, desired: dict[str, Any], current: dict[str, Any]) -> bool:
        """Return True when any non-None desired key differs from current."""
        for k, v in desired.items():
            if v is None:
                continue
            if current.get(k) != v:
                return True
        return False

    def run(self) -> None:
        raise NotImplementedError("Subclasses must implement run()")

    def __call__(self) -> None:
        try:
            self.run()
        except SylveAPIError as exc:
            self.fail_json(
                msg=str(exc),
                status_code=exc.status_code,
                error_code=exc.error_code,
                error_data=exc.data,
            )
        except SylveError as exc:
            self.fail_json(msg=str(exc))
        finally:
            if self._client is not None:
                self._client.close()

