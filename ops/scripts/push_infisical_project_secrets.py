#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fetch_infisical_cloud import load_operator_env, normalize_api_url, require_env


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FILE = REPO_ROOT / ".secrets" / "infisical" / "project.env"


def run_cli(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


def parse_secret_file(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    scalar_secrets: dict[str, str] = {}
    file_backed_secrets: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if "=" not in line:
            index += 1
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            index += 1
            continue

        if value == "" and index + 1 < len(lines) and lines[index + 1].startswith("-----BEGIN "):
            block_lines = []
            index += 1
            while index < len(lines):
                block_lines.append(lines[index])
                if lines[index].startswith("-----END "):
                    break
                index += 1
            file_backed_secrets[key] = "\n".join(block_lines) + "\n"
            index += 1
            continue

        scalar_secrets[key] = value
        index += 1

    return scalar_secrets, file_backed_secrets


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
    parser = argparse.ArgumentParser(description="Upload one local dotenv file into the configured Infisical project.")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="Path to a dotenv file with the project secrets")
    parser.add_argument("--path", default="", help="Optional Infisical path override. Defaults to INFISICAL_RUNTIME_SECRET_PATH or '/runtime'.")
    args = parser.parse_args()

    load_operator_env()
    api_url = normalize_api_url(os.environ.get("INFISICAL_API_URL", "https://app.infisical.com"))
    token = login(api_url)

    source_file = Path(args.file)
    if not source_file.exists():
        raise SystemExit(f"secret file not found: {source_file}")
    scalar_secrets, file_backed_secrets = parse_secret_file(source_file)

    secret_path = (
        args.path.strip()
        or os.environ.get("INFISICAL_RUNTIME_SECRET_PATH", "").strip()
        or "/runtime"
    )

    if scalar_secrets:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            for key, value in scalar_secrets.items():
                handle.write(f"{key}={value}\n")
            scalar_file = handle.name
        try:
            command = [
                "infisical",
                "secrets",
                "set",
                f"--file={scalar_file}",
                f"--path={secret_path}",
                f"--projectId={require_env('INFISICAL_PROJECT_ID')}",
                f"--env={require_env('INFISICAL_ENV_SLUG')}",
                f"--token={token}",
                f"--domain={api_url}",
                "--silent",
            ]
            run_cli(command)
        finally:
            os.unlink(scalar_file)

    for key, value in file_backed_secrets.items():
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(value)
            secret_file = handle.name
        try:
            command = [
                "infisical",
                "secrets",
                "set",
                f"{key}=@{secret_file}",
                f"--path={secret_path}",
                f"--projectId={require_env('INFISICAL_PROJECT_ID')}",
                f"--env={require_env('INFISICAL_ENV_SLUG')}",
                f"--token={token}",
                f"--domain={api_url}",
                "--silent",
            ]
            run_cli(command)
        finally:
            os.unlink(secret_file)

    print(f"Uploaded secrets from {source_file} to {secret_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
