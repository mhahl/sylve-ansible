# sylve_jail

_Manage Sylve FreeBSD jails_

Create, validate, update, start, stop, restart, migrate, or delete FreeBSD jails on Sylve.

Supports creating jails from scratch (C(POST /jail)) or from a template (C(POST /jail/templates/{id}/jails)).

Supports day-2 updates to name, description, CPU, RAM, resource limits, network inheritance, and jail options.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_jail`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `started`, `stopped`, `restarted`, `migrated`, `validated` | Desired jail state. |
| `name` | `str` | no | — | — | Jail name. |
| `ctid` (aliases: `ct_id`) | `int` | no | — | — | Numeric jail CTID. |
| `new_name` | `str` | no | — | — | New name when renaming an existing jail. |
| `description` | `str` | no | — | — | Jail description. |
| `pool` | `str` | no | — | — | ZFS pool for jail root dataset. |
| `type` | `str` | no | `freebsd` | — | Jail type (e.g. C(freebsd), C(linux)). |
| `base` | `str` | no | — | — | Base rootfs download UUID or bootstrap name. |
| `template` | `int` | no | — | — | Jail template ID when deploying from a template. |
| `template_options` | `dict` | no | — | — | Additional options when deploying from a template. |
| `cores` (aliases: `cpu`) | `int` | no | — | — | CPU core limit. |
| `memory` (aliases: `ram`) | `raw` | no | — | — | Memory limit (bytes or human-readable like C(1G), C(512M)). |
| `resource_limits` | `bool` | no | — | — | Enable or disable RCTL resource limits. |
| `inherit_ipv4` | `bool` | no | — | — | Inherit host IPv4 stack. |
| `inherit_ipv6` | `bool` | no | — | — | Inherit host IPv6 stack. |
| `start_at_boot` | `bool` | no | — | — | Start jail at host boot. |
| `boot_order` | `int` | no | — | — | Boot order priority. |
| `devfs_ruleset` | `int` | no | — | — | DevFS ruleset number. |
| `additional_options` | `str` | no | — | — | Additional raw jail.conf options string. |
| `allowed_options` | `list` | no | — | — | List of allowed jail permissions (e.g. C(allow.raw_sockets)). |
| `execution_timeout` | `int` | no | — | — | Start/stop execution timeout in seconds. |
| `fstab` | `str` | no | — | — | Jail fstab entries string. |
| `lifecycle_hooks` | `dict` | no | — | — | Jail lifecycle hook commands dictionary. |
| `metadata` | `dict` | no | — | — | Jail metadata (C(meta) and C(env)). |
| `resolv_conf` | `str` | no | — | — | Custom C(/etc/resolv.conf) content. |
| `wol` | `bool` | no | — | — | Enable Wake-on-LAN. |
| `target_node` | `str` | no | — | — | Target cluster node hostname or UUID when C(state=migrated). |
| `delete_rootfs` | `bool` | no | `true` | — | Delete jail root ZFS dataset when C(state=absent). |
| `delete_macs` | `bool` | no | `true` | — | Delete unused MAC objects when C(state=absent). |
| `extra_params` | `dict` | no | — | — | Additional raw fields merged into the jail creation payload. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create and start a FreeBSD jail
  sylve.cloud.sylve_jail:
    name: app-01
    ctid: 201
    pool: zroot
    cores: 2
    memory: 1G
    state: started

- name: Manage Sylve FreeBSD jails on a specific node using a named context
  sylve.cloud.sylve_jail:
    context: prod
    node: node1.lan
    name: app-01
    state: started
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `jail` | `dict` | always | Jail representation. | `{"ctId": 201, "name": "app-01", "state": "RUNNING"}` |
| `task` | `dict` | when a task is executed and C(wait=true) | Completed lifecycle, migration, replication, or backup task details. | `{"id": 42, "status": "completed"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_jail.py` — edit the module, not this file._
