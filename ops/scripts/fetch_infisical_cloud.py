#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
from typing import Dict
from urllib import parse

DEFAULT_INFISICAL_API_URL = "https://app.infisical.com"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DEFAULT_OPERATOR_ENV_PATHS = (
    os.path.join(REPO_ROOT, ".secrets", "infisical", "bootstrap.env"),
    os.path.expanduser("~/.config/infisical/bootstrap.env"),
)
ENV_ALIASES = {
    "INFISICAL_UNIVERSAL_AUTH_CLIENT_ID": ("INFISICAL_UNIVERSAL_AUTH_CLIENT_ID",),
    "INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET": ("INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET",),
    "INFISICAL_API_URL": ("INFISICAL_API_URL",),
    "INFISICAL_PROJECT_ID": ("INFISICAL_PROJECT_ID",),
    "INFISICAL_ENV_SLUG": ("INFISICAL_ENV_SLUG",),
    "INFISICAL_ORGANIZATION_SLUG": ("INFISICAL_ORGANIZATION_SLUG",),
}


PROFILE_CONFIG = {
    "bootstrap-shell": {
        "path_envs": ("INFISICAL_BOOTSTRAP_SECRET_PATH",),
        "default_path": "/bootstrap",
        "required": (
            "TAILSCALE_AUTH_KEY",
        ),
        "optional": (),
    },
    "connection-ssh": {
        "path_envs": ("INFISICAL_CONNECTION_SECRET_PATH",),
        "default_path": "/connection",
        "required": (
            "PROD_HOST",
            "PROD_SSH_USER",
            "PROD_SSH_PRIVATE_KEY",
            "PROD_SSH_KNOWN_HOSTS",
        ),
        "optional": (),
    },
    "runtime-env": {
        "path_envs": ("INFISICAL_RUNTIME_SECRET_PATH",),
        "default_path": "/runtime",
        "required": (
            "GRAFANA_ADMIN_PASSWORD",
            "COUCHDB_PASSWORD",
        ),
        "optional": (
            "COUCHDB_USER",
        ),
    },
    "seaweed-s3": {
        "path_envs": ("INFISICAL_RUNTIME_SECRET_PATH",),
        "default_path": "/runtime",
        "required": (
            "SEAWEED_S3_ACCESS_KEY",
            "SEAWEED_S3_SECRET_KEY",
        ),
        "optional": (),
    },
}


def load_env_file(path: str, *, override_existing: bool = False) -> None:
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue
            name, raw_value = line.split("=", 1)
            name = name.strip()
            raw_value = raw_value.strip()
            if not name:
                continue
            if not override_existing and name in os.environ:
                continue
            if raw_value:
                value = raw_value
                if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
                    value = value[1:-1]
            else:
                value = ""
            os.environ[name] = value


def load_operator_env() -> str:
    explicit_path = os.environ.get("INFISICAL_OPERATOR_ENV_FILE", "").strip()
    if explicit_path:
        expanded_path = os.path.expanduser(explicit_path)
        if not os.path.exists(expanded_path):
            raise SystemExit(f"operator env file not found: {expanded_path}")
        load_env_file(expanded_path, override_existing=True)
        return expanded_path
    for candidate in DEFAULT_OPERATOR_ENV_PATHS:
        if os.path.exists(candidate):
            load_env_file(candidate, override_existing=True)
            return candidate
    return ""


def require_env(name: str) -> str:
    for candidate in ENV_ALIASES.get(name, (name,)):
        value = os.environ.get(candidate, "").strip()
        if value:
            return value
    raise SystemExit(f"missing required environment variable: {name}")


def normalize_api_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    if normalized.endswith("/api"):
        normalized = normalized[: -len("/api")]
    return normalized


def resolve_secret_path(path_envs: tuple[str, ...], default_path: str) -> str:
    for env_name in path_envs:
        candidate = os.environ.get(env_name, "").strip()
        if candidate:
            return candidate
    return default_path


