#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""---
module: sylve_download
short_description: Manage Sylve ISO and disk-image downloads, local uploads, and signed URLs
description:
- Start URL/magnet downloads, upload local ISO/image files to downloader storage, update metadata, mint signed download URLs,
  download completed files locally, query storage paths, or delete downloads.
extends_documentation_fragment:
- sylve.cloud.sylve
options:
  state:
    description: Desired download state or action.
    type: str
    choices:
    - present
    - absent
    - uploaded
    - abort_upload
    - signed_url
    - fetched
    - detect_filename
    - query
    default: present
    required: false
  download_id:
    description: Numeric download ID (or upload staging ID for C(abort_upload)).
    type: str
    aliases:
    - id
    required: false
  ids:
    description: List of download IDs for bulk deletion.
    type: list
    elements: int
    required: false
  uuid:
    description: Download UUID.
    type: str
    required: false
  url:
    description: HTTP(S) URL or magnet URI to download.
    type: str
    required: false
  name:
    description: Filename or download name.
    type: str
    aliases:
    - filename
    required: false
  download_type:
    description: Usage type (C(uncategorized), C(cloud-init), C(base-rootfs)).
    type: str
    default: uncategorized
    required: false
  storage_pool:
    description: Target ZFS storage pool.
    type: str
    aliases:
    - pool
    required: false
  automatic_extraction:
    description: Automatically extract compressed archives.
    type: bool
    default: true
    required: false
  automatic_raw_conversion:
    description: Automatically convert disk images to RAW.
    type: bool
    default: false
    required: false
  ignore_tls:
    description: Ignore TLS certificate errors on the source URL.
    type: bool
    default: false
    required: false
  src:
    description: Local file path to upload when C(state=uploaded).
    type: path
    required: false
  dest:
    description: Local destination file path when C(state=fetched).
    type: path
    required: false
  params:
    description: Optional query parameters (e.g. signed capability parameters when C(state=fetched)).
    type: dict
    required: false
  data:
    description: Additional raw request fields.
    type: dict
    required: false
version_added: 1.0.0
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
- name: Download FreeBSD 14.2 cloud-init image
  sylve.cloud.sylve_download:
    url: https://download.freebsd.org/releases/VM-IMAGES/14.2-RELEASE/amd64/Latest/FreeBSD-14.2-RELEASE-amd64-BASIC-CLOUDINIT.ufs.raw.xz
    download_type: cloud-init
    storage_pool: zroot
    state: present

- name: Manage Sylve ISO and disk-image downloads, local uploads, and signed URLs on a specific node using a named context
  sylve.cloud.sylve_download:
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
download:
  description: Download metadata or action result.
  returned: always
  type: raw
  sample: '{"uuid": "9f2c...", "name": "FreeBSD-14.2.iso", "status": "completed"}'
