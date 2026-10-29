# sylve_jail_bootstrap

_Manage pkgbase FreeBSD jail bootstraps on Sylve_

List, create, or delete pkgbase FreeBSD jail bootstraps on a ZFS pool.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_jail_bootstrap`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent` | Desired bootstrap state. |
| `name` | `str` | no | — | — | Bootstrap dataset/entry name (used for C(state=absent) or matching). |
| `pool` | `str` | no | — | — | ZFS pool name. |
| `major` | `int` | no | — | — | FreeBSD major version (e.g. C(14) or C(15)). |
| `minor` | `int` | no | `0` | — | FreeBSD minor version (e.g. C(2)). |
| `type` | `str` | no | `base` | — | Bootstrap flavor (e.g. C(base), C(minimal)). |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Ensure FreeBSD 14.2 base jail bootstrap exists on zroot
  sylve.cloud.sylve_jail_bootstrap:
    pool: zroot
    major: 14
    minor: 2
    type: base
    state: present

- name: Manage pkgbase FreeBSD jail bootstraps on Sylve on a specific node using a named context
  sylve.cloud.sylve_jail_bootstrap:
    context: prod
    node: node1.lan
    pool: zroot
    major: 14
    state: present
  register: result

- name: Show result
  ansible.builtin.debug:
    var: result
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `bootstrap` | `dict` | always | Bootstrap record or request payload. | `{"name": "14.2-RELEASE-base", "pool": "zroot"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_jail_bootstrap.py` — edit the module, not this file._
