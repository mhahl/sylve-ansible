#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_jail
short_description: Manage Sylve FreeBSD jails
description:
- Create, validate, update, start, stop, restart, migrate, or delete FreeBSD jails on Sylve.
- Supports creating jails from scratch (C(POST /jail)) or from a template (C(POST /jail/templates/{id}/jails)).
- Supports day-2 updates to name, description, CPU, RAM, resource limits, network inheritance, and jail options.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired jail state.
    type: str
    choices:
    - present
    - absent
    - started
    - stopped
    - restarted
    - migrated
    - validated
    default: present
    required: false
  name:
    description: Jail name.
    type: str
    required: false
  ctid:
    description: Numeric jail CTID.
    type: int
    aliases:
    - ct_id
    required: false
  new_name:
    description: New name when renaming an existing jail.
    type: str
    required: false
  description:
    description: Jail description.
    type: str
    required: false
  pool:
    description: ZFS pool for jail root dataset.
    type: str
    required: false
  type:
    description: Jail type (e.g. C(freebsd), C(linux)).
    type: str
    default: freebsd
    required: false
  base:
    description: Base rootfs download UUID or bootstrap name.
    type: str
    required: false
  template:
    description: Jail template ID when deploying from a template.
    type: int
    required: false
  template_options:
    description: Additional options when deploying from a template.
    type: dict
    required: false
  cores:
    description: CPU core limit.
    type: int
    aliases:
    - cpu
    required: false
  memory:
    description: Memory limit (bytes or human-readable like C(1G), C(512M)).
    type: raw
    aliases:
    - ram
    required: false
  resource_limits:
    description: Enable or disable RCTL resource limits.
    type: bool
    required: false
  inherit_ipv4:
    description: Inherit host IPv4 stack.
    type: bool
    required: false
  inherit_ipv6:
    description: Inherit host IPv6 stack.
    type: bool
    required: false
  start_at_boot:
    description: Start jail at host boot.
    type: bool
    required: false
  boot_order:
    description: Boot order priority.
    type: int
    required: false
  devfs_ruleset:
    description: DevFS ruleset number.
    type: int
    required: false
  additional_options:
    description: Additional raw jail.conf options string.
    type: str
    required: false
  allowed_options:
    description: List of allowed jail permissions (e.g. C(allow.raw_sockets)).
    type: list
    elements: str
    required: false
  execution_timeout:
    description: Start/stop execution timeout in seconds.
    type: int
    required: false
  fstab:
    description: Jail fstab entries string.
    type: str
    required: false
  lifecycle_hooks:
    description: Jail lifecycle hook commands dictionary.
    type: dict
    required: false
  metadata:
    description: Jail metadata (C(meta) and C(env)).
    type: dict
    required: false
  resolv_conf:
    description: Custom C(/etc/resolv.conf) content.
    type: str
    required: false
  wol:
    description: Enable Wake-on-LAN.
    type: bool
    required: false
  target_node:
    description: Target cluster node hostname or UUID when C(state=migrated).
    type: str
    required: false
  delete_rootfs:
    description: Delete jail root ZFS dataset when C(state=absent).
    type: bool
    default: true
    required: false
  delete_macs:
    description: Delete unused MAC objects when C(state=absent).
    type: bool
    default: true
    required: false
  extra_params:
    description: Additional raw fields merged into the jail creation payload.
    type: dict
    required: false
  timeout:
    description: HTTP request and lifecycle-task polling timeout in seconds. Raised for this module because creates and migrations can run for several minutes.
    type: float
    default: 600.0
    required: false
version_added: 0.3.1
author:
- Sylve Contributors (@mhahl)
requirements:
- python >= 3.10
- PyYAML
attributes:
  check_mode:
    description: Can run in check mode and return changed status prediction without modifying the target.
    support: full
  diff_mode:
    description: Will return details on what has changed when in diff mode. This module does not report diffs.
    support: none
notes:
- Supports C(check_mode).
- 'C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.'
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).
seealso:
- module: sylve.cloud.sylve_api
  description: Execute any Sylve REST API endpoint directly.
- name: sylve.cloud collection README
  link: https://github.com/mhahl/sylve-ansible
  description: Authentication, configuration, and inventory plugin usage.
"""

EXAMPLES = r"""
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
"""

RETURN = r"""changed:
  description: Whether the module made changes on the Sylve cluster.
  returned: always
  type: bool
  sample: true
