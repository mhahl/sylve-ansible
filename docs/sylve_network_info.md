# sylve_network_info

_Gather information about Sylve network interfaces, switches, routes, DHCP, firewall, and WireGuard_

Query network interfaces, L3 configurations, pending L3 changes, global network config, switches, switch sync status, static routes, network objects, DHCP config/ranges/leases, firewall rules/counters/rendered/live logs/route suggestions, and WireGuard.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_network_info`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `gather` | `list` | no | `['interfaces', 'switches', 'routes', 'objects']` | — | List of network sections to query. |
| `nat_rule_id` | `int` | no | — | — | Optional NAT rule ID to fetch route suggestions for (C(/network/firewall/nat/{id}/route-suggestions)). |
| `log_params` | `dict` | no | — | — | Optional query parameters for C(/network/firewall/logs/live). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Gather switches and interfaces across the cluster
  sylve.cloud.sylve_network_info:
    gather: [interfaces, switches, dhcp, firewall, wireguard]
  register: net_info

- name: Gather information about Sylve network interfaces, switches, routes, DHCP, firewall, and WireGuard on a specific node using a named context
  sylve.cloud.sylve_network_info:
    context: prod
    node: node1.lan
    gather: [interfaces, switches, routes, objects]
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `network_info` | `dict` | always | Dictionary of gathered network resources. | `{"switches": {"standard": [{"id": 1, "name": "lan0"}]}}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_network_info.py` — edit the module, not this file._
