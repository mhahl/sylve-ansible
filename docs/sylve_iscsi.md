# sylve_iscsi

_Manage Sylve iSCSI global config, initiators, targets, LUNs, and portals_

Query or configure iSCSI global settings, initiators (and connect), targets, target LUNs, target portals, status, and target sessions.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_iscsi`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `resource` | `str` | no | `target` | `config`, `initiator`, `target`, `lun`, `portal`, `status`, `sessions` | iSCSI sub-resource to manage. |
| `state` | `str` | no | `present` | `present`, `absent`, `connected`, `query` | Desired state or action. |
| `id` | `int` | no | — | — | Initiator ID, Target ID, LUN ID, or Portal ID. |
| `target_id` | `int` | no | — | — | Parent Target ID when managing C(lun) or C(portal). |
| `name` | `str` | no | — | — | Resource name or IQN. |
| `data` | `dict` | no | — | — | Request body fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create an iSCSI target
  sylve.cloud.sylve_iscsi:
    resource: target
    name: iqn.2026-01.lan.sylve:storage01
    state: present

- name: Manage Sylve iSCSI global config, initiators, targets, LUNs, and portals on a specific node using a named context
  sylve.cloud.sylve_iscsi:
    context: prod
    node: node1.lan
    resource: status
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
| `iscsi` | `raw` | always | iSCSI resource details. | `{"id": 1, "name": "iqn.2026-01.lan.sylve:storage01"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_iscsi.py` — edit the module, not this file._
