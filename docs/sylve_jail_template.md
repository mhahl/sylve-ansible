# sylve_jail_template

_Manage Sylve FreeBSD jail templates_

Capture a jail as a template, deploy jails from a template, or delete a jail template.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_jail_template`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `deployed`, `absent` | Desired template state or action. |
| `template_id` | `int` | no | — | — | Jail template numeric ID. |
| `name` | `str` | no | — | — | Template name (for capture or lookup) or deployed jail name. |
| `source_jail` | `str` | no | — | — | Source jail CTID or name when capturing a template (C(state=present)). |
| `deploy_options` | `dict` | no | — | — | Deployment payload when C(state=deployed). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Capture jail 201 as a template
  sylve.cloud.sylve_jail_template:
    name: web-jail-template
    source_jail: 201
    state: present

- name: Manage Sylve FreeBSD jail templates on a specific node using a named context
  sylve.cloud.sylve_jail_template:
    context: prod
    node: node1.lan
    name: web-jail-template
    source_jail: app-01
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
| `template` | `dict` | always | Jail template representation or deployment response. | `{"id": 3, "name": "web-jail-template"}` |
| `task` | `dict` | when a task is executed and C(wait=true) | Completed lifecycle, migration, replication, or backup task details. | `{"id": 42, "status": "completed"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_jail_template.py` — edit the module, not this file._
