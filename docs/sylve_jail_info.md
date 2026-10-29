# sylve_jail_info

_Gather information about Sylve FreeBSD jails, bootstraps, templates, and stats_

Query FreeBSD jails, simple summaries, live guest-info, root mountpoints, ZFS sources, logs, stats, snapshots, bootstraps, and templates.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_jail_info`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `jail` | `str` | no | — | — | Optional jail CTID or name to query a single jail. |
| `simple` | `bool` | no | `false` | — | Use C(/jail/simple) instead of full C(/jail) details. |
| `include_state` | `bool` | no | `false` | — | Fetch C(/jail/{ctid}/state) when querying a single jail. |
| `include_guest_info` | `bool` | no | `false` | — | Fetch live OS/network info (C(/jail/{ctid}/guest-info)) when querying a single jail. |
| `include_root_mountpoint` | `bool` | no | `false` | — | Fetch root mountpoint (C(/jail/{ctid}/root-mountpoint)) when querying a single jail. |
| `include_logs` | `bool` | no | `false` | — | Fetch console logs (C(/jail/{ctid}/logs)) when querying a single jail. |
| `include_snapshots` | `bool` | no | `false` | — | Fetch snapshots (C(/jail/{ctid}/snapshots)) when querying a single jail. |
| `include_stats` | `bool` | no | `false` | — | Fetch jail stats (C(/jail/{ctid}/stats) or C(/jail/{ctid}/stats/{step})). |
| `stats_step` | `str` | no | — | — | Step parameter for C(/jail/{ctid}/stats/{step}). |
| `include_zfs_sources` | `bool` | no | `false` | — | Include available jail ZFS sources (C(/jail/zfs-sources)). |
| `bootstrap_pool` | `str` | no | — | — | ZFS pool name to list pkgbase jail bootstraps from (C(/jail/bootstraps)). |
| `include_templates` | `bool` | no | `false` | — | Include jail templates (C(/jail/templates)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: List all jails across the cluster
  sylve.cloud.sylve_jail_info:
  register: jail_info

- name: Gather information about Sylve FreeBSD jails, bootstraps, templates, and stats on a specific node using a named context
  sylve.cloud.sylve_jail_info:
    context: prod
    node: node1.lan
    bootstrap_pool: zroot
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `jails` | `list` | always | List of matching jails. | `[{"ctId": 201, "name": "app-01", "state": "RUNNING"}]` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_jail_info.py` — edit the module, not this file._
