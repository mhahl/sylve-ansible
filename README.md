# `sylve.cloud` Ansible Collection

Ansible collection for managing [Sylve](https://github.com/AlchemillaHQ/Sylve) FreeBSD hypervisor clusters, Bhyve virtual machines, FreeBSD Jails, ZFS storage, networking, replication, and backups.

Modeled after `openstack.cloud`, `sylve.cloud` shares `~/.config/sylve/config.yaml` contexts and `SYLVE_*` environment variables with `sylve-cli`.

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
