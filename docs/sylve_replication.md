# sylve_replication

_Manage Sylve HA replication policies, manual runs, failovers, and replication events_

Create, update, delete, run, or fail over cluster HA replication policies, and query replication events.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_replication`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `run`, `failover`, `events` | Desired replication policy state or action. |
| `policy_id` (aliases: `id`) | `int` | no | — | — | Replication policy numeric ID. |
| `event_id` | `int` | no | — | — | Replication event ID when querying or waiting for an event. |
| `name` | `str` | no | — | — | Policy name. |
| `guest_type` | `str` | no | — | — | Guest type (C(vm) or C(jail)). |
| `guest_id` | `int` | no | — | — | VM RID or Jail CTID. |
| `targets` | `list` | no | — | — | List of target node dicts (e.g. C([{'nodeId': 'uuid', 'weight': 100}])). |
| `cron_expr` | `str` | no | `*/15 * * * *` | — | Cron schedule expression. |
| `failover_mode` | `str` | no | — | — | Policy failover mode (C(manual) or C(auto)) or failover action mode (C(safe) or C(force)). |
| `target_node` | `str` | no | — | — | Target node hostname or UUID when C(state=failover). |
| `move_pinned_source` | `bool` | no | `true` | — | Update pinned source node during failover. |
| `confirm_data_loss` | `bool` | no | `false` | — | Acknowledge potential data loss for forced failover. |
| `enabled` | `bool` | no | `true` | — | Enable the policy. |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create an HA replication policy for VM 101
  sylve.cloud.sylve_replication:
    name: web-01-ha
    guest_type: vm
    guest_id: 101
    targets:
      - nodeId: node2-uuid
        weight: 100
    state: present

- name: Manage Sylve HA replication policies, manual runs, failovers, and replication events on a specific node using a named context
  sylve.cloud.sylve_replication:
    context: prod
    node: node1.lan
    state: events
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `replication` | `raw` | always | Replication policy or event details. | `{"id": 2, "name": "web-01-ha", "lastStatus": "success"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_replication.py` — edit the module, not this file._
