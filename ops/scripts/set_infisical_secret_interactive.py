#!/usr/bin/env python3

import getpass
import os
import subprocess
import sys

from fetch_infisical_cloud import load_operator_env, normalize_api_url, require_env


def login(api_url: str) -> str:
    command = [
        "infisical",
        "login",
        "--method=universal-auth",
        f"--client-id={require_env('INFISICAL_UNIVERSAL_AUTH_CLIENT_ID')}",
        f"--client-secret={require_env('INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET')}",
        "--plain",
        "--silent",
        f"--domain={api_url}",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    for token in completed.stdout.split():
        if token.startswith("eyJ"):
            return token
    raise SystemExit("infisical login succeeded but no access token was returned")


def main() -> int:
    load_operator_env()
    api_url = normalize_api_url(os.environ.get("INFISICAL_API_URL", "https://app.infisical.com"))
    default_path = (
        os.environ.get("INFISICAL_RUNTIME_SECRET_PATH", "").strip()
        or "/runtime"
    )

    secret_name = input("Secret name: ").strip()
    if not secret_name:
        raise SystemExit("secret name is required")

    secret_value = getpass.getpass("Secret value: ").strip()
    if not secret_value:
        raise SystemExit("secret value is required")

    raw_path = input(f"Secret path [{default_path}]: ").strip()
    secret_path = raw_path or default_path

    token = login(api_url)
    command = [
        "infisical",
        "secrets",
        "set",
        f"{secret_name}={secret_value}",
        f"--path={secret_path}",
        f"--projectId={require_env('INFISICAL_PROJECT_ID')}",
        f"--env={require_env('INFISICAL_ENV_SLUG')}",
        f"--token={token}",
        f"--domain={api_url}",
        "--silent",
    ]
    subprocess.run(command, check=True)
    print(f"Stored {secret_name} in {secret_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
