# sylve_firewall

_Manage Sylve PF firewall traffic rules, NAT rules, and advanced settings_

Create, update, reorder, delete, or bulk-delete PF firewall traffic and NAT rules, or update/preview advanced PF settings.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_firewall`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `rule_type` | `str` | no | `traffic` | `traffic`, `nat`, `advanced` | Firewall component to manage. |
| `state` | `str` | no | `present` | `present`, `absent`, `reordered`, `preview` | Desired state or operation. |
| `rule_id` (aliases: `id`) | `int` | no | — | — | Numeric rule ID. |
| `ids` | `list` | no | — | — | List of rule IDs for bulk deletion (C(state=absent)) or reordering (C(state=reordered)). |
| `name` | `str` | no | — | — | Rule name. |
| `priority` | `int` | no | — | — | Rule evaluation priority. |
| `action` | `str` | no | — | — | Traffic rule action (e.g. C(pass), C(block)). |
| `nat_type` | `str` | no | — | — | NAT rule type (e.g. C(nat), C(rdr), C(binat)) when C(rule_type=nat). |
| `direction` | `str` | no | — | — | Packet direction (C(in) or C(out)). |
| `protocol` | `str` | no | — | — | Protocol (e.g. C(tcp), C(udp), C(icmp), C(any)). |
| `interface` | `str` | no | — | — | Network interface. |
| `source` | `str` | no | — | — | Source address/object. |
| `destination` | `str` | no | — | — | Destination address/object. |
| `dst_ports` | `str` | no | — | — | Destination port(s). |
| `enabled` | `bool` | no | `true` | — | Enable the rule. |
| `data` | `dict` | no | — | — | Additional raw request fields (or full body for C(rule_type=advanced)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Allow inbound HTTPS traffic
  sylve.cloud.sylve_firewall:
    rule_type: traffic
    name: allow-https
    action: pass
    direction: in
    protocol: tcp
    destination: any
    dst_ports: "443"
    enabled: true
    state: present

- name: Manage Sylve PF firewall traffic rules, NAT rules, and advanced settings on a specific node using a named context
  sylve.cloud.sylve_firewall:
    context: prod
    node: node1.lan
    rule_type: traffic
    state: present
    name: allow-https
    action: pass
    direction: in
    protocol: tcp
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `firewall` | `raw` | always | Firewall rule or settings result. | `{"id": 7, "name": "allow-https", "action": "pass"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_firewall.py` — edit the module, not this file._
