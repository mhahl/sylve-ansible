# sylve_task

_Query, wait for, validate, or cancel Sylve lifecycle and migration tasks_

Query active or recent lifecycle tasks, wait for a task by ID, validate guest migration preflight, or cancel an active migration task.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_task`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `action` | `str` | no | `recent` | `active`, `recent`, `show`, `wait`, `validate_migration`, `cancel_migration` | Task operation to perform. |
| `task_id` (aliases: `id`) | `int` | no | — | — | Lifecycle or migration task ID. |
| `guest_type` | `str` | no | — | — | Guest type (C(vm) or C(jail)). |
| `guest_id` | `int` | no | — | — | Guest RID or CTID. |
| `target_node` | `str` | no | — | — | Target node hostname or UUID for C(action=validate_migration). |
| `limit` | `int` | no | `25` | — | Maximum recent tasks to return. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Wait for lifecycle task 42 to complete
  sylve.cloud.sylve_task:
    action: wait
    task_id: 42

- name: Query, wait for, validate, or cancel Sylve lifecycle and migration tasks on a specific node using a named context
  sylve.cloud.sylve_task:
    context: prod
    node: node1.lan
    action: recent
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `task` | `raw` | always | Task details or task list. | `{"id": 42, "action": "start", "status": "completed"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_task.py` — edit the module, not this file._