jail:
  description: Jail representation.
  returned: always
  type: dict
  sample: '{"ctId": 201, "name": "app-01", "state": "RUNNING"}'
task:
  description: Completed lifecycle, migration, replication, or backup task details.
  returned: when a task is executed and C(wait=true)
  type: dict
  sample: '{"id": 42, "status": "completed"}'
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import (
    ResourceNotFoundError,
    SylveModule,
    parse_size,
)


class SylveJailModule(SylveModule):
    default_timeout = 600.0
    argument_spec = {
        "state": {
            "type": "str",
            "choices": [
                "present",
                "absent",
                "started",
                "stopped",
                "restarted",
                "migrated",
                "validated",
            ],
            "default": "present",
        },
        "name": {"type": "str"},
        "ctid": {"type": "int", "aliases": ["ct_id"]},
        "new_name": {"type": "str"},
        "description": {"type": "str"},
        "pool": {"type": "str"},
        "type": {"type": "str", "default": "freebsd"},
        "base": {"type": "str"},
        "template": {"type": "int"},
        "template_options": {"type": "dict"},
        "cores": {"type": "int", "aliases": ["cpu"]},
        "memory": {"type": "raw", "aliases": ["ram"]},
        "resource_limits": {"type": "bool"},
        "inherit_ipv4": {"type": "bool"},
        "inherit_ipv6": {"type": "bool"},
        "start_at_boot": {"type": "bool"},
        "boot_order": {"type": "int"},
        "devfs_ruleset": {"type": "int"},
        "additional_options": {"type": "str"},
        "allowed_options": {"type": "list", "elements": "str"},
        "execution_timeout": {"type": "int"},
        "fstab": {"type": "str"},
        "lifecycle_hooks": {"type": "dict"},
        "metadata": {"type": "dict"},
        "resolv_conf": {"type": "str"},
        "wol": {"type": "bool"},
        "target_node": {"type": "str"},
        "delete_rootfs": {"type": "bool", "default": True},
        "delete_macs": {"type": "bool", "default": True},
        "extra_params": {"type": "dict"},
    }

    def _find_jail(self) -> tuple[int | None, str | None, dict]:
        ident = self.params.get("ctid") or self.params.get("name")
        if not ident:
            self.fail_json(msg="Either 'ctid' or 'name' is required.")
        try:
            ctid, host, summary = self.client.resolve_jail(ident, node=self.node)
            detail = self.client.get(f"/jail/{ctid}", node=host or self.node)
            if isinstance(detail, dict):
                detail.setdefault("state", summary.get("state"))
                return ctid, host or self.node, detail
            return ctid, host or self.node, summary
        except ResourceNotFoundError:
            if self.params.get("ctid") and self.params.get("name"):
                try:
                    ctid, host, summary = self.client.resolve_jail(
                        self.params["name"], node=self.node
                    )
                    detail = self.client.get(f"/jail/{ctid}", node=host or self.node)
                    return ctid, host or self.node, detail if isinstance(detail, dict) else summary
                except ResourceNotFoundError:
                    pass
            return None, self.client.resolve_node_hostname(self.node), {}

    def _build_create_payload(self) -> dict:
        p = self.params
        payload: dict = {
            "name": p.get("name"),
            "ctId": p.get("ctid") or 200,
            "type": p.get("type") or "freebsd",
        }
        if p.get("pool"):
            payload["pool"] = p["pool"]
        if p.get("base"):
            payload["base"] = p["base"]
        if p.get("description") is not None:
            payload["description"] = p["description"]
        if p.get("cores") is not None:
            payload["cores"] = p["cores"]
        if p.get("memory") is not None:
            payload["memory"] = parse_size(p["memory"], "memory")
        if p.get("resource_limits") is not None:
            payload["resourceLimits"] = p["resource_limits"]
        if p.get("inherit_ipv4") is not None:
            payload["inheritIPv4"] = p["inherit_ipv4"]
        if p.get("inherit_ipv6") is not None:
            payload["inheritIPv6"] = p["inherit_ipv6"]
        if p.get("start_at_boot") is not None:
            payload["startAtBoot"] = p["start_at_boot"]
        if p.get("boot_order") is not None:
            payload["bootOrder"] = p["boot_order"]
        if p.get("devfs_ruleset") is not None:
            payload["devfsRuleset"] = p["devfs_ruleset"]
        if p.get("additional_options") is not None:
            payload["additionalOptions"] = p["additional_options"]
        if p.get("allowed_options") is not None:
            payload["allowedOptions"] = p["allowed_options"]
        if p.get("fstab") is not None:
            payload["fstab"] = p["fstab"]
        if p.get("resolv_conf") is not None:
            payload["resolvConf"] = p["resolv_conf"]
        if p.get("wol") is not None:
            payload["wol"] = p["wol"]
        if p.get("extra_params"):
            payload.update(p["extra_params"])
        return payload

    def _update_existing_jail(self, ctid: int, host: str | None, current: dict) -> bool:
        p = self.params
        changed = False

        if p.get("new_name") and current.get("name") != p["new_name"]:
            changed = True
            if not self.check_mode:
                self.client.patch(
                    f"/jail/{ctid}/name", json_body={"name": p["new_name"]}, node=host
                )

        if p.get("description") is not None and current.get("description") != p["description"]:
            changed = True
            if not self.check_mode:
                self.client.patch(
                    f"/jail/{ctid}/description",
                    json_body={"description": p["description"]},
                    node=host,
                )

        if p.get("cores") is not None and current.get("cores") != p["cores"]:
            changed = True
            if not self.check_mode:
                self.client.put(
                    f"/jail/{ctid}/hardware/cpu", json_body={"cores": p["cores"]}, node=host
                )

        if p.get("memory") is not None:
            mem_bytes = parse_size(p["memory"], "memory")
            if current.get("memory") != mem_bytes:
                changed = True
                if not self.check_mode:
                    self.client.put(
                        f"/jail/{ctid}/hardware/ram", json_body={"memory": mem_bytes}, node=host
                    )

        if (
            p.get("resource_limits") is not None
            and current.get("resourceLimits") != p["resource_limits"]
        ):
            changed = True
            if not self.check_mode:
                self.client.put(
                    f"/jail/{ctid}/hardware/resource-limits",
                    json_body={"enabled": p["resource_limits"]},
                    node=host,
                )

        if self.subset_differs(
            {"inheritIPv4": p.get("inherit_ipv4"), "inheritIPv6": p.get("inherit_ipv6")},
            current,
        ):
            changed = True
            if not self.check_mode:
                self.client.put(
                    f"/jail/{ctid}/network/inheritance",
                    json_body={
                        "ipv4": (
                            p["inherit_ipv4"]
                            if p.get("inherit_ipv4") is not None
                            else bool(current.get("inheritIPv4", False))
                        ),
                        "ipv6": (
                            p["inherit_ipv6"]
                            if p.get("inherit_ipv6") is not None
                            else bool(current.get("inheritIPv6", False))
                        ),
                    },
                    node=host,
                )

        option_updates = [
            (
                {"additionalOptions": p.get("additional_options")},
                f"/jail/{ctid}/options/additional-options",
                lambda: {"additionalOptions": p["additional_options"]},
            ),
            (
                {"allowedOptions": p.get("allowed_options")},
                f"/jail/{ctid}/options/allowed-options",
                lambda: {"allowedOptions": p["allowed_options"]},
            ),
            (
                {"startAtBoot": p.get("start_at_boot"), "bootOrder": p.get("boot_order")},
                f"/jail/{ctid}/options/boot-order",
                lambda: {
                    "startAtBoot": (
                        p["start_at_boot"]
                        if p.get("start_at_boot") is not None
                        else bool(current.get("startAtBoot", False))
                    ),
                    "bootOrder": (
                        p["boot_order"]
                        if p.get("boot_order") is not None
                        else int(current.get("bootOrder") or 0)
                    ),
                },
            ),
            (
                {"devfsRuleset": p.get("devfs_ruleset")},
                f"/jail/{ctid}/options/devfs-rules",
                lambda: {"devfsRuleset": p["devfs_ruleset"]},
            ),
            (
                {"executionTimeout": p.get("execution_timeout")},
                f"/jail/{ctid}/options/execution-timeout",
                lambda: {"executionTimeout": p["execution_timeout"]},
            ),
            (
                {"fstab": p.get("fstab")},
                f"/jail/{ctid}/options/fstab",
                lambda: {"fstab": p["fstab"]},
            ),
            (
                {"resolvConf": p.get("resolv_conf")},
                f"/jail/{ctid}/options/resolv-conf",
                lambda: {"resolvConf": p["resolv_conf"]},
            ),
            (
                {"wol": p.get("wol")},
                f"/jail/{ctid}/options/wol",
                lambda: {"wol": p["wol"]},
            ),
        ]
        for desired_map, endpoint, body_fn in option_updates:
            if self.subset_differs(desired_map, current):
                changed = True
                if not self.check_mode:
                    self.client.put(endpoint, json_body=body_fn(), node=host)

        if p.get("lifecycle_hooks") is not None:
            changed = True
            if not self.check_mode:
                self.client.put(
                    f"/jail/{ctid}/options/lifecycle-hooks",
                    json_body=p["lifecycle_hooks"],
                    node=host,
                )

        if p.get("metadata") is not None:
            changed = True
            if not self.check_mode:
                self.client.put(
                    f"/jail/{ctid}/options/metadata", json_body=p["metadata"], node=host
                )

        return changed

    def run(self) -> None:
        state = self.params["state"]
        if state == "validated":
            payload = self._build_create_payload()
            res = self.client.post("/jail/validate", json_body=payload, node=self.node)
            self.exit_json(changed=False, jail=res or payload)
            return

        ctid, host, current = self._find_jail()

        if state == "absent":
            if ctid is None:
                self.exit_json(changed=False, jail={})
                return
            if not self.check_mode:
                self.client.delete(
                    f"/jail/{ctid}",
                    params={
                        "deleterootfs": self.params["delete_rootfs"],
                        "deletemacs": self.params["delete_macs"],
                    },
                    node=host,
                )
            self.exit_json(changed=True, jail=current)
            return

        changed = False
        task = None

        if ctid is None:
            if state in ("stopped", "restarted", "migrated"):
                self.fail_json(msg=f"Jail not found for state={state}.")
            changed = True
            if self.check_mode:
                self.exit_json(changed=True, jail=self._build_create_payload())
                return
            if self.params.get("template"):
                tid = self.params["template"]
                body = dict(self.params.get("template_options") or {})
                if self.params.get("name"):
                    body.setdefault("name", self.params["name"])
                if self.params.get("ctid"):
                    body.setdefault("ctId", self.params["ctid"])
                body.setdefault("mode", "single")
                resp = self.client.post(f"/jail/templates/{tid}/jails", json_body=body, node=host)
                task = self.wait_task(resp, node=host)
                ctid, host, current = self._find_jail()
            else:
                payload = self._build_create_payload()
                resp = self.client.post("/jail", json_body=payload, node=host)
                ctid = int((resp or {}).get("ctId") or payload["ctId"])
                current = self.client.get(f"/jail/{ctid}", node=host) or payload
        else:
            if self._update_existing_jail(ctid, host, current):
                changed = True
                if not self.check_mode:
                    current = self.client.get(f"/jail/{ctid}", node=host) or current

        if state == "migrated" and ctid is not None:
            target_node = self.params.get("target_node")
            if not target_node:
                self.fail_json(msg="target_node is required when state=migrated.")
            target_uuid, target_host = self.client.resolve_node_uuid(target_node)
            if (host or "").lower() != target_host.lower():
                changed = True
                self.client.get(
                    "/tasks/migration/validate",
                    params={
                        "guestType": "jail",
                        "guestId": ctid,
                        "targetNodeUuid": target_uuid,
                    },
                    node=host,
                )
                if not self.check_mode:
                    resp = self.client.post(
                        f"/jail/{ctid}/migrations",
                        json_body={"targetNodeUuid": target_uuid},
                        node=host,
                    )
                    task = self.wait_task(resp, node=host)

        elif state in ("started", "stopped", "restarted") and ctid is not None:
            j_state = str(current.get("state") or "").upper()
            if not j_state:
                st_res = self.client.get(f"/jail/{ctid}/state", node=host)
                if isinstance(st_res, dict):
                    j_state = str(st_res.get("state") or "").upper()
            is_running = j_state in ("RUNNING", "ACTIVE", "UP")
            action_map = {
                "started": ("start", not is_running),
                "stopped": ("stop", is_running),
                "restarted": ("restart", True),
            }
            action, should_run = action_map[state]
            if should_run:
                changed = True
                if not self.check_mode:
                    resp = self.client.post(f"/jail/{ctid}/actions/{action}", node=host)
                    task = self.wait_task(resp, node=host)
                    current = self.client.get(f"/jail/{ctid}", node=host) or current

        self.exit_json(changed=changed, jail=current, task=task)


def main() -> None:
    SylveJailModule()()


if __name__ == "__main__":
    main()
