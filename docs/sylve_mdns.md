# sylve_mdns

_Manage Sylve mDNS configuration and records_

Query or update mDNS settings and create, update, or delete mDNS service/host records.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_mdns`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `resource` | `str` | no | `record` | `record`, `config` | mDNS component to manage. |
| `state` | `str` | no | `present` | `present`, `absent`, `query` | Desired state. |
| `record_id` (aliases: `id`) | `int` | no | — | — | Numeric mDNS record ID. |
| `name` | `str` | no | — | — | mDNS record name. |
| `type` | `str` | no | — | — | mDNS record/service type. |
| `port` | `int` | no | — | — | Service port. |
| `enabled` | `bool` | no | — | — | Enable the mDNS record or service. |
| `data` | `dict` | no | — | — | Additional raw request fields (or full body for C(resource=config)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create an mDNS record
  sylve.cloud.sylve_mdns:
    resource: record
    name: web-ui
    type: _https._tcp
    port: 8443
    state: present

- name: Manage Sylve mDNS configuration and records on a specific node using a named context
  sylve.cloud.sylve_mdns:
    context: prod
    node: node1.lan
    resource: record
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
| `mdns` | `raw` | always | mDNS record or configuration details. | `{"id": 1, "name": "web-ui", "type": "_https._tcp"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_mdns.py` — edit the module, not this file._
