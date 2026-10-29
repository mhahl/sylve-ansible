# sylve_certificate

_Manage Sylve TLS certificates, ACME renewals, activation, and archives_

List, create, update, delete, activate, cancel activation, renew, retry, check domains, or download archives for TLS certificates.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_certificate`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `activated`, `activate_cancelled`, `renewed`, `retried`, `domain_check`, `archive`, `query` | Desired certificate state or action. |
| `cert_id` (aliases: `id`) | `int` | no | — | — | Numeric certificate ID. |
| `name` | `str` | no | — | — | Certificate name. |
| `domain` | `str` | no | — | — | Domain name for C(state=domain_check). |
| `dest` | `path` | no | — | — | Local destination path when downloading a certificate archive (C(state=archive)). |
| `data` | `dict` | no | — | — | Certificate request payload. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Renew TLS certificate #1
  sylve.cloud.sylve_certificate:
    cert_id: 1
    state: renewed

- name: Manage Sylve TLS certificates, ACME renewals, activation, and archives on a specific node using a named context
  sylve.cloud.sylve_certificate:
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
| `certificate` | `raw` | always | Certificate details or operation result. | `{"id": 1, "name": "node1.lan", "status": "issued"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_certificate.py` — edit the module, not this file._
