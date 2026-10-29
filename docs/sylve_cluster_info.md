# sylve_cluster_info

_Gather information about Sylve cluster status, nodes, telemetry, and audit logs_

Query cluster status, join key, nodes, cluster resources, cluster notes, node telemetry (CPU, RAM, swap, history), and audit logs.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_cluster_info`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `gather` | `list` | no | `['cluster', 'nodes', 'resources']` | — | Sections of cluster and node information to retrieve. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Gather cluster status, nodes, and node telemetry
  sylve.cloud.sylve_cluster_info:
    gather: [cluster, nodes, resources, node_telemetry, audit_records]
  register: cluster_info

- name: Gather information about Sylve cluster status, nodes, telemetry, and audit logs on a specific node using a named context
  sylve.cloud.sylve_cluster_info:
    context: prod
    node: node1.lan
    gather: [cluster, nodes, resources]
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `cluster_info` | `dict` | always | Dictionary of gathered cluster and node data. | `{"nodes": [{"hostname": "node1.lan", "status": "online"}]}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_cluster_info.py` — edit the module, not this file._
