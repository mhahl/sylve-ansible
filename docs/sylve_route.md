# sylve_route

_Manage Sylve static network routes_

Create, update, or delete static network routes on a Sylve node.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_route`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent` | Desired static route state. |
| `route_id` (aliases: `id`) | `int` | no | — | — | Numeric static route ID. |
| `name` | `str` | no | — | — | Route name. |
| `family` | `str` | no | — | — | Address family (C(inet) or C(inet6)). |
| `destination_type` | `str` | no | — | — | Destination type (e.g. C(network), C(host)). |
| `destination` | `str` | no | — | — | Destination CIDR or object. |
| `gateway` | `str` | no | — | — | Next-hop gateway IP or object. |
| `interface` | `str` | no | — | — | Outgoing network interface. |
| `enabled` | `bool` | no | `true` | — | Enable the static route. |
| `data` | `dict` | no | — | — | Additional raw fields merged into the request payload. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Add a static route to 10.20.0.0/16
  sylve.cloud.sylve_route:
    name: corp-vpn
    family: inet
    destination_type: network
    destination: 10.20.0.0/16
    gateway: 192.168.1.254
    enabled: true
    state: present

- name: Manage Sylve static network routes on a specific node using a named context
  sylve.cloud.sylve_route:
    context: prod
    node: node1.lan
    name: corp-vpn
    destination: 10.20.0.0/16
    gateway: 192.168.1.254
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
| `route` | `dict` | always | Static route details. | `{"id": 1, "name": "corp-vpn", "destinationRaw": "10.20.0.0/16"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_route.py` — edit the module, not this file._
