# sylve_vm_info

_Gather information about Sylve Bhyve VMs, templates, snapshots, stats, and logs_

Query Bhyve virtual machines, simple summaries, libvirt domain XML, QEMU guest-agent data, console logs, snapshots, templates, and RRD stats.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_vm_info`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `vm` | `str` | no | — | — | Optional VM RID or name to query a single VM. |
| `simple` | `bool` | no | `false` | — | Use C(/vm/simple) instead of full C(/vm) details. |
| `include_domain` | `bool` | no | `false` | — | Include libvirt domain XML (C(/vm/{rid}/domain)) when querying a single VM. |
| `include_guest_agent` | `bool` | no | `false` | — | Include QEMU guest agent info (C(/vm/{rid}/guest-agent)) when querying a single VM. |
| `include_logs` | `bool` | no | `false` | — | Include console logs (C(/vm/{rid}/logs)) when querying a single VM. |
| `include_snapshots` | `bool` | no | `false` | — | Include VM snapshots (C(/vm/{rid}/snapshots)) when querying a single VM. |
| `include_stats` | `bool` | no | `false` | — | Include VM stats (C(/vm/{rid}/stats) or C(/vm/{rid}/stats/{step})). |
| `stats_step` | `str` | no | — | — | Optional step interval for C(/vm/{rid}/stats/{step}). |
| `include_templates` | `bool` | no | `false` | — | Also list VM templates across the cluster/node (C(/vm/templates)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: List all VMs across the cluster
  sylve.cloud.sylve_vm_info:
  register: vm_info

- name: Gather information about Sylve Bhyve VMs, templates, snapshots, stats, and logs on a specific node using a named context
  sylve.cloud.sylve_vm_info:
    context: prod
    node: node1.lan
    simple: true
    include_templates: true
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `vms` | `list` | always | List of matching virtual machines. | `[{"rid": 101, "name": "web-01", "state": "RUNNING"}]` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_vm_info.py` — edit the module, not this file._
