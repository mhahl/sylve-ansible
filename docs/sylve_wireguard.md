# sylve_wireguard

_Manage Sylve WireGuard VPN server, server peers, and outbound clients_

Initialize, update, enable/disable, or delete the WireGuard server, server peers, and outbound WireGuard clients.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_wireguard`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `component` | `str` | no | `client` | `server`, `peer`, `client` | WireGuard component to manage. |
| `state` | `str` | no | `present` | `present`, `absent`, `enabled`, `disabled` | Desired state. |
| `id` | `int` | no | — | — | Peer ID or Client ID. |
| `name` | `str` | no | — | — | Peer or client name. |
| `endpoint` | `str` | no | — | — | Remote WireGuard endpoint (host:port) for C(component=client). |
| `allowed_ips` | `list` | no | — | — | List of allowed IP CIDRs. |
| `port` | `int` | no | — | — | Listen port for C(component=server). |
| `addresses` | `list` | no | — | — | Server tunnel addresses for C(component=server). |
| `enabled` | `bool` | no | — | — | Enabled flag. |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Initialize WireGuard server
  sylve.cloud.sylve_wireguard:
    component: server
    port: 51820
    addresses: ["10.99.0.1/24"]
    state: present

- name: Manage Sylve WireGuard VPN server, server peers, and outbound clients on a specific node using a named context
  sylve.cloud.sylve_wireguard:
    context: prod
    node: node1.lan
    component: server
    port: 51820
    state: present
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `wireguard` | `dict` | always | WireGuard resource representation. | `{"id": 1, "name": "peer-01", "enabled": true}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_wireguard.py` — edit the module, not this file._
