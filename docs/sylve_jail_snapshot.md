# sylve_jail_snapshot

_Manage ZFS snapshots for a Sylve FreeBSD jail_

Create, roll back to, or delete ZFS snapshots for a FreeBSD jail.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_jail_snapshot`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `rolled_back` | Desired snapshot state. |
| `jail` | `str` | yes | — | — | Jail CTID or name. |
| `snapshot_id` | `int` | no | — | — | Snapshot numeric ID. |
| `name` | `str` | no | — | — | Snapshot name. |
| `description` | `str` | no | `` | — | Snapshot description. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a snapshot of jail app-01
  sylve.cloud.sylve_jail_snapshot:
    jail: app-01
    name: pre-deploy
    state: present

- name: Manage ZFS snapshots for a Sylve FreeBSD jail on a specific node using a named context
  sylve.cloud.sylve_jail_snapshot:
    context: prod
    node: node1.lan
    jail: app-01
    name: pre-deploy
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
| `snapshot` | `dict` | always | Jail snapshot details. | `{"id": 5, "name": "pre-deploy"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_jail_snapshot.py` — edit the module, not this file._
