# sylve_backup_job

_Manage Sylve scheduled backup jobs, runs, restores, snapshots, and events_

Create, update, delete, run, or restore from cluster backup jobs, and query backup job snapshots and events.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_backup_job`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `run`, `restored`, `snapshots`, `events` | Desired backup job state or action. |
| `job_id` (aliases: `id`) | `int` | no | — | — | Backup job numeric ID. |
| `event_id` | `int` | no | — | — | Backup event ID when querying or waiting for an event. |
| `remote_events` | `bool` | no | `false` | — | Query paginated remote backup events (C(/cluster/backups/events/remote)). |
| `name` | `str` | no | — | — | Backup job name. |
| `target_id` | `int` | no | — | — | Target backup storage ID. |
| `mode` | `str` | no | — | — | Backup mode (e.g. C(dataset), C(vm), C(jail)). |
| `guest_type` | `str` | no | — | — | Guest type (C(vm) or C(jail)). |
| `guest_id` | `int` | no | — | — | Guest RID or CTID. |
| `runner_node_id` | `str` | no | — | — | Runner node UUID. |
| `cron_expr` | `str` | no | — | — | Cron schedule expression. |
| `enabled` | `bool` | no | `true` | — | Enable the backup job. |
| `snapshot` | `str` | no | — | — | Snapshot name to restore when C(state=restored). |
| `encryption_key` | `str` | no | — | — | Decryption key when C(state=restored). |
| `data` | `dict` | no | — | — | Additional raw request fields. |
| `timeout` | `float` | no | `3600.0` | — | HTTP request and backup-event polling timeout in seconds. Raised for this module because backup runs can take hours. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a nightly backup job for VM 101
  sylve.cloud.sylve_backup_job:
    name: nightly-web-01
    target_id: 1
    mode: vm
    guest_type: vm
    guest_id: 101
    cron_expr: "0 2 * * *"
    state: present

- name: Manage Sylve scheduled backup jobs, runs, restores, snapshots, and events on a specific node using a named context
  sylve.cloud.sylve_backup_job:
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
| `backup_job` | `raw` | always | Backup job, snapshot list, or event details. | `{"id": 3, "name": "nightly-web-01", "lastStatus": "success"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_backup_job.py` — edit the module, not this file._
