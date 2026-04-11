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


REPO_ROOT = Path(__file__).resolve().parents[2]
ANSIBLE_DIR = REPO_ROOT / "ansible"
PRODUCTION_GROUP_VARS_FILE = ANSIBLE_DIR / "inventories" / "production" / "group_vars" / "all.yml"
REQUIRED_CONNECTION_KEYS = (
    "PROD_HOST",
    "PROD_SSH_PRIVATE_KEY",
    "PROD_SSH_KNOWN_HOSTS",
)
REQUIRED_BOOTSTRAP_KEYS = (
    "TAILSCALE_AUTH_KEY",
)
DEFAULT_BOOTSTRAP_SSH_USER = "root"


def normalize_secret_value(value: str) -> str:
    return value.replace("\\n", "\n").strip()


def validate_ssh_material(host: str, user: str, private_key: str, known_hosts: str) -> None:
    if private_key.startswith("@/"):
        raise SystemExit(
            "PROD_SSH_PRIVATE_KEY in Infisical looks like a file reference, not a real key. "
            "Store the full private key contents, not a local @/tmp/... path."
        )
    if "-----BEGIN " not in private_key or "PRIVATE KEY-----" not in private_key:
        raise SystemExit(
            f"PROD_SSH_PRIVATE_KEY for {user}@{host} is not a valid PEM/OpenSSH private key payload."
        )
    if not known_hosts.strip():
        raise SystemExit("PROD_SSH_KNOWN_HOSTS is empty.")


def require_keys(secrets: dict[str, str], required_keys: tuple[str, ...], source_name: str) -> dict[str, str]:
    missing = [key for key in required_keys if not secrets.get(key, "").strip()]
    if missing:
        raise SystemExit(f"missing required secrets in {source_name}: {', '.join(missing)}")
    return {key: secrets[key] for key in required_keys}


def build_inventory(host: str, user: str) -> str:
    return "\n".join(
        (
            "all:",
            "  children:",
            "    vps:",
            "      hosts:",
            "        production:",
            f"          ansible_host: {host}",
            f"          ansible_user: {user}",
            "          ansible_become: true",
            "",
        )
    )


def run_ssh_preflight(host: str, user: str, private_key_path: Path, known_hosts_path: Path) -> None:
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts_path}",
        "-i",
        str(private_key_path),
        f"{user}@{host}",
        "echo ssh-ok",
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        output = ((completed.stdout or "") + (completed.stderr or "")).strip()
        raise SystemExit(f"SSH preflight failed for {user}@{host}: {output}")
    if "ssh-ok" not in (completed.stdout or ""):
        raise SystemExit(f"SSH preflight reached {user}@{host} but did not return the expected marker")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch bootstrap SSH material from Infisical and run the Ansible bootstrap playbook.")
    parser.add_argument("--bootstrap-path", default="", help="Override the Infisical bootstrap secret path. Defaults to INFISICAL_BOOTSTRAP_SECRET_PATH or '/bootstrap'.")
    parser.add_argument("--connection-path", default="", help="Override the Infisical SSH connection secret path. Defaults to INFISICAL_CONNECTION_SECRET_PATH or '/connection'.")
    parser.add_argument("--ssh-user", default=DEFAULT_BOOTSTRAP_SSH_USER, help="SSH user for bootstrap. Defaults to root and does not come from Infisical.")
    parser.add_argument("--playbook", default="bootstrap/playbooks/bootstrap.yml", help="Playbook path relative to the ansible/ directory.")
    parser.add_argument("--start-at-task", default="", help="Optional Ansible task name to resume from.")
    parser.add_argument("--verbosity", default="", choices=("", "-v", "-vv", "-vvv", "-vvvv"), help="Optional Ansible verbosity flag.")
    parser.add_argument("--check", action="store_true", help="Run Ansible in check mode.")
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

    bootstrap_path = args.bootstrap_path.strip() or resolve_secret_path(("INFISICAL_BOOTSTRAP_SECRET_PATH",), "/bootstrap")
    connection_path = args.connection_path.strip() or resolve_secret_path(
        ("INFISICAL_CONNECTION_SECRET_PATH",),
        "/connection",
    )

    print(f"Fetching bootstrap secrets from {bootstrap_path}...")
    bootstrap_secrets = fetch_secrets(api_url, access_token, bootstrap_path)
    print(f"Fetching SSH connection secrets from {connection_path}...")
    connection_secrets = fetch_secrets(api_url, access_token, connection_path)

    selected_bootstrap = require_keys(bootstrap_secrets, REQUIRED_BOOTSTRAP_KEYS, f"path {bootstrap_path}")
    selected_connection = require_keys(connection_secrets, REQUIRED_CONNECTION_KEYS, f"path {connection_path}")

    prod_host = normalize_secret_value(selected_connection["PROD_HOST"])
    prod_user = normalize_secret_value(args.ssh_user)
    prod_private_key = normalize_secret_value(selected_connection["PROD_SSH_PRIVATE_KEY"])
    prod_known_hosts = normalize_secret_value(selected_connection["PROD_SSH_KNOWN_HOSTS"])
    tailscale_auth_key = normalize_secret_value(selected_bootstrap["TAILSCALE_AUTH_KEY"])

    validate_ssh_material(prod_host, prod_user, prod_private_key, prod_known_hosts)
    prod_private_key += "\n"
    prod_known_hosts += "\n"

    with tempfile.TemporaryDirectory(prefix="bootstrap-infisical-") as tempdir:
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
        print("SSH preflight ok. Running ansible-playbook...")

        env = os.environ.copy()
        env["TAILSCALE_AUTH_KEY"] = tailscale_auth_key
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
        if args.start_at_task:
            command.extend(["--start-at-task", args.start_at_task])
        if args.check:
            command.append("--check")
        if args.verbosity:
            command.append(args.verbosity)

        completed = subprocess.run(command, cwd=ANSIBLE_DIR, env=env)
        return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
