# sylve_zfs_snapshot

_Manage Sylve ZFS dataset snapshots and periodic snapshot schedules_

Create, roll back to, or delete ZFS dataset snapshots, or manage periodic snapshot schedules.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_zfs_snapshot`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `rolled_back`, `periodic_present`, `periodic_absent` | Desired snapshot or periodic schedule state. |
| `dataset` | `str` | no | — | — | Target dataset name or GUID. |
| `name` | `str` | no | — | — | Snapshot name (after C(@)) or full snapshot name (C(dataset@snap)). |
| `guid` | `str` | no | — | — | Snapshot or dataset GUID. |
| `recursive` | `bool` | no | `false` | — | Create or delete snapshot recursively. |
| `destroy_more_recent` | `bool` | no | `false` | — | Destroy newer snapshots during rollback. |
| `periodic_id` | `int` | no | — | — | Periodic snapshot schedule ID. |
| `ids` | `list` | no | — | — | List of periodic schedule IDs for bulk deletion. |
| `prefix` | `str` | no | — | — | Snapshot prefix for periodic schedules. |
| `cron_expr` | `str` | no | — | — | Cron expression for periodic schedules. |
| `keep_last` | `int` | no | — | — | Number of snapshots to retain for periodic schedules. |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a ZFS snapshot of zroot/appdata
  sylve.cloud.sylve_zfs_snapshot:
    dataset: zroot/appdata
    name: daily-01
    recursive: true
    state: present

- name: Manage Sylve ZFS dataset snapshots and periodic snapshot schedules on a specific node using a named context
  sylve.cloud.sylve_zfs_snapshot:
    context: prod
    node: node1.lan
    dataset: zroot/appdata
    name: daily-01
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
| `snapshot` | `dict` | always | Snapshot or periodic schedule details. | `{"name": "zroot/appdata@daily-01"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_zfs_snapshot.py` — edit the module, not this file._
