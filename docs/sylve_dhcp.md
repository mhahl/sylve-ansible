# sylve_dhcp

_Manage Sylve DHCP service configuration, IP ranges, and leases_

Configure DHCP global settings, IPv4/IPv6 ranges, static leases, or delete dynamic leases.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_dhcp`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `resource` | `str` | no | `range` | `config`, `range`, `lease`, `dynamic_lease` | DHCP sub-resource to manage. |
| `state` | `str` | no | `present` | `present`, `absent` | Desired state. |
| `id` | `int` | no | — | — | Numeric ID of the DHCP range or static lease. |
| `start_ip` | `str` | no | — | — | Range start IP address when C(resource=range). |
| `end_ip` | `str` | no | — | — | Range end IP address when C(resource=range). |
| `type` | `str` | no | — | — | Range type (e.g. C(ipv4), C(ipv6)) when C(resource=range). |
| `expiry` | `int` | no | — | — | Lease expiry in seconds. |
| `slaac` | `bool` | no | — | — | Enable SLAAC on IPv6 range. |
| `hostname` | `str` | no | — | — | Static lease hostname when C(resource=lease). |
| `ip` | `str` | no | — | — | Static or dynamic lease IP address. |
| `mac` | `str` | no | — | — | Static or dynamic lease MAC address. |
| `data` | `dict` | no | — | — | Additional raw request fields (or full body for C(resource=config)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a DHCPv4 range
  sylve.cloud.sylve_dhcp:
    resource: range
    type: ipv4
    start_ip: 192.168.10.100
    end_ip: 192.168.10.200
    expiry: 3600
    state: present

- name: Manage Sylve DHCP service configuration, IP ranges, and leases on a specific node using a named context
  sylve.cloud.sylve_dhcp:
    context: prod
    node: node1.lan
    resource: range
    state: present
    type: ipv4
    start_ip: 192.168.10.100
    end_ip: 192.168.10.200
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `dhcp` | `raw` | always | DHCP resource details. | `{"id": 4, "startIp": "192.168.10.100", "endIp": "192.168.10.200"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_dhcp.py` — edit the module, not this file._
