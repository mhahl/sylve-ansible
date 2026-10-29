# sylve_disk

_Manage Sylve host disks, GPT partition tables, partitions, and SMART self-tests_

Query disks, initialize or clear GPT partition tables, create/delete partitions, run/abort SMART self-tests, and manage SMART schedules.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_disk`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `action` | `str` | no | `info` | `info`, `gpt_init`, `gpt_clear`, `partition_create`, `partition_delete`, `smart_info`, `smart_start`, `smart_abort`, `smart_schedules`, `smart_schedule_present`, `smart_schedule_absent` | Disk or SMART operation to perform. |
| `device` | `str` | no | — | — | Disk device name (e.g. C(nda0), C(ada0)). |
| `partition` | `str` | no | — | — | Partition identifier (e.g. C(nda0p1)) for C(action=partition_delete). |
| `schedule_id` | `int` | no | — | — | SMART schedule ID. |
| `data` | `dict` | no | — | — | Request body for partition creation, SMART self-test, or SMART schedule. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Initialize GPT partition table on ada1
  sylve.cloud.sylve_disk:
    action: gpt_init
    device: ada1

- name: Manage Sylve host disks, GPT partition tables, partitions, and SMART self-tests on a specific node using a named context
  sylve.cloud.sylve_disk:
    context: prod
    node: node1.lan
    action: info
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `disk` | `raw` | always | Disk, partition, or SMART operation result. | `{"device": "ada1", "smartStatus": "PASSED"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_disk.py` — edit the module, not this file._
