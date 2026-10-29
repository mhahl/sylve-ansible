# sylve_zfs_pool

_Manage Sylve ZFS storage pools, devices, scrubs, and scrub schedules_

Create, edit, delete, scrub, detach/replace devices on ZFS pools, or manage ZFS pool scrub schedules.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_zfs_pool`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `scrubbed`, `device_detached`, `device_replaced`, `scrub_schedule_present`, `scrub_schedule_absent` | Desired ZFS pool state or action. |
| `name` | `str` | no | — | — | ZFS pool name. |
| `guid` | `str` | no | — | — | ZFS pool GUID. |
| `schedule_id` | `int` | no | — | — | Scrub schedule ID when managing scrub schedules. |
| `cron_expr` | `str` | no | — | — | Cron schedule expression for scrub schedules. |
| `properties` | `dict` | no | — | — | Pool properties dictionary. |
| `vdevs` | `list` | no | — | — | Pool vdev layout list when creating a pool. |
| `device` | `str` | no | — | — | Device identifier for C(device_detached) or old device for C(device_replaced). |
| `new_device` | `str` | no | — | — | Replacement device identifier for C(device_replaced). |
| `data` | `dict` | no | — | — | Additional raw request body fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Start a scrub on ZFS pool zroot
  sylve.cloud.sylve_zfs_pool:
    name: zroot
    state: scrubbed

- name: Manage Sylve ZFS storage pools, devices, scrubs, and scrub schedules on a specific node using a named context
  sylve.cloud.sylve_zfs_pool:
    context: prod
    node: node1.lan
    name: zroot
    state: scrubbed
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `pool` | `dict` | always | ZFS pool or scrub schedule details. | `{"name": "zroot", "state": "ONLINE"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_zfs_pool.py` — edit the module, not this file._
