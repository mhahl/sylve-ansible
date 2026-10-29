# sylve_ddns

_Manage Sylve Dynamic DNS entries_

List, create, update, synchronize, or delete Dynamic DNS entries on Sylve.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_ddns`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `synced`, `query` | Desired DDNS entry state or action. |
| `entry_id` (aliases: `id`) | `int` | no | — | — | Numeric DDNS entry ID. |
| `name` | `str` | no | — | — | DDNS entry name or hostname. |
| `provider` | `str` | no | — | — | DDNS provider name. |
| `domain` | `str` | no | — | — | Domain or record to update. |
| `enabled` | `bool` | no | `true` | — | Enable the DDNS entry. |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a Dynamic DNS entry
  sylve.cloud.sylve_ddns:
    name: home-wan
    provider: cloudflare
    domain: home.example.com
    state: present

- name: Manage Sylve Dynamic DNS entries on a specific node using a named context
  sylve.cloud.sylve_ddns:
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
| `ddns` | `raw` | always | Dynamic DNS entry details. | `{"id": 1, "name": "home-wan", "domain": "home.example.com"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_ddns.py` — edit the module, not this file._
