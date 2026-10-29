# sylve_system

_Manage Sylve system initialization, pools, services, tunables, PCI passthrough, and files_

Initialize Sylve, configure usable ZFS pools, control system services, set sysctl tunables, manage PCI passthrough (PPT) devices, run health checks, or manage remote files via file-explorer endpoints.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_system`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `action` | `str` | no | `info` | `info`, `initialize`, `set_pools`, `service`, `tunable_set`, `ppt_enable`, `ppt_import`, `ppt_prepare`, `ppt_disable`, `file_list`, `file_create`, `file_copy_move`, `file_delete`, `file_rename`, `file_upload`, `file_upload_revert`, `file_download`, `health` | System operation to perform. |
| `pools` | `list` | no | — | — | List of usable ZFS pool names for C(action=set_pools). |
| `service` | `str` | no | — | — | Service name for C(action=service). |
| `ppt_id` | `int` | no | — | — | PCI passthrough device ID for C(action=ppt_disable). |
| `path` | `str` | no | — | — | Remote file or directory path for file-explorer operations. |
| `src` | `path` | no | — | — | Local source file for C(action=file_upload). |
| `dest` | `path` | no | — | — | Local destination file for C(action=file_download). |
| `data` | `dict` | no | — | — | Request payload dictionary. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Configure usable ZFS pools
  sylve.cloud.sylve_system:
    action: set_pools
    pools: [zroot, tank]

- name: Manage Sylve system initialization, pools, services, tunables, PCI passthrough, and files on a specific node using a named context
  sylve.cloud.sylve_system:
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
| `system` | `raw` | always | System operation result. | `{"pools": ["zroot", "tank"]}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_system.py` — edit the module, not this file._
