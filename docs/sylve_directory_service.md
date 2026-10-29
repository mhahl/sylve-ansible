# sylve_directory_service

_Manage Sylve Active Directory and Kerberos directory services_

Configure Active Directory (check, enable/disable, join, leave, status), Kerberos realms (discover, CRUD), Kerberos keytabs (CRUD), Kerberos settings, and query directory principals.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_directory_service`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `service` | `str` | no | `active_directory` | `active_directory`, `kerberos_realm`, `kerberos_keytab`, `kerberos_settings`, `principals` | Directory service component to manage. |
| `action` | `str` | no | `present` | `info`, `present`, `absent`, `check`, `enabled`, `join`, `leave`, `discover` | Operation to perform. |
| `id` | `int` | no | — | — | Numeric Kerberos realm or keytab ID. |
| `name` | `str` | no | — | — | Realm or keytab name. |
| `enabled` | `bool` | no | — | — | Enable or disable Active Directory when C(action=enabled). |
| `data` | `dict` | no | — | — | Request body fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Query Active Directory status
  sylve.cloud.sylve_directory_service:
    service: active_directory
    action: info

- name: Manage Sylve Active Directory and Kerberos directory services on a specific node using a named context
  sylve.cloud.sylve_directory_service:
    context: prod
    node: node1.lan
    service: active_directory
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
| `directory_service` | `raw` | always | Directory service configuration or operation result. | `{"enabled": true}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_directory_service.py` — edit the module, not this file._
