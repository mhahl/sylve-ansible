# sylve.cloud documentation

Ansible collection for managing Sylve FreeBSD hypervisor clusters.
Each page below mirrors its module's `DOCUMENTATION` block — the module source is the canonical reference.

## Authentication

All modules share `~/.config/sylve/config.yaml` contexts and `SYLVE_*` environment variables with `sylve-cli`. Common options: `config_path`, `context` (alias `cloud`), `auth` dict, `server` (`SYLVE_SERVER`), `token` (`SYLVE_TOKEN`), `username`/`password`, `auth_type`, `node` (`SYLVE_NODE`), `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`.

## Modules

| Module | Short description |
| --- | --- |
| [`sylve_api`](sylve_api.md) | Execute any Sylve Swagger HTTP API request directly |
| [`sylve_backup_job`](sylve_backup_job.md) | Manage Sylve scheduled backup jobs, runs, restores, snapshots, and events |
| [`sylve_backup_target`](sylve_backup_target.md) | Manage Sylve cluster backup targets, validation, datasets, and restores |
| [`sylve_certificate`](sylve_certificate.md) | Manage Sylve TLS certificates, ACME renewals, activation, and archives |
| [`sylve_cloud_init_template`](sylve_cloud_init_template.md) | Manage reusable Sylve cloud-init templates |
| [`sylve_cluster`](sylve_cluster.md) | Manage Sylve cluster formation, membership, resynchronization, and cluster notes |
| [`sylve_cluster_info`](sylve_cluster_info.md) | Gather information about Sylve cluster status, nodes, telemetry, and audit logs |
| [`sylve_ddns`](sylve_ddns.md) | Manage Sylve Dynamic DNS entries |
| [`sylve_dhcp`](sylve_dhcp.md) | Manage Sylve DHCP service configuration, IP ranges, and leases |
| [`sylve_directory_service`](sylve_directory_service.md) | Manage Sylve Active Directory and Kerberos directory services |
| [`sylve_disk`](sylve_disk.md) | Manage Sylve host disks, GPT partition tables, partitions, and SMART self-tests |
| [`sylve_download`](sylve_download.md) | Manage Sylve ISO and disk-image downloads, local uploads, and signed URLs |
| [`sylve_firewall`](sylve_firewall.md) | Manage Sylve PF firewall traffic rules, NAT rules, and advanced settings |
| [`sylve_group`](sylve_group.md) | Manage Sylve authentication groups and group membership |
| [`sylve_iscsi`](sylve_iscsi.md) | Manage Sylve iSCSI global config, initiators, targets, LUNs, and portals |
| [`sylve_jail`](sylve_jail.md) | Manage Sylve FreeBSD jails |
| [`sylve_jail_bootstrap`](sylve_jail_bootstrap.md) | Manage pkgbase FreeBSD jail bootstraps on Sylve |
| [`sylve_jail_info`](sylve_jail_info.md) | Gather information about Sylve FreeBSD jails, bootstraps, templates, and stats |
| [`sylve_jail_network`](sylve_jail_network.md) | Manage network attachments for a Sylve FreeBSD jail |
| [`sylve_jail_snapshot`](sylve_jail_snapshot.md) | Manage ZFS snapshots for a Sylve FreeBSD jail |
| [`sylve_jail_template`](sylve_jail_template.md) | Manage Sylve FreeBSD jail templates |
| [`sylve_mdns`](sylve_mdns.md) | Manage Sylve mDNS configuration and records |
| [`sylve_network_info`](sylve_network_info.md) | Gather information about Sylve network interfaces, switches, routes, DHCP, firewall, and WireGuard |
| [`sylve_network_interface`](sylve_network_interface.md) | Manage Sylve host Layer-3 network interfaces, global network config, and pending IP changes |
| [`sylve_network_object`](sylve_network_object.md) | Manage Sylve network and firewall alias objects |
| [`sylve_node`](sylve_node.md) | Manage Sylve cluster node maintenance drain, reboot, and host notes |
| [`sylve_notification`](sylve_notification.md) | Manage Sylve notification transports, alert rules, and active notifications |
| [`sylve_replication`](sylve_replication.md) | Manage Sylve HA replication policies, manual runs, failovers, and replication events |
| [`sylve_route`](sylve_route.md) | Manage Sylve static network routes |
| [`sylve_samba`](sylve_samba.md) | Manage Sylve Samba global configuration, shares, and audit logs |
| [`sylve_switch`](sylve_switch.md) | Manage Sylve standard and manual network switches |
| [`sylve_system`](sylve_system.md) | Manage Sylve system initialization, pools, services, tunables, PCI passthrough, and files |
| [`sylve_task`](sylve_task.md) | Query, wait for, validate, or cancel Sylve lifecycle and migration tasks |
| [`sylve_user`](sylve_user.md) | Manage Sylve local, PAM, and imported Unix users and user passkeys |
| [`sylve_vm`](sylve_vm.md) | Manage Sylve Bhyve virtual machines |
| [`sylve_vm_info`](sylve_vm_info.md) | Gather information about Sylve Bhyve VMs, templates, snapshots, stats, and logs |
| [`sylve_vm_network`](sylve_vm_network.md) | Manage network interfaces attached to a Sylve Bhyve VM |
| [`sylve_vm_snapshot`](sylve_vm_snapshot.md) | Manage ZFS snapshots for a Sylve Bhyve VM |
| [`sylve_vm_storage`](sylve_vm_storage.md) | Manage storage volumes attached to a Sylve Bhyve VM |
| [`sylve_vm_template`](sylve_vm_template.md) | Manage Sylve Bhyve VM templates |
| [`sylve_wireguard`](sylve_wireguard.md) | Manage Sylve WireGuard VPN server, server peers, and outbound clients |
| [`sylve_zfs_dataset`](sylve_zfs_dataset.md) | Manage Sylve ZFS filesystems and volumes |
| [`sylve_zfs_info`](sylve_zfs_info.md) | Gather information about Sylve ZFS pools, datasets, snapshots, scrubs, and dashboard metrics |
| [`sylve_zfs_pool`](sylve_zfs_pool.md) | Manage Sylve ZFS storage pools, devices, scrubs, and scrub schedules |
| [`sylve_zfs_snapshot`](sylve_zfs_snapshot.md) | Manage Sylve ZFS dataset snapshots and periodic snapshot schedules |

## Inventory

See `plugins/inventory/sylve.py` (`sylve.cloud.sylve`).
