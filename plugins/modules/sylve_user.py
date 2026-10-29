#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""
---
module: sylve_user
short_description: Manage Sylve local, PAM, and imported Unix users and user passkeys
description:
  - Create, import, update, or delete local, PAM, and Unix users, query user capabilities/importable users/next UID, and manage user passkeys.
extends_documentation_fragment:
  - sylve.cloud.sylve
options:
  state:
    description: Desired user state or action.
    type: str
    choices: [present, pam_present, imported, absent, passkey_absent, info]
    default: present
  user_id:
    description: Numeric user ID.
    type: int
    aliases: [id]
  name:
    description: Username.
    type: str
  user_password:
    description: Password for the managed user account.
    type: str
  email:
    description: User email address.
    type: str
  uid:
    description: Unix UID.
    type: int
  admin:
    description: Administrator privilege flag.
    type: bool
  credential_id:
    description: Passkey credential ID when C(state=passkey_absent).
    type: str
  data:
    description: Additional raw request fields.
    type: dict
"""

EXAMPLES = r"""
- name: Create a local Sylve user
  sylve.cloud.sylve_user:
    name: devops
    user_password: "{{ vault_user_password }}"
    admin: true
    state: present
"""

RETURN = r"""
user:
  description: User details or info dictionary.
  returned: always
  type: raw
"""

from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveUserModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": [
                "present",
                "pam_present",
                "imported",
                "absent",
                "passkey_absent",
                "info",
            ],
            "default": "present",
        },
        "user_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "user_password": {"type": "str", "no_log": True},
        "email": {"type": "str"},
        "uid": {"type": "int"},
        "admin": {"type": "bool"},
        "credential_id": {"type": "str"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        uid_param = self.params.get("user_id")
        uname = self.params.get("name")
        users = self.client.get("/auth/users", node=self.node) or []

        existing = None
        for u in users if isinstance(users, list) else []:
            if not isinstance(u, dict):
                continue
            if uid_param is not None and u.get("id") == uid_param:
                existing = u
                break
            if uname and str(u.get("username") or u.get("name") or "").lower() == uname.lower():
                existing = u
                uid_param = int(u["id"])
                break

        if state == "info":
            info: dict = {
                "users": users,
                "capabilities": self.client.get("/auth/users/capabilities", node=self.node),
                "importable": self.client.get("/auth/users/importable", node=self.node),
                "next_uid": self.client.get("/auth/users/uid/next", node=self.node),
            }
            if uid_param is not None:
                info["passkeys"] = self.client.get(
                    f"/auth/users/{uid_param}/passkeys", node=self.node
                )
            self.exit_json(changed=False, user=info)
            return

        if state == "passkey_absent":
            cred = self.params.get("credential_id")
            if uid_param is None or not cred:
                self.fail_json(msg="user_id/name and credential_id are required.")
            if not self.check_mode:
                self.client.delete(
                    f"/auth/users/{uid_param}/passkeys/{cred}", node=self.node
                )
            self.exit_json(changed=True, user={"user_id": uid_param, "credential_id": cred})
            return

        if state == "absent":
            if uid_param is None:
                self.exit_json(changed=False, user={})
                return
            if not self.check_mode:
                self.client.delete(f"/auth/users/{uid_param}", node=self.node)
            self.exit_json(changed=True, user=existing or {"id": uid_param})
            return

        payload: dict = dict(self.params.get("data") or {})
        if uname is not None:
            payload.setdefault("username", uname)
        if self.params.get("user_password") is not None:
            payload["password"] = self.params["user_password"]
        for key in ("email", "uid", "admin"):
            if self.params.get(key) is not None:
                payload[key] = self.params[key]

        if existing and uid_param is not None:
            compare_payload = {k: v for k, v in payload.items() if k != "password"}
            if not self.subset_differs(compare_payload, existing) and "password" not in payload:
                self.exit_json(changed=False, user=existing)
                return
            if not self.check_mode:
                resp = self.client.put(
                    f"/auth/users/{uid_param}", json_body=payload, node=self.node
                )
            else:
                resp = compare_payload
            self.exit_json(changed=True, user=resp or compare_payload)
            return

        endpoint = {
            "present": "/auth/users",
            "pam_present": "/auth/users/pam",
            "imported": "/auth/users/import",
        }[state]
        if not self.check_mode:
            resp = self.client.post(endpoint, json_body=payload, node=self.node)
        else:
            resp = {k: v for k, v in payload.items() if k != "password"}
        self.exit_json(changed=True, user=resp or {})


def main() -> None:
    SylveUserModule()()


if __name__ == "__main__":
    main()
