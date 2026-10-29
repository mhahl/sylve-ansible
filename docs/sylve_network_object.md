# sylve_network_object

_Manage Sylve network and firewall alias objects_

Create, update, delete, or bulk-delete network alias objects (Host, Network, Port, Mac).

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_network_object`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent` | Desired network object state. |
| `object_id` (aliases: `id`) | `int` | no | — | — | Numeric network object ID. |
| `ids` | `list` | no | — | — | List of object IDs for bulk deletion when C(state=absent). |
| `name` | `str` | no | — | — | Network object name. |
| `type` | `str` | no | — | — | Object type (e.g. C(Host), C(Network), C(Port), C(Mac)). |
| `values` | `list` | no | — | — | List of values (IPs, CIDRs, ports, or MAC addresses). |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create a MAC address object
  sylve.cloud.sylve_network_object:
    name: web-01-mac
    type: Mac
    values: ["02:00:00:10:20:30"]
    state: present

- name: Manage Sylve network and firewall alias objects on a specific node using a named context
  sylve.cloud.sylve_network_object:
    context: prod
    node: node1.lan
    name: web-01-mac
    type: Mac
    values: ["02:00:00:10:20:30"]
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
| `object` | `dict` | always | Network object details. | `{"id": 9, "name": "web-01-mac", "type": "Mac"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_network_object.py` — edit the module, not this file._
