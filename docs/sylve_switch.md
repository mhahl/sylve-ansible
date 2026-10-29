# sylve_switch

_Manage Sylve standard and manual network switches_

Create, update, delete, or synchronize standard and manual FreeBSD bridge network switches on Sylve.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_switch`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `synced` | Desired switch state or action. |
| `switch_id` (aliases: `id`) | `int` | no | — | — | Numeric switch ID. |
| `name` | `str` | no | — | — | Switch name. |
| `type` | `str` | no | `standard` | `standard`, `manual` | Switch type (C(standard) or C(manual)). |
| `bridge` | `str` | no | — | — | Existing host bridge interface name when C(type=manual) (e.g. C(bridge0)). |
| `bridge_mac` | `dict` | no | — | — | Bridge MAC source (sent as C(bridgeMac)). Required by the API when creating a standard switch. |
| `bridge_mac.mode` | `str` | no | — | — | MAC source mode (e.g. C(port), as used by switches created in the web UI). |
| `bridge_mac.port` | `str` | no | — | — | Member port name to derive the bridge MAC from (when C(mode=port)). |
| `bridge_mac.mac_object_id` | `int` | no | — | — | MAC network object ID (for object-backed modes). |
| `ports` | `list` | no | — | — | List of member interface names when C(type=standard). |
| `private` | `bool` | no | `false` | — | Host-only private switch flag. |
| `dhcp` | `bool` | no | `false` | — | Enable DHCP client on the switch bridge. |
| `mtu` | `int` | no | `1500` | — | Switch MTU. |
| `vlan` | `int` | no | `0` | — | VLAN tag. |
| `vlan_filtering` | `bool` | no | `false` | — | Enable FreeBSD bridge VLAN filtering. |
| `default_access_vlan` | `int` | no | `0` | — | Default access VLAN when VLAN filtering is enabled. |
| `address` | `str` | no | — | — | Optional IPv4 CIDR address or network object. |
| `data` | `dict` | no | — | — | Additional raw fields merged into the request body. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a standard switch on em0
  sylve.cloud.sylve_switch:
    name: lan0
    type: standard
    ports: [em0]
    mtu: 1500
    state: present

- name: Manage Sylve standard and manual network switches on a specific node using a named context
  sylve.cloud.sylve_switch:
    context: prod
    node: node1.lan
    name: lan0
    type: standard
    ports: [em0]
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
| `switch` | `dict` | always | Switch details. | `{"id": 1, "name": "lan0", "type": "standard"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_switch.py` — edit the module, not this file._