"""

from pathlib import Path
from ansible_collections.sylve.cloud.plugins.module_utils.sylve import SylveModule


class SylveDownloadModule(SylveModule):
    argument_spec = {
        "state": {
            "type": "str",
            "choices": [
                "present",
                "absent",
                "uploaded",
                "abort_upload",
                "signed_url",
                "fetched",
                "detect_filename",
                "query",
            ],
            "default": "present",
        },
        "download_id": {"type": "str", "aliases": ["id"]},
        "ids": {"type": "list", "elements": "int"},
        "uuid": {"type": "str"},
        "url": {"type": "str"},
        "name": {"type": "str", "aliases": ["filename"]},
        "download_type": {"type": "str", "default": "uncategorized"},
        "storage_pool": {"type": "str", "aliases": ["pool"]},
        "automatic_extraction": {"type": "bool", "default": True},
        "automatic_raw_conversion": {"type": "bool", "default": False},
        "ignore_tls": {"type": "bool", "default": False},
        "src": {"type": "path"},
        "dest": {"type": "path"},
        "params": {"type": "dict"},
        "data": {"type": "dict"},
    }

    def run(self) -> None:
        state = self.params["state"]
        did = self.params.get("download_id")
        uuid = self.params.get("uuid")
        name = self.params.get("name")
        url = self.params.get("url")
        payload: dict = dict(self.params.get("data") or {})

        if state == "query":
            info = {
                "downloads": self.client.get("/utilities/downloads", node=self.node),
                "utype": self.client.get("/utilities/downloads/utype", node=self.node),
                "paths": self.client.get("/utilities/downloads/paths", node=self.node),
                "storage": self.client.get("/utilities/downloads/storage", node=self.node),
            }
            self.exit_json(changed=False, download=info)
            return

        if state == "detect_filename":
            res = self.client.post(
                "/utilities/downloads/detect-filename",
                json_body={"url": url},
                node=self.node,
            )
            self.exit_json(changed=False, download=res)
            return

        if state == "signed_url":
            res = self.client.post(
                "/utilities/downloads/signed-url",
                json_body={"parentUUID": uuid, "name": name},
                node=self.node,
            )
            self.exit_json(changed=False, download=res)
            return

        if state == "fetched":
            if not uuid or not self.params.get("dest"):
                self.fail_json(msg="Both 'uuid' and 'dest' are required when state=fetched.")
            dl_path = (
                f"/utilities/downloads/{uuid}/{name}"
                if name
                else f"/utilities/downloads/{uuid}"
            )
            if not self.check_mode:
                out_file = self.client.download_file(
                    dl_path,
                    self.params["dest"],
                    params=self.params.get("params"),
                    node=self.node,
                )
            else:
                out_file = Path(self.params["dest"])
            self.exit_json(changed=True, download={"dest": str(out_file)})
            return

        if state == "abort_upload":
            if not did:
                self.fail_json(msg="'download_id' (upload ID) is required for abort_upload.")
            if not self.check_mode:
                self.client.delete(f"/utilities/downloader-uploads/{did}", node=self.node)
            self.exit_json(changed=True, download={"id": did})
            return

        if state == "uploaded":
            src = self.params.get("src")
            if not src:
                self.fail_json(msg="'src' is required when state=uploaded.")
            if self.check_mode:
                self.exit_json(changed=True, download={"src": src})
                return
            qparams = (
                {"storagePool": self.params["storage_pool"]}
                if self.params.get("storage_pool")
                else None
            )
            receipt = self.client.post(
                "/utilities/downloader-uploads",
                params=qparams,
                upload_file=src,
                node=self.node,
            )
            upload_id = (
                receipt.get("uploadId") if isinstance(receipt, dict) else str(receipt or "")
            )
            result = self.client.post(
                f"/utilities/downloader-uploads/{upload_id}/complete",
                json_body={
                    "downloadType": self.params["download_type"],
                    "automaticExtraction": self.params["automatic_extraction"],
                    "automaticRawConversion": self.params["automatic_raw_conversion"],
                },
                node=self.node,
            )
            self.exit_json(changed=True, download=result)
            return

        if state == "absent" and self.params.get("ids"):
            body = {"ids": self.params["ids"]}
            if not self.check_mode:
                self.client.post(
                    "/utilities/downloads/bulk-delete", json_body=body, node=self.node
                )
            self.exit_json(changed=True, download=body)
            return

        downloads = self.client.get("/utilities/downloads", node=self.node) or []
        existing = None
        for d in downloads if isinstance(downloads, list) else []:
            if not isinstance(d, dict):
                continue
            if did and str(d.get("id")) == str(did):
                existing = d
                break
            if uuid and str(d.get("uuid") or "").lower() == uuid.lower():
                existing = d
                did = str(d.get("id"))
                break
            if name and str(d.get("name") or "").lower() == name.lower():
                existing = d
                did = str(d.get("id"))
                break
            if url and str(d.get("url") or "") == url:
                existing = d
                did = str(d.get("id"))
                break

        if state == "absent":
            if not did:
                self.exit_json(changed=False, download={})
                return
            if not self.check_mode:
                self.client.delete(f"/utilities/downloads/{did}", node=self.node)
            self.exit_json(changed=True, download=existing or {"id": did})
            return

        if existing and did:
            if not payload:
                self.exit_json(changed=False, download=existing)
                return
            if not self.check_mode:
                resp = self.client.patch(
                    f"/utilities/downloads/{did}", json_body=payload, node=self.node
                )
            else:
                resp = payload
            self.exit_json(changed=True, download=resp or payload)
            return

        body = {
            "url": url,
            "downloadType": self.params["download_type"],
            "automaticExtraction": self.params["automatic_extraction"],
            "automaticRawConversion": self.params["automatic_raw_conversion"],
            "ignoreTLS": self.params["ignore_tls"],
        }
        if name:
            body["filename"] = name
        if self.params.get("storage_pool"):
            body["storagePool"] = self.params["storage_pool"]
        body.update(payload)

        if not self.check_mode:
            resp = self.client.post("/utilities/downloads", json_body=body, node=self.node)
        else:
            resp = body
        self.exit_json(changed=True, download=resp or body)


def main() -> None:
    SylveDownloadModule()()


if __name__ == "__main__":
    main()
