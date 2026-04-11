#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from fetch_infisical_cloud import load_operator_env, normalize_api_url, require_env


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SECRET_FILES = {
    "bootstrap": REPO_ROOT / ".secrets" / "infisical" / "bootstrap.env",
    "connection": REPO_ROOT / ".secrets" / "infisical" / "connection.env",
    "runtime": REPO_ROOT / ".secrets" / "infisical" / "runtime.env",
}
DEFAULT_SECRET_PATHS = {
    "bootstrap": "/bootstrap",
    "connection": "/connection",
    "runtime": "/runtime",
}


def run_cli(command: list[str], *, tolerate_failure: bool = False) -> int:
    completed = subprocess.run(command, text=True)
    if completed.returncode != 0 and not tolerate_failure:
        raise SystemExit(completed.returncode)
    return completed.returncode


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
    output = subprocess.check_output(command, text=True)
    token_match = re.search(r"eyJ[0-9A-Za-z._-]+", output)
    if not token_match:
        raise SystemExit("infisical login succeeded but no access token was returned")
    return token_match.group(0)


def ensure_folder_path(path: str, api_url: str, token: str) -> None:
    normalized = path.strip()
    if normalized in ("", "/"):
        return
    parts = [part for part in normalized.split("/") if part]
    current_path = "/"
    for part in parts:
        command = [
            "infisical",
            "secrets",
            "folders",
            "create",
            f"--name={part}",
            f"--path={current_path}",
            f"--projectId={require_env('INFISICAL_PROJECT_ID')}",
            f"--token={token}",
            f"--domain={api_url}",
            f"--env={require_env('INFISICAL_ENV_SLUG')}",
            "--silent",
        ]
        run_cli(command, tolerate_failure=True)
        current_path = f"{current_path.rstrip('/')}/{part}"


def seed_profile(profile: str, source_file: Path, api_url: str, token: str) -> None:
    if not source_file.exists():
        raise SystemExit(f"secret file not found: {source_file}")
    path_env_names = {
        "bootstrap": ("INFISICAL_BOOTSTRAP_SECRET_PATH",),
        "connection": ("INFISICAL_CONNECTION_SECRET_PATH",),
        "runtime": ("INFISICAL_RUNTIME_SECRET_PATH",),
    }
    secret_path = DEFAULT_SECRET_PATHS[profile]
    for env_name in path_env_names[profile]:
        candidate = os.environ.get(env_name, "").strip()
        if candidate:
            secret_path = candidate
            break
    ensure_folder_path(secret_path, api_url, token)
    command = [
        "infisical",
        "secrets",
        "set",
        f"--file={source_file}",
        f"--path={secret_path}",
        f"--projectId={require_env('INFISICAL_PROJECT_ID')}",
        f"--token={token}",
        f"--domain={api_url}",
        f"--env={require_env('INFISICAL_ENV_SLUG')}",
        "--silent",
    ]
    run_cli(command)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Infisical Cloud folders from local dotenv files.")
    parser.add_argument("profile", choices=("bootstrap", "connection", "runtime", "all"))
    parser.add_argument("--bootstrap-file", default=str(DEFAULT_SECRET_FILES["bootstrap"]))
    parser.add_argument("--connection-file", default=str(DEFAULT_SECRET_FILES["connection"]))
    parser.add_argument("--runtime-file", default=str(DEFAULT_SECRET_FILES["runtime"]))
    args = parser.parse_args()

    load_operator_env()
    api_url = normalize_api_url(os.environ.get("INFISICAL_API_URL", "https://app.infisical.com"))
    token = login(api_url)

    if args.profile in ("bootstrap", "all"):
        seed_profile("bootstrap", Path(args.bootstrap_file), api_url, token)
    if args.profile in ("connection", "all"):
        seed_profile("connection", Path(args.connection_file), api_url, token)
    if args.profile in ("runtime", "all"):
        seed_profile("runtime", Path(args.runtime_file), api_url, token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
