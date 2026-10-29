# `sylve.cloud` Ansible Collection

Ansible collection for managing [Sylve](https://github.com/AlchemillaHQ/Sylve) FreeBSD hypervisor clusters, Bhyve virtual machines, FreeBSD Jails, ZFS storage, networking, replication, and backups.

`sylve.cloud` shares `~/.config/sylve/config.yaml` contexts and `SYLVE_*` environment variables with `sylve-cli`.

## Installation

Requirements on the controller: `ansible-core >= 2.14`, Python `>= 3.10`, `PyYAML`.

From Ansible Galaxy (once published):

```sh
ansible-galaxy collection install sylve.cloud
```

From git:

```sh
ansible-galaxy collection install git+https://github.com/mhahl/sylve-ansible.git
```

From a local checkout (used by the integration playbooks in `tests/integration/`):

```sh
ansible-galaxy collection build
ansible-galaxy collection install sylve-cloud-0.3.1.tar.gz
```

## Quick start

Log in once with `sylve-cli` (or export `SYLVE_SERVER` and `SYLVE_TOKEN`), then use any module:

```yaml
- name: Create a Bhyve VM
  hosts: localhost
  connection: local
  tasks:
    - name: Create web-01
      sylve.cloud.sylve_vm:
        context: prod
        node: node1.lan
        name: web-01
        cpu_cores: 2
        ram: 2G
        storage_pool: zroot
        storage_size: 20G
        switch_name: lan0
        switch_emulation_type: e1000
        state: present
```

Dynamic inventory (`inventory.yml`):

```yaml
plugin: sylve.cloud.sylve
context: prod
```

```sh
ansible-inventory -i inventory.yml --list
```

Module reference lives in [`docs/`](docs/index.md); the module sources are canonical.

## Authentication & Configuration

All modules and the inventory plugin resolve credentials in the following order:

1. Module `auth:` dictionary or top-level parameters (`server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`).
2. Environment variables (`SYLVE_CONFIG`, `SYLVE_CONTEXT`, `SYLVE_SERVER`, `SYLVE_TOKEN`, `SYLVE_NODE`, `SYLVE_INSECURE`, `SYLVE_USERNAME`, `SYLVE_PASSWORD`).
3. Saved contexts in `~/.config/sylve/config.yaml` created by `sylve login`.

## Modules

- **Compute (VMs)**: `sylve_vm`, `sylve_vm_storage`, `sylve_vm_network`, `sylve_vm_snapshot`, `sylve_vm_template`, `sylve_vm_info`
- **Compute (Jails)**: `sylve_jail`, `sylve_jail_network`, `sylve_jail_snapshot`, `sylve_jail_bootstrap`, `sylve_jail_template`, `sylve_jail_info`
- **Networking**: `sylve_switch`, `sylve_network_interface`, `sylve_route`, `sylve_network_object`, `sylve_dhcp`, `sylve_firewall`, `sylve_wireguard`, `sylve_network_info`
- **Storage**: `sylve_zfs_pool`, `sylve_zfs_dataset`, `sylve_zfs_snapshot`, `sylve_zfs_info`, `sylve_disk`, `sylve_samba`, `sylve_iscsi`
- **Cluster, HA & Backups**: `sylve_cluster`, `sylve_node`, `sylve_cluster_info`, `sylve_replication`, `sylve_backup_target`, `sylve_backup_job`, `sylve_task`
- **System, Utilities & IAM**: `sylve_download`, `sylve_cloud_init_template`, `sylve_system`, `sylve_certificate`, `sylve_ddns`, `sylve_mdns`, `sylve_notification`, `sylve_user`, `sylve_group`, `sylve_directory_service`, `sylve_api`
- **Inventory**: `sylve.cloud.sylve`

## Development & testing

```sh
python3 -m pytest -q            # unit tests
yamllint .                      # YAML style (config: .yamllint)
antsibull-changelog lint        # changelog fragments
ansible-test sanity --test validate-modules --test pep8 --test yamllint --test import --python 3.12
ansible-galaxy collection build # build artifact
python3 scripts/generate_docs.py # regenerate docs/ from module documentation
```

`validate-modules` runs against the collection layout (`.../ansible_collections/sylve/cloud`); the BSD-only license headers are covered by `tests/sanity/ignore-*.txt`.

## License

BSD-2-Clause, see [LICENSE](LICENSE).
