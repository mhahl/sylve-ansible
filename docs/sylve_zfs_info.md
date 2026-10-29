# sylve_zfs_info

_Gather information about Sylve ZFS pools, datasets, snapshots, scrubs, and dashboard metrics_

Query ZFS pools, pool status, scrub runs, scrub schedules, disk usage, datasets, paginated datasets, periodic snapshot schedules, and dashboard metrics.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_zfs_info`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `gather` | `list` | no | `['pools', 'datasets', 'periodic_snapshots']` | — | List of ZFS sections to query. |
| `all_pools` | `bool` | no | `false` | — | Include pools not marked usable in Sylve settings. |
| `pool_guid` | `str` | no | — | — | Pool GUID to fetch detailed status (C(/zfs/pools/{guid}/status)) and scrub runs (C(/zfs/pools/{guid}/scrub/runs)). |
| `dataset_type` | `str` | no | — | — | Filter datasets by type (C(FILESYSTEM), C(VOLUME), C(SNAPSHOT), C(ALL)). |
| `paginated_params` | `dict` | no | — | — | Query parameters for C(/zfs/datasets/paginated). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Gather ZFS pools and datasets
  sylve.cloud.sylve_zfs_info:
    gather: [pools, datasets, disks_usage, scrub_schedules]
  register: zfs_info

- name: Gather information about Sylve ZFS pools, datasets, snapshots, scrubs, and dashboard metrics on a specific node using a named context
  sylve.cloud.sylve_zfs_info:
    context: prod
    node: node1.lan
    gather: [pools, datasets]
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `zfs_info` | `dict` | always | Dictionary of gathered ZFS data. | `{"pools": [{"name": "zroot", "state": "ONLINE"}]}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_zfs_info.py` — edit the module, not this file._
