# sylve_network_interface

_Manage Sylve host Layer-3 network interfaces, global network config, and pending IP changes_

Configure or remove host Layer-3 interface IP settings (C(/network/interface/{name}/l3)), reapply L3 settings, confirm or revert pending host IP transactions, or update global network settings (C(/network/global-config)).

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_network_interface`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `reapplied`, `pending_confirmed`, `pending_reverted`, `global_config` | Desired L3 interface or global network action. |
| `name` | `str` | no | — | — | Host network interface name (e.g. C(em0), C(vtnet0)). |
| `pending_id` | `str` | no | — | — | Pending host IP transaction ID for C(pending_confirmed) or C(pending_reverted). |
| `dhcp` | `bool` | no | — | — | Enable DHCPv4 on the interface. |
| `slaac` | `bool` | no | — | — | Enable IPv6 SLAAC on the interface. |
| `mtu` | `int` | no | — | — | Interface MTU. |
| `ipv4` | `list` | no | — | — | List of IPv4 address configurations. |
| `ipv6` | `list` | no | — | — | List of IPv6 address configurations. |
| `description` | `str` | no | — | — | Interface description. |
| `data` | `dict` | no | — | — | Raw request body for L3 configuration or C(global_config). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Configure static IPv4 on em1
  sylve.cloud.sylve_network_interface:
    name: em1
    dhcp: false
    mtu: 1500
    ipv4:
      - ip: 192.168.10.10
        netmask: 24
    state: present

- name: Manage Sylve host Layer-3 network interfaces, global network config, and pending IP changes on a specific node using a named context
  sylve.cloud.sylve_network_interface:
    context: prod
    node: node1.lan
    name: em1
    dhcp: false
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
| `interface` | `dict` | always | Interface L3 configuration or operation result. | `{"name": "em1", "dhcp": false}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_network_interface.py` — edit the module, not this file._
