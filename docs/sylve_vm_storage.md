# sylve_vm_storage

_Manage storage volumes attached to a Sylve Bhyve VM_

Attach, create from image, update, or detach storage volumes on a Bhyve VM.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_vm_storage`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `from_image`, `absent` | Desired storage state. |
| `vm` | `str` | yes | — | — | VM RID or name. |
| `storage_id` | `int` | no | — | — | Storage attachment ID (required for update or delete when name is not matched). |
| `name` | `str` | no | — | — | Storage volume name. |
| `type` | `str` | no | — | — | Storage backend type (C(zvol), C(raw), C(image), C(filesystem)). |
| `pool` | `str` | no | — | — | ZFS pool name. |
| `size` | `raw` | no | — | — | Disk size (bytes or human-readable like C(20G)). |
| `emulation` | `str` | no | — | — | Disk emulation type (C(virtio-blk), C(nvme), C(ahci-hd), C(ahci-cd)). |
| `image_uuid` | `str` | no | — | — | Download/image UUID when C(state=from_image) or C(type=image). |
| `boot_order` | `int` | no | — | — | Disk boot order. |
| `data` | `dict` | no | — | — | Additional raw request body fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Attach a 50G NVMe zvol to VM 101
  sylve.cloud.sylve_vm_storage:
    vm: 101
    name: data-disk
    pool: zroot
    type: zvol
    size: 50G
    emulation: nvme
    state: present

- name: Manage storage volumes attached to a Sylve Bhyve VM on a specific node using a named context
  sylve.cloud.sylve_vm_storage:
    context: prod
    node: node1.lan
    vm: web-01
    name: data-disk
    pool: zroot
    size: 50G
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
| `storage` | `dict` | always | Storage operation result. | `{"id": 2, "name": "data-disk", "size": 53687091200}` |
| `task` | `dict` | when a task is executed and C(wait=true) | Completed lifecycle, migration, replication, or backup task details. | `{"id": 42, "status": "completed"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_vm_storage.py` — edit the module, not this file._
