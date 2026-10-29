# sylve_node

_Manage Sylve cluster node maintenance drain, reboot, and host notes_

Drain a cluster node for maintenance (failing over HA policies and migrating/stopping VMs and Jails), initiate a node reboot, or manage per-host notes.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_node`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `action` | `str` | no | `drain` | `drain`, `reboot`, `note_present`, `note_absent` | Node operation to perform. |
| `target_node` | `str` | no | — | — | Destination node hostname or UUID when C(action=drain). Auto-selects least-loaded node if omitted. |
| `stop_only` | `bool` | no | `false` | — | Gracefully stop all guests on the node instead of migrating them when C(action=drain). |
| `fallback_stop` | `bool` | no | `false` | — | Stop guests that fail migration preflight instead of failing the drain. |
| `running_only` | `bool` | no | `false` | — | Only drain currently running guests. |
| `note_id` | `int` | no | — | — | Host note ID. |
| `ids` | `list` | no | — | — | Host note IDs for bulk deletion (C(DELETE /info/notes)). |
| `title` | `str` | no | — | — | Host note title. |
| `content` | `str` | no | — | — | Host note content. |
| `timeout` | `float` | no | `1800.0` | — | HTTP request and task polling timeout in seconds. Raised for this module because drain operations chain failovers and migrations. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Drain node1.lan for maintenance
  sylve.cloud.sylve_node:
    node: node1.lan
    action: drain
    target_node: node2.lan
    fallback_stop: true

- name: Drain node for maintenance on a specific node using a named context
  sylve.cloud.sylve_node:
    context: prod
    node: node1.lan
    action: drain
    target_node: node2.lan
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `node_result` | `raw` | always | Operation result. | `{"node": "node1.lan"}` |
| `task` | `dict` | when a task is executed and C(wait=true) | Completed lifecycle, migration, replication, or backup task details. | `{"id": 42, "status": "completed"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_node.py` — edit the module, not this file._
