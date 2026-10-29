#!/usr/bin/python
# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_certificate
short_description: Manage Sylve TLS certificates, ACME renewals, activation, and archives
description:
- List, create, update, delete, activate, cancel activation, renew, retry, check domains, or download archives for TLS certificates.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired certificate state or action.
    type: str
    choices:
    - present
    - absent
    - activated
    - activate_cancelled
    - renewed
    - retried
    - domain_check
    - archive
    - query
    default: present
    required: false
  cert_id:
    description: Numeric certificate ID.
    type: int
    aliases:
    - id
    required: false
  name:
    description: Certificate name.
    type: str
    required: false
  domain:
    description: Domain name for C(state=domain_check).
    type: str
    required: false
  dest:
    description: Local destination path when downloading a certificate archive (C(state=archive)).
    type: path
    required: false
  data:
    description: Certificate request payload.
    type: dict
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
- name: Renew TLS certificate #1
  sylve.cloud.sylve_certificate:
    cert_id: 1
    state: renewed

- name: Manage Sylve TLS certificates, ACME renewals, activation, and archives on a specific node using a named context
  sylve.cloud.sylve_certificate:
    context: prod
    node: node1.lan
    state: query
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
certificate:
  description: Certificate details or operation result.
  returned: always
  type: raw
  sample: '{"id": 1, "name": "node1.lan", "status": "issued"}'
"""

from pathlib import Path
from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveCertificateModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": [
                "present",
                "absent",
                "activated",
                "activate_cancelled",
                "renewed",
                "retried",
                "domain_check",
                "archive",
                "query",
            ],
            "default": "present",
        },
        "cert_id": {"type": "int", "aliases": ["id"]},
        "name": {"type": "str"},
        "domain": {"type": "str"},
        "dest": {"type": "path"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        cid = self.params.get("cert_id")
        name = self.params.get("name")
        payload: dict = dict(self.params.get("data") or {})

        if state == "domain_check":
            res = self.client.get(
                "/certificates/domain-check",
                params={"domain": self.params.get("domain")},
                node=self.node,
            )
            self.exit_json(changed=False, certificate=res)
            return

        certs = self.client.get("/certificates", node=self.node) or []
        if state == "query":
            self.exit_json(changed=False, certificate=certs)
            return

        existing = None
        for c in certs if isinstance(certs, list) else []:
            if not isinstance(c, dict):
                continue
            if cid is not None and c.get("id") == cid:
                existing = c
                break
            if name and str(c.get("name") or "").lower() == name.lower():
                existing = c
                cid = int(c["id"])
                break

        if state == "archive":
            if cid is None or not self.params.get("dest"):
                self.fail_json(msg="Both 'cert_id' and 'dest' are required for state=archive.")
            if not self.check_mode:
                out = self.client.download_file(
                    f"/certificates/{cid}/archive", self.params["dest"], node=self.node
                )
            else:
                out = Path(self.params["dest"])
            self.exit_json(changed=True, certificate={"dest": str(out)})
            return

        if state == "absent":
            if cid is None:
                self.exit_json(changed=False, certificate={})
                return
            if not self.check_mode:
                self.client.delete(f"/certificates/{cid}", node=self.node)
            self.exit_json(changed=True, certificate=existing or {"id": cid})
            return

        if state in ("activated", "activate_cancelled", "renewed", "retried"):
            if cid is None:
                self.fail_json(msg="Certificate not found.")
            if not self.check_mode:
                if state == "activated":
                    resp = self.client.post(
                        f"/certificates/{cid}/activate", json_body=payload, node=self.node
                    )
                elif state == "activate_cancelled":
                    resp = self.client.delete(
                        f"/certificates/{cid}/activate", node=self.node
                    )
                elif state == "renewed":
                    resp = self.client.post(f"/certificates/{cid}/renew", node=self.node)
                else:
                    resp = self.client.post(f"/certificates/{cid}/retry", node=self.node)
            else:
                resp = {"id": cid, "state": state}
            self.exit_json(changed=True, certificate=resp or {"id": cid})
            return

        if name:
            payload.setdefault("name", name)

        if existing and cid is not None:
            if not self.subset_differs(payload, existing):
                self.exit_json(changed=False, certificate=existing)
                return
            if not self.check_mode:
                resp = self.client.patch(
                    f"/certificates/{cid}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, certificate=resp or payload)
            return

        if not self.check_mode:
            resp = self.client.post("/certificates", json_body=payload, node=self.node)
        else:
            resp = payload
        self.exit_json(changed=True, certificate=resp or payload)


def main() -> None:
    SylveCertificateModule()()


if __name__ == "__main__":
    main()
