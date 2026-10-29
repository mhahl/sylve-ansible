# sylve_group

_Manage Sylve authentication groups and group membership_

List, create, or delete authentication groups, and replace group membership.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_group`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `query` | Desired group state. |
| `group_id` (aliases: `id`) | `int` | no | — | — | Numeric group ID. |
| `name` | `str` | no | — | — | Group name. |
| `members` | `list` | no | — | — | List of user IDs or usernames belonging to the group. |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create an operators group and set members
  sylve.cloud.sylve_group:
    name: operators
    members: [1, 2]
    state: present

- name: Manage Sylve authentication groups and group membership on a specific node using a named context
  sylve.cloud.sylve_group:
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
| `group` | `raw` | always | Group details. | `{"id": 2, "name": "operators"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_group.py` — edit the module, not this file._
