# sylve_samba

_Manage Sylve Samba global configuration, shares, and audit logs_

Query or update Samba global configuration, create/update/enable/disable/delete Samba shares, or fetch Samba audit logs.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_samba`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `resource` | `str` | no | `share` | `share`, `config`, `audit_logs` | Samba component to manage. |
| `state` | `str` | no | `present` | `present`, `absent`, `enabled`, `disabled`, `query` | Desired share state. |
| `share_id` (aliases: `id`) | `int` | no | — | — | Numeric Samba share ID. |
| `name` | `str` | no | — | — | Samba share name. |
| `dataset` | `str` | no | — | — | ZFS dataset or path backing the share. |
| `enabled` | `bool` | no | — | — | Enable or disable the share. |
| `data` | `dict` | no | — | — | Additional raw request fields (or full body for C(resource=config)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a Samba share
  sylve.cloud.sylve_samba:
    resource: share
    name: media
    dataset: zroot/media
    enabled: true
    state: present

- name: Manage Sylve Samba global configuration, shares, and audit logs on a specific node using a named context
  sylve.cloud.sylve_samba:
    context: prod
    node: node1.lan
    resource: share
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
| `samba` | `raw` | always | Samba share, global config, or audit logs. | `{"id": 1, "name": "media", "enabled": true}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_samba.py` — edit the module, not this file._
