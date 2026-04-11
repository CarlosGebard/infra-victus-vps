#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from fetch_infisical_cloud import (
    DEFAULT_INFISICAL_API_URL,
    load_operator_env,
    login,
    normalize_api_url,
    fetch_secrets,
    resolve_secret_path,
)
from bootstrap_via_infisical import (
    DEFAULT_BOOTSTRAP_SSH_USER,
    PRODUCTION_GROUP_VARS_FILE,
    normalize_secret_value,
    require_keys,
    build_inventory,
    run_ssh_preflight,
    validate_ssh_material,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ANSIBLE_DIR = REPO_ROOT / "ansible"
REQUIRED_CONNECTION_KEYS = (
    "PROD_HOST",
    "PROD_SSH_PRIVATE_KEY",
    "PROD_SSH_KNOWN_HOSTS",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch SSH material from Infisical and run the bootstrap validation playbook.")
    parser.add_argument("--connection-path", default="", help="Override the Infisical SSH connection secret path. Defaults to INFISICAL_CONNECTION_SECRET_PATH or '/connection'.")
    parser.add_argument("--ssh-user", default=DEFAULT_BOOTSTRAP_SSH_USER, help="SSH user for bootstrap validation. Defaults to root.")
    parser.add_argument("--playbook", default="runtime/playbooks/validate-bootstrap.yml", help="Playbook path relative to the ansible/ directory.")
    parser.add_argument("--verbosity", default="", choices=("", "-v", "-vv", "-vvv", "-vvvv"), help="Optional Ansible verbosity flag.")
    args = parser.parse_args()

    if shutil.which("ansible-playbook") is None:
        raise SystemExit("ansible-playbook is required but was not found in PATH")
    if shutil.which("ssh") is None:
        raise SystemExit("ssh is required but was not found in PATH")

    load_operator_env()
    api_url = normalize_api_url(os.environ.get("INFISICAL_API_URL", DEFAULT_INFISICAL_API_URL))
    print("Loading machine identity token from Infisical...")
    print(
        "Using Infisical config: "
        f"api_url={api_url} "
        f"project_id={os.environ.get('INFISICAL_PROJECT_ID', '')} "
        f"env_slug={os.environ.get('INFISICAL_ENV_SLUG', '')}"
    )
    access_token = login(api_url)

    connection_path = args.connection_path.strip() or resolve_secret_path(
        ("INFISICAL_CONNECTION_SECRET_PATH",),
        "/connection",
    )

    print(f"Fetching SSH connection secrets from {connection_path}...")
    connection_secrets = fetch_secrets(api_url, access_token, connection_path)
    selected_connection = require_keys(connection_secrets, REQUIRED_CONNECTION_KEYS, f"path {connection_path}")

    prod_host = normalize_secret_value(selected_connection["PROD_HOST"])
    prod_user = normalize_secret_value(args.ssh_user)
    prod_private_key = normalize_secret_value(selected_connection["PROD_SSH_PRIVATE_KEY"])
    prod_known_hosts = normalize_secret_value(selected_connection["PROD_SSH_KNOWN_HOSTS"])

    validate_ssh_material(prod_host, prod_user, prod_private_key, prod_known_hosts)
    prod_private_key += "\n"
    prod_known_hosts += "\n"

    with tempfile.TemporaryDirectory(prefix="verify-bootstrap-infisical-") as tempdir:
        temp_path = Path(tempdir)
        private_key_path = temp_path / "id_ed25519"
        known_hosts_path = temp_path / "known_hosts"
        inventory_path = temp_path / "inventory.yml"

        private_key_path.write_text(prod_private_key, encoding="utf-8")
        known_hosts_path.write_text(prod_known_hosts, encoding="utf-8")
        inventory_path.write_text(build_inventory(prod_host, prod_user), encoding="utf-8")

        os.chmod(private_key_path, 0o600)
        os.chmod(known_hosts_path, 0o644)
        os.chmod(inventory_path, 0o600)

        print(f"Running SSH preflight against {prod_user}@{prod_host}...")
        run_ssh_preflight(prod_host, prod_user, private_key_path, known_hosts_path)
        print("SSH preflight ok. Running bootstrap validation playbook...")

        env = os.environ.copy()
        env["ANSIBLE_LOCAL_TEMP"] = env.get("ANSIBLE_LOCAL_TEMP", "/tmp/.ansible-local")
        env["ANSIBLE_HOST_KEY_CHECKING"] = "True"
        env["ANSIBLE_SSH_ARGS"] = " ".join(
            (
                "-o IdentitiesOnly=yes",
                "-o StrictHostKeyChecking=yes",
                f"-o UserKnownHostsFile={known_hosts_path}",
            )
        )

        command = [
            "ansible-playbook",
            "-i",
            str(inventory_path),
            "--extra-vars",
            f"@{PRODUCTION_GROUP_VARS_FILE}",
            "--private-key",
            str(private_key_path),
            args.playbook,
        ]
        if args.verbosity:
            command.append(args.verbosity)

        completed = subprocess.run(command, cwd=ANSIBLE_DIR, env=env)
        return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
