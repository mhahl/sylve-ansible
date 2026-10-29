# sylve_vm

_Manage Sylve Bhyve virtual machines_

Create, update, start, stop, shut down, reboot, migrate, or delete Bhyve virtual machines on Sylve.

Supports creating VMs from scratch (C(POST /vm)) or deploying from a VM template (C(POST /vm/templates/{id}/vms)).

Supports day-2 updates to name, description, CPU, RAM, VNC, PCI passthrough, and VM options.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_vm`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `started`, `stopped`, `shutdown`, `rebooted`, `migrated`, `domain_reinitialized`, `registration_purged` | Desired VM state. |
| `name` | `str` | no | — | — | VM name. |
| `rid` | `int` | no | — | — | Numeric VM RID (1-9999). |
| `new_name` | `str` | no | — | — | New name when renaming an existing VM. |
| `description` | `str` | no | — | — | VM description. |
| `template` | `str` | no | — | — | Template ID or name when deploying a VM from a template. |
| `template_options` | `dict` | no | — | — | Additional payload options for template deployment (e.g. C(mode), C(startRid), C(count), C(namePrefix), C(storagePools)). |
| `cpu_sockets` | `int` | no | — | — | Number of CPU sockets. |
| `cpu_cores` (aliases: `cores`, `cpu`) | `int` | no | — | — | Number of CPU cores per socket. |
| `cpu_threads` | `int` | no | — | — | Number of threads per core. |
| `cpu_pinning` | `list` | no | — | — | CPU pinning list. |
| `ram` (aliases: `memory`) | `raw` | no | — | — | Memory size (integer bytes or human-readable like C(2G), C(512M)). |
| `storage_type` | `str` | no | — | `zvol`, `raw`, `image`, `filesystem`, `none` | Primary disk storage type for VM creation. |
| `storage_pool` (aliases: `pool`) | `str` | no | — | — | ZFS pool name for primary disk. |
| `storage_size` (aliases: `disk_size`) | `raw` | no | — | — | Primary disk size (integer bytes or human-readable like C(20G)). |
| `storage_emulation_type` | `str` | no | — | `virtio-blk`, `virtio-9p`, `ahci-hd`, `ahci-cd`, `nvme` | Primary disk emulation type. |
| `iso` | `str` | no | — | — | ISO/image UUID or download name. |
| `switch_name` (aliases: `switch`) | `str` | no | — | — | Network switch name. |
| `switch_emulation_type` | `str` | no | — | — | Network emulation type (e.g. C(virtio-net), C(e1000)). |
| `mac_id` | `int` | no | — | — | MAC object ID. |
| `vnc_enabled` | `bool` | no | — | — | Enable VNC console. |
| `vnc_bind` | `str` | no | — | — | VNC bind address. |
| `vnc_port` | `int` | no | — | — | VNC port. Auto-selected as the first free port in 5900-5999 on the target node when omitted. |
| `vnc_password` | `str` | no | — | — | VNC password. A random 12-character password is generated on create when VNC is enabled and this is omitted; it is returned as C(vnc_password) in the result. On update the key is omitted from the request when neither the task nor the live config provides one (never sent empty). |
| `vnc_resolution` | `str` | no | — | — | VNC resolution (e.g. C(1024x768)). |
| `vnc_wait` | `bool` | no | — | — | Wait for VNC connection before booting. |
| `pci_devices` | `list` | no | — | — | List of PCI passthrough device IDs. |
| `cloud_init` | `bool` | no | — | — | Enable cloud-init. |
| `cloud_init_data` | `str` | no | — | — | Cloud-init user-data YAML string. |
| `cloud_init_meta_data` | `str` | no | — | — | Cloud-init meta-data YAML string. |
| `cloud_init_network_config` | `str` | no | — | — | Cloud-init network-config YAML string. |
| `boot_rom` | `str` | no | — | — | Boot ROM (C(uefi), C(uboot), C(none)). |
| `time_offset` | `str` | no | — | — | Clock offset (C(utc) or C(localtime)). |
| `start_at_boot` | `bool` | no | — | — | Start VM at host boot. |
| `start_order` | `int` | no | — | — | Boot order priority. |
| `serial` | `bool` | no | — | — | Enable serial console. |
| `tpm_emulation` | `bool` | no | — | — | Enable TPM emulation. |
| `qemu_guest_agent` | `bool` | no | — | — | Enable QEMU Guest Agent. |
| `ignore_umsr` | `bool` | no | — | — | Ignore unknown MSR accesses. |
| `apic` | `bool` | no | — | — | Enable APIC. |
| `acpi` | `bool` | no | — | — | Enable ACPI. |
| `wol` | `bool` | no | — | — | Enable Wake-on-LAN. |
| `shutdown_wait_time` | `int` | no | — | — | Graceful shutdown wait time in seconds. |
| `extra_bhyve_options` | `list` | no | — | — | Extra bhyve command-line options. |
| `target_node` | `str` | no | — | — | Target cluster node hostname or UUID when C(state=migrated). |
| `delete_volumes` | `bool` | no | `true` | — | Delete attached ZFS volumes when C(state=absent). |
| `delete_raw_disks` | `bool` | no | `true` | — | Delete attached RAW disk images when C(state=absent). |
| `delete_macs` | `bool` | no | `true` | — | Delete associated MAC objects when C(state=absent). |
| `force` | `bool` | no | `false` | — | Force deletion when C(state=absent). |
| `extra_params` | `dict` | no | — | — | Additional raw request fields merged into the create payload. |
| `timeout` | `float` | no | `600.0` | — | HTTP request and lifecycle-task polling timeout in seconds. Raised for this module because creates and migrations can run for several minutes. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
- name: Create and start a Bhyve VM
  sylve.cloud.sylve_vm:
    name: web-01
    rid: 101
    node: node1.lan
    cpu_cores: 2
    ram: 2G
    storage_pool: zroot
    storage_size: 20G
    switch_name: lan0
    state: started

- name: Manage Sylve Bhyve virtual machines on a specific node using a named context
  sylve.cloud.sylve_vm:
    context: prod
    node: node1.lan
    name: web-01
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
| `vm` | `dict` | always | Virtual machine representation. | `{"rid": 101, "name": "web-01", "state": "RUNNING"}` |
| `task` | `dict` | when a task is executed and C(wait=true) | Completed lifecycle, migration, replication, or backup task details. | `{"id": 42, "status": "completed"}` |
| `vnc_password` | `str` | when a VNC password is auto-generated | Auto-generated VNC password. Only returned when VNC is enabled, no password was supplied, and the module generated one. | `aB3dE5gH7jK9` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_vm.py` — edit the module, not this file._
