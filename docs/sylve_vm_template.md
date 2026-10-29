# sylve_vm_template

_Manage Sylve Bhyve VM templates_

Capture a shut-off VM as a reusable template, deploy VMs from a template, or delete a VM template.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_vm_template`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `deployed`, `absent` | Desired template state or action. |
| `template_id` | `int` | no | — | — | VM template numeric ID. |
| `name` | `str` | no | — | — | Template name (for capture or lookup) or deployed VM name. |
| `source_vm` | `str` | no | — | — | Shut-off source VM RID or name when capturing a template (C(state=present)). |
| `deploy_options` | `dict` | no | — | — | Deployment payload when C(state=deployed) (e.g. C(mode), C(rid), C(name), C(startRid), C(count), C(namePrefix), C(storagePools)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Capture VM 101 as a template
  sylve.cloud.sylve_vm_template:
    name: freebsd-14-base
    source_vm: 101
    state: present

- name: Manage Sylve Bhyve VM templates on a specific node using a named context
  sylve.cloud.sylve_vm_template:
    context: prod
    node: node1.lan
    name: freebsd-14-base
    source_vm: web-01
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
| `template` | `dict` | always | VM template representation or deployment response. | `{"id": 3, "name": "freebsd-14-base"}` |
| `task` | `dict` | when a task is executed and C(wait=true) | Completed lifecycle, migration, replication, or backup task details. | `{"id": 42, "status": "completed"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_vm_template.py` — edit the module, not this file._
