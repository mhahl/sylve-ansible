# -*- coding: utf-8 -*-
# BSD-2-Clause

from __future__ import annotations


class ModuleDocFragment:
    DOCUMENTATION = r"""
options:
  config_path:
    description:
      - Path to the Sylve CLI configuration file (C(~/.config/sylve/config.yaml)).
      - Defaults to C($SYLVE_CONFIG), C($XDG_CONFIG_HOME/sylve/config.yaml), or C(~/.config/sylve/config.yaml).
    type: path
  context:
    description:
      - Named context from the Sylve configuration file to use (or C($SYLVE_CONTEXT)).
    type: str
    aliases: [cloud]
  auth:
    description:
      - Optional dictionary containing authentication and connection overrides (similar to C(openstack.cloud)).
    type: dict
    suboptions:
      server:
        description: Sylve server URL or hostname.
        type: str
      token:
        description: Bearer JWT token.
        type: str
      username:
        description: Username for login if no valid token is present.
        type: str
      password:
        description: Password for login if no valid token is present.
        type: str
      auth_type:
        description: Authentication provider (C(sylve) or C(pam)).
        type: str
        choices: [sylve, pam]
        default: sylve
      save_token:
        description: Persist newly acquired login tokens back to the Sylve config file.
        type: bool
        default: false
  server:
    description:
      - Override Sylve server URL (or C($SYLVE_SERVER)).
    type: str
    aliases: [api_url]
  token:
    description:
      - Override Bearer JWT token (or C($SYLVE_TOKEN)).
    type: str
  username:
    description:
      - Username to authenticate via C(POST /api/auth/login) when no valid token is available (or C($SYLVE_USERNAME)).
    type: str
  password:
    description:
      - Password to authenticate via C(POST /api/auth/login) when no valid token is available (or C($SYLVE_PASSWORD)).
    type: str
  auth_type:
    description:
      - Authentication backend used when logging in with username and password (C(sylve) or C(pam)).
    type: str
    choices: [sylve, pam]
    default: sylve
  save_token:
    description:
      - Whether to atomically persist a newly minted login token into C(config.yaml).
    type: bool
    default: false
  node:
    description:
      - Target cluster node hostname or UUID (sets C(X-Current-Hostname), or C($SYLVE_NODE)).
    type: str
  validate_certs:
    description:
      - Verify TLS certificates when talking to the Sylve server (or C($SYLVE_INSECURE)).
    type: bool
    aliases: [verify]
  ca_cert:
    description:
      - Path to a custom CA certificate bundle.
    type: path
  timeout:
    description:
      - HTTP request and task polling timeout in seconds.
    type: float
    default: 60.0
  wait:
    description:
      - Wait for asynchronous lifecycle, migration, replication, or backup tasks to reach a terminal state.
    type: bool
    default: true
  poll_interval:
    description:
      - Seconds between task polling checks when C(wait=true).
    type: float
    default: 1.5
notes:
  - Shares C(~/.config/sylve/config.yaml) and environment variables (C(SYLVE_CONFIG), C(SYLVE_CONTEXT),
    C(SYLVE_SERVER), C(SYLVE_TOKEN), C(SYLVE_NODE), C(SYLVE_INSECURE)) with C(sylve-cli).
"""
