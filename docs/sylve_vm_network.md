# sylve_vm_network

_Manage network interfaces attached to a Sylve Bhyve VM_

Attach, update, or detach network interfaces on a Bhyve VM.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_vm_network`)
- **Added in:** `sylve.cloud 1.0.0`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent` | Desired network attachment state. |
| `vm` | `str` | yes | — | — | VM RID or name. |
| `network_id` | `int` | no | — | — | VM network attachment ID. |
| `switch_name` (aliases: `switch`) | `str` | no | — | — | Switch name to attach. |
| `emulation` | `str` | no | — | — | NIC emulation type (e.g. C(virtio-net), C(e1000)). |
| `mac_id` | `int` | no | — | — | MAC object ID. |
| `data` | `dict` | no | — | — | Additional raw request fields. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Attach VM 101 to switch lan0
  sylve.cloud.sylve_vm_network:
    vm: 101
    switch_name: lan0
    emulation: virtio-net
    state: present

- name: Manage network interfaces attached to a Sylve Bhyve VM on a specific node using a named context
  sylve.cloud.sylve_vm_network:
    context: prod
    node: node1.lan
    vm: web-01
    switch_name: lan0
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
| `network` | `dict` | always | VM network attachment details. | `{"id": 1, "switchName": "lan0"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_vm_network.py` — edit the module, not this file._
