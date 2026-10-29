# sylve_download

_Manage Sylve ISO and disk-image downloads, local uploads, and signed URLs_

Start URL/magnet downloads, upload local ISO/image files to downloader storage, update metadata, mint signed download URLs, download completed files locally, query storage paths, or delete downloads.

- **Collection:** `sylve.cloud` (FQCN `sylve.cloud.sylve_download`)
- **Added in:** `sylve.cloud 0.3.1`
- **Author:** Sylve Contributors (@mhahl)
- **Requirements:** `python >= 3.10`, `PyYAML`
- **Check mode:** supported (`full`)

## Options

| Option | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `state` | `str` | no | `present` | `present`, `absent`, `uploaded`, `abort_upload`, `signed_url`, `fetched`, `detect_filename`, `query` | Desired download state or action. |
| `download_id` (aliases: `id`) | `str` | no | — | — | Numeric download ID (or upload staging ID for C(abort_upload)). |
| `ids` | `list` | no | — | — | List of download IDs for bulk deletion. |
| `uuid` | `str` | no | — | — | Download UUID. |
| `url` | `str` | no | — | — | HTTP(S) URL or magnet URI to download. |
| `name` (aliases: `filename`) | `str` | no | — | — | Filename or download name. |
| `download_type` | `str` | no | `uncategorized` | — | Usage type (C(uncategorized), C(cloud-init), C(base-rootfs)). |
| `storage_pool` (aliases: `pool`) | `str` | no | — | — | Target ZFS storage pool. |
| `automatic_extraction` | `bool` | no | `true` | — | Automatically extract compressed archives. |
| `automatic_raw_conversion` | `bool` | no | `false` | — | Automatically convert disk images to RAW. |
| `ignore_tls` | `bool` | no | `false` | — | Ignore TLS certificate errors on the source URL. |
| `src` | `path` | no | — | — | Local file path to upload when C(state=uploaded). |
| `dest` | `path` | no | — | — | Local destination file path when C(state=fetched). |
| `params` | `dict` | no | — | — | Optional query parameters (e.g. signed capability parameters when C(state=fetched)). |
| `data` | `dict` | no | — | — | Additional raw request fields. |
| `timeout` | `float` | no | `600.0` | — | HTTP request timeout in seconds. Raised for this module because large ISO uploads and downloads take a while. |

All modules also accept the shared [sylve connection options](index.md#authentication) (`config_path`, `context`, `auth`, `server`, `token`, `username`, `password`, `auth_type`, `node`, `validate_certs`, `ca_cert`, `timeout`, `wait`, `poll_interval`).

## Notes

- Supports C(check_mode).
- C(state=present) is idempotent: the module only issues write requests when the desired state differs from the live object.
- Shares C(~/.config/sylve/config.yaml) contexts and C(SYLVE_*) environment variables with the C(sylve) CLI (see M(sylve.cloud.sylve_api)).

## Examples

```yaml
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
```

## Return values

| Key | Type | Returned | Description | Sample |
| --- | --- | --- | --- | --- |
| `changed` | `bool` | always | Whether the module made changes on the Sylve cluster. | `True` |
| `download` | `raw` | always | Download metadata or action result. | `{"uuid": "9f2c...", "name": "FreeBSD-14.2.iso", "status": "completed"}` |

## See also

- Module `sylve.cloud.sylve_api` — Execute any Sylve REST API endpoint directly.
- [sylve.cloud collection README](https://github.com/mhahl/sylve-ansible) — Authentication, configuration, and inventory plugin usage.

_Auto-generated from `plugins/modules/sylve_download.py` — edit the module, not this file._
