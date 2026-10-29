# sylve_cluster

_Manage Sylve cluster formation, membership, resynchronization, and cluster notes_

Initialize a cluster, join an existing cluster, accept a pending join, leave/reset a node, remove a peer node, resynchronize Raft state, sync intra-cluster health, or manage cluster-wide notes.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_cluster`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `action` | `str` | no | `create` | `create`, `join`, `accept_join`, `leave`, `remove_node`, `resync`, `sync_health`, `note_present`, `note_absent` | Cluster operation to perform. |
| `ip` | `str` | no | — | — | Bootstrap Raft IP address for C(action=create). |
| `leader_ip` | `str` | no | — | — | Cluster leader IP for C(action=join). |
| `node_ip` | `str` | no | — | — | Joining node Raft IP for C(action=join). |
| `node_id` | `str` | no | — | — | Node UUID or hostname for C(join) or C(remove_node). |
| `cluster_key` | `str` | no | — | — | Cluster join key for C(action=join). |
| `retain_guests` | `bool` | no | `true` | — | Retain local VM and jail registrations when leaving or removing a node. |
| `force` | `bool` | no | `false` | — | Force local cluster reset or force-remove an externally fenced peer node. |
| `note_id` | `int` | no | — | — | Cluster note ID. |
| `ids` | `list` | no | — | — | List of cluster note IDs for bulk deletion. |
| `title` | `str` | no | — | — | Cluster note title. |
| `content` | `str` | no | — | — | Cluster note content. |
| `data` | `dict` | no | — | — | Additional raw request body fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Initialize a new Sylve cluster
  sylve.cloud.sylve_cluster:
    action: create
    ip: 10.0.0.10

- name: Manage Sylve cluster formation, membership, resynchronization, and cluster notes on a specific node using a named context
  sylve.cloud.sylve_cluster:
    context: prod
    node: node1.lan
    action: sync_health
    data: {}
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `cluster` | `raw` | always | Cluster or note operation result. | `{"enabled": true, "leaderId": "node-1"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_cluster.py` — edit the module, not this file._
