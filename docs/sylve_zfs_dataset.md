# sylve_zfs_dataset

_Manage Sylve ZFS filesystems and volumes_

Create, edit, flash, delete, or bulk-delete ZFS filesystems and volumes (zvols).

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_zfs_dataset`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `flashed` | Desired dataset state or action. |
| `type` | `str` | no | `filesystem` | `filesystem`, `volume` | Dataset type. |
| `parent` | `str` | no | — | — | Parent dataset path when creating (e.g. C(zroot)). |
| `name` | `str` | no | — | — | Dataset leaf name (or full path for lookup). |
| `guid` | `str` | no | — | — | Dataset GUID. |
| `guids` | `list` | no | — | — | List of dataset GUIDs for bulk deletion (C(DELETE /zfs/datasets)). |
| `size` | `str` | no | — | — | Volume size (e.g. C(10G)) when C(type=volume). |
| `properties` | `dict` | no | — | — | ZFS dataset properties dictionary. |
| `image_uuid` | `str` | no | — | — | Image UUID when C(state=flashed) on a volume. |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a ZFS filesystem zroot/appdata
  sylve.cloud.sylve_zfs_dataset:
    type: filesystem
    parent: zroot
    name: appdata
    state: present

- name: Manage Sylve ZFS filesystems and volumes on a specific node using a named context
  sylve.cloud.sylve_zfs_dataset:
    context: prod
    node: node1.lan
    type: filesystem
    parent: zroot
    name: appdata
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
| `dataset` | `dict` | always | ZFS dataset details. | `{"name": "zroot/appdata", "type": "FILESYSTEM"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_zfs_dataset.py` — edit the module, not this file._
