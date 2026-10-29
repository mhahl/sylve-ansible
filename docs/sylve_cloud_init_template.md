# sylve_cloud_init_template

_Manage reusable Sylve cloud-init templates_

List, create, update, or delete reusable cloud-init templates on Sylve.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_cloud_init_template`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `query` | Desired template state. |
| `template_id` (aliases: `id`) | `int` | no | — | — | Numeric cloud-init template ID. |
| `name` | `str` | no | — | — | Cloud-init template name. |
| `user_data` | `str` | no | — | — | Cloud-init user-data YAML string (sent as C(user)). |
| `meta_data` | `str` | no | — | — | Cloud-init meta-data YAML string (sent as C(meta)). |
| `network_config` | `str` | no | — | — | Cloud-init network-config YAML string (sent as C(networkConfig)). |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a reusable cloud-init template
  sylve.cloud.sylve_cloud_init_template:
    name: base-ssh
    user_data: |
      #cloud-config
      users:
        - name: freebsd
          sudo: ALL=(ALL) NOPASSWD:ALL
    meta_data: |
      instance-id: base-ssh
    network_config: |
      version: 1
      config:
        - type: physical
          name: eth0
          subnets:
            - type: dhcp
    state: present

- name: Manage reusable Sylve cloud-init templates on a specific node using a named context
  sylve.cloud.sylve_cloud_init_template:
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
| `template` | `raw` | always | Cloud-init template details. | `{"id": 2, "name": "base-ssh"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_cloud_init_template.py` — edit the module, not this file._
