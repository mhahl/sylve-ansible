# sylve_jail_network

_Manage network attachments for a Sylve FreeBSD jail_

Attach, update, or detach networks on a FreeBSD jail, or configure network inheritance.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_jail_network`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `inheritance` | Desired network state. |
| `jail` | `str` | yes | — | — | Jail CTID or name. |
| `network_id` | `int` | no | — | — | Jail network attachment ID. |
| `name` | `str` | no | — | — | Network attachment name. |
| `switch_id` | `int` | no | — | — | Switch ID. |
| `switch_type` | `str` | no | — | — | Switch type (C(standard) or C(manual)). |
| `mac_id` | `int` | no | — | — | MAC object ID. |
| `ipv4_id` | `int` | no | — | — | IPv4 network object ID. |
| `ipv4_gw_id` | `int` | no | — | — | IPv4 gateway object ID. |
| `ipv6_id` | `int` | no | — | — | IPv6 network object ID. |
| `ipv6_gw_id` | `int` | no | — | — | IPv6 gateway object ID. |
| `dhcp` | `bool` | no | — | — | Enable DHCP on the jail interface. |
| `slaac` | `bool` | no | — | — | Enable IPv6 SLAAC on the jail interface. |
| `inherit_ipv4` | `bool` | no | — | — | Inherit host IPv4 when C(state=inheritance). |
| `inherit_ipv6` | `bool` | no | — | — | Inherit host IPv6 when C(state=inheritance). |
| `data` | `dict` | no | — | — | Additional raw request body fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Attach jail 201 to switch 1 with DHCP
  sylve.cloud.sylve_jail_network:
    jail: 201
    name: net0
    switch_id: 1
    dhcp: true
    state: present

- name: Manage network attachments for a Sylve FreeBSD jail on a specific node using a named context
  sylve.cloud.sylve_jail_network:
    context: prod
    node: node1.lan
    jail: app-01
    state: inheritance
    inherit_ipv4: true
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `network` | `dict` | always | Jail network attachment details. | `{"id": 1, "name": "net0", "switchId": 2}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_jail_network.py` — edit the module, not this file._
