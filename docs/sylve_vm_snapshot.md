# sylve_vm_snapshot

_Manage ZFS snapshots for a Sylve Bhyve VM_

Create, roll back to, or delete crash-consistent ZFS snapshots for a Bhyve virtual machine.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_vm_snapshot`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `rolled_back` | Desired snapshot state. |
| `vm` | `str` | yes | — | — | VM RID or name. |
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
- name: Create a snapshot of VM web-01
  sylve.cloud.sylve_vm_snapshot:
    vm: web-01
    name: pre-upgrade
    description: Before patching
    state: present

- name: Manage ZFS snapshots for a Sylve Bhyve VM on a specific node using a named context
  sylve.cloud.sylve_vm_snapshot:
    context: prod
    node: node1.lan
    vm: web-01
    name: pre-upgrade
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
| `snapshot` | `dict` | always | VM snapshot details. | `{"id": 5, "name": "pre-upgrade"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_vm_snapshot.py` — edit the module, not this file._