def http_json(method: str, url: str, *, headers: dict[str, str] | None = None, payload: dict | None = None) -> dict:
    command = ["curl", "--silent", "--show-error", "--fail", "--request", method, "--url", url]
    for key, value in (headers or {}).items():
        command.extend(["--header", f"{key}: {value}"])
    if payload is not None:
        command.extend(["--header", "Content-Type: application/json", "--data", json.dumps(payload)])
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise SystemExit("curl is required but was not found in PATH") from exc
    except subprocess.CalledProcessError as exc:
        output = ((exc.stdout or "") + (exc.stderr or "")).strip()
        raise SystemExit(f"Infisical API {method} {url} failed: {output[:500]}") from exc

    try:
        return json.loads(completed.stdout or "")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Infisical API {method} {url} returned non-JSON output") from exc


def login(api_url: str) -> str:
    payload = {
        "clientId": require_env("INFISICAL_UNIVERSAL_AUTH_CLIENT_ID"),
        "clientSecret": require_env("INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET"),
    }
    organization_slug = os.environ.get("INFISICAL_ORGANIZATION_SLUG", "").strip()
    if organization_slug:
        payload["organizationSlug"] = organization_slug
    response = http_json("POST", f"{api_url}/api/v1/auth/universal-auth/login", payload=payload)
    access_token = str(response.get("accessToken", "")).strip()
    if not access_token:
        raise SystemExit("Infisical login succeeded but no access token was returned")
    return access_token


def fetch_secrets(api_url: str, access_token: str, secret_path: str) -> Dict[str, str]:
    query = parse.urlencode(
        {
            "projectId": require_env("INFISICAL_PROJECT_ID"),
            "environment": require_env("INFISICAL_ENV_SLUG"),
            "secretPath": secret_path,
            "viewSecretValue": "true",
            "expandSecretReferences": "true",
            "includeImports": "true",
            "recursive": "false",
        }
    )
    response = http_json(
        "GET",
        f"{api_url}/api/v4/secrets?{query}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    secrets = {}
    for item in response.get("secrets", []):
        key = str(item.get("secretKey", "")).strip()
        if not key:
            continue
        value = item.get("secretValue")
        if value is None:
            continue
        secrets[key] = str(value)
    return secrets


def collect_profile(profile: str, secrets: Dict[str, str]) -> Dict[str, str]:
    config = PROFILE_CONFIG[profile]
    missing = [key for key in config["required"] if key not in secrets or secrets[key] == ""]
    if missing:
        raise SystemExit(f"missing required secrets for profile {profile}: {', '.join(missing)}")
    selected = {key: secrets[key] for key in config["required"]}
    for key in config["optional"]:
        if key in secrets and secrets[key] != "":
            selected[key] = secrets[key]
    return selected


def render_dotenv(values: Dict[str, str]) -> str:
    lines = []
    for key, value in values.items():
        if "\n" in value:
            raise SystemExit(f"secret {key} contains a newline and cannot be rendered safely as dotenv")
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def render_seaweed(values: Dict[str, str]) -> str:
    payload = {
        "identities": [
            {
                "name": "admin",
                "credentials": [
                    {
                        "accessKey": values["SEAWEED_S3_ACCESS_KEY"],
                        "secretKey": values["SEAWEED_S3_SECRET_KEY"],
                    }
                ],
                "actions": ["Admin", "Read", "Write", "List", "Tagging"],
            }
        ]
    }
    return json.dumps(payload, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and render profile-specific secrets from Infisical Cloud.")
    parser.add_argument("profile", choices=sorted(PROFILE_CONFIG.keys()))
    parser.add_argument("--out", required=True, help="Output file path")
    args = parser.parse_args()

    load_operator_env()
    api_url = normalize_api_url(os.environ.get("INFISICAL_API_URL", DEFAULT_INFISICAL_API_URL))
    config = PROFILE_CONFIG[args.profile]
    secret_path = resolve_secret_path(config["path_envs"], config["default_path"])

    access_token = login(api_url)
    secrets = fetch_secrets(api_url, access_token, secret_path)
    values = collect_profile(args.profile, secrets)

    if args.profile == "seaweed-s3":
        rendered = render_seaweed(values)
    else:
        rendered = render_dotenv(values)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
