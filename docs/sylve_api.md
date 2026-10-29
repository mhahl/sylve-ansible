# sylve_api

_Execute any Sylve Swagger HTTP API request directly_

Universal module for invoking any Sylve REST API endpoint (GET, POST, PUT, PATCH, DELETE), including file uploads, binary downloads, and unauthenticated endpoints.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_api`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `method` | `str` | no | `GET` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | HTTP method. |
| `path` | `str` | yes | — | — | API path without the C(/api) prefix (e.g. C(/cluster/nodes), C(/auth/preferences)). |
| `params` | `dict` | no | — | — | Query parameters dictionary. |
| `body` (aliases: `data`) | `raw` | no | — | — | JSON request body. |
| `upload_file` | `path` | no | — | — | Local file path to upload via multipart form-data. |
| `output_file` | `path` | no | — | — | Local destination path to stream a binary download to. |
| `require_auth` | `bool` | no | `true` | — | Whether to attach the Bearer token header. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Query user preferences via sylve_api
  sylve.cloud.sylve_api:
    method: GET
    path: /auth/preferences
  register: prefs

- name: Execute any Sylve Swagger HTTP API request directly on a specific node using a named context
  sylve.cloud.sylve_api:
    context: prod
    node: node1.lan
    method: GET
    path: /cluster/nodes
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `data` | `raw` | always | Unwrapped response data from the Sylve API. | `{"nodes": [{"hostname": "node1.lan", "status": "online"}]}` |
| `task` | `dict` | when a task is executed and C(wait=true) | Completed lifecycle, migration, replication, or backup task details. | `{"id": 42, "status": "completed"}` |

## See also

- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_api.py` — edit the module, not this file._
