# sylve_backup_target

_Manage Sylve cluster backup targets, validation, datasets, and restores_

Create, update, validate, delete, or restore from cluster backup targets, and inspect target datasets/metadata/readiness.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_backup_target`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `validated`, `restored`, `query` | Desired backup target state or action. |
| `target_id` (aliases: `id`) | `int` | no | — | — | Backup target numeric ID. |
| `name` | `str` | no | — | — | Backup target name. |
| `ssh_host` | `str` | no | — | — | Remote SSH host (e.g. C(backup@host)). |
| `ssh_port` | `int` | no | — | — | Remote SSH port. |
| `backup_root` | `str` | no | — | — | Remote ZFS dataset root path. |
| `description` | `str` | no | — | — | Backup target description. |
| `enabled` | `bool` | no | `true` | — | Enable the backup target. |
| `dataset_params` | `dict` | no | — | — | Query parameters when inspecting datasets/snapshots/metadata in C(state=query). |
| `data` | `dict` | no | — | — | Additional raw request fields (or restore payload for C(state=restored)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a backup target
  sylve.cloud.sylve_backup_target:
    name: offsite-zfs
    ssh_host: root@backup.lan
    backup_root: tank/sylve-backups
    enabled: true
    state: present

- name: Manage Sylve cluster backup targets, validation, datasets, and restores on a specific node using a named context
  sylve.cloud.sylve_backup_target:
    context: prod
    node: node1.lan
    state: query
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `target` | `raw` | always | Backup target details or info dictionary. | `{"id": 1, "name": "offsite-zfs", "sshHost": "root@backup.lan"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_backup_target.py` — edit the module, not this file._
