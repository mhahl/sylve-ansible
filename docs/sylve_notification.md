# sylve_notification

_Manage Sylve notification transports, alert rules, and active notifications_

List, create, update, bulk-update, test, or delete notification transports and rules, or count/dismiss active notifications.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_notification`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `resource` | `str` | no | `rule` | `transport`, `rule`, `notification` | Notification sub-resource to manage. |
| `state` | `str` | no | `present` | `present`, `absent`, `tested`, `dismissed`, `dismissed_all`, `bulk_updated`, `query` | Desired state or action. |
| `id` | `int` | no | — | — | Numeric transport, rule, or notification ID. |
| `ids` | `list` | no | — | — | List of rule IDs for bulk deletion or bulk update. |
| `name` | `str` | no | — | — | Transport or rule name. |
| `type` | `str` | no | — | — | Transport type (e.g. C(webhook), C(smtp), C(discord)). |
| `enabled` | `bool` | no | — | — | Enable the transport or rule. |
| `data` | `dict` | no | — | — | Request payload dictionary. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a webhook notification transport
  sylve.cloud.sylve_notification:
    resource: transport
    name: ops-webhook
    type: webhook
    enabled: true
    data:
      url: https://hooks.example.com/sylve
    state: present

- name: Manage Sylve notification transports, alert rules, and active notifications on a specific node using a named context
  sylve.cloud.sylve_notification:
    context: prod
    node: node1.lan
    resource: notification
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
| `notification` | `raw` | always | Notification transport, rule, or alert result. | `{"id": 1, "name": "ops-webhook"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_notification.py` — edit the module, not this file._
