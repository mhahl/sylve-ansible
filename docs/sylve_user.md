# sylve_user

_Manage Sylve local, PAM, and imported Unix users and user passkeys_

Create, import, update, or delete local, PAM, and Unix users, query user capabilities/importable users/next UID, and manage user passkeys.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_user`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `pam_present`, `imported`, `absent`, `passkey_absent`, `query` | Desired user state or action. |
| `user_id` (aliases: `id`) | `int` | no | — | — | Numeric user ID. |
| `name` | `str` | no | — | — | Username. |
| `user_password` | `str` | no | — | — | Password for the managed user account. |
| `email` | `str` | no | — | — | User email address. |
| `uid` | `int` | no | — | — | Unix UID. |
| `admin` | `bool` | no | — | — | Administrator privilege flag. |
| `credential_id` | `str` | no | — | — | Passkey credential ID when C(state=passkey_absent). |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a local Sylve user
  sylve.cloud.sylve_user:
    name: devops
    user_password: "{{ vault_user_password }}"
    admin: true
    state: present

- name: Manage Sylve local, PAM, and imported Unix users and user passkeys on a specific node using a named context
  sylve.cloud.sylve_user:
    context: prod
    node: node1.lan
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
| `user` | `raw` | always | User details or info dictionary. | `{"id": 3, "username": "devops"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_user.py` — edit the module, not this file._
