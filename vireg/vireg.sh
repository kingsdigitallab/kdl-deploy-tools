#!/usr/bin/env bash
# vireg.sh — run the vireg toolkit inside a container.
#
# Usage:
#   ./vireg.sh [-p PROJECT_NAME] [-d DOMAIN_KEY] [--reinstall] [ACTION]
#
# ACTION is one of: init | fetch | diff | report | test | accept | urls
#   (default: test)
#
# The default project comes from VIREG_PROJECT in the environment or .env,
# falling back to "default". Use --project to override it for one run.
#
# --reinstall  re-run `npm ci` inside the container (use after editing
#             package.json so the container's node_modules volume is refreshed).
#
# Prerequisite: Docker Engine + the Compose plugin must be installed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/build/docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/.env"

PROJECT="${VIREG_PROJECT:-default}"
REINSTALL=0
ACTION=""
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain|-d)
      [ $# -ge 2 ] || { echo "Error: $1 requires a value." >&2; exit 1; }
      DOMAIN="$2"
      shift 2
      ;;
    --project|-p)
      [ $# -ge 2 ] || { echo "Error: $1 requires a value." >&2; exit 1; }
      PROJECT="$2"
      shift 2
      ;;
    --reinstall)
      REINSTALL=1
      shift
      ;;
    -h|--help)
      sed -n '2,16p' "$0"
      exit 0
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#ARGS[@]} -gt 0 ]]; then
  ACTION="${ARGS[0]}"
fi
if [[ -z "$ACTION" ]]; then
  ACTION="test"
fi

ENV_ARGS=(-e "VIREG_PROJECT=$PROJECT" -e "VIREG_DOMAIN=$DOMAIN" -e "VIREG_UID=$(id -u)" -e "VIREG_GID=$(id -g)")

echo "[vireg] project=$PROJECT domain=$DOMAIN action=$ACTION"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: 'docker' was not found. Install Docker Engine + the Compose plugin, then retry." >&2
  exit 1
fi

# Build (no-op if cached) before running so the first invocation just works.
docker compose -f "$COMPOSE_FILE" build

if [ "$REINSTALL" = "1" ]; then
  exec docker compose -f "$COMPOSE_FILE" run --rm -u 0 "${ENV_ARGS[@]}" vireg npm ci --no-audit --no-fund
fi

exec docker compose -f "$COMPOSE_FILE" run --rm "${ENV_ARGS[@]}" vireg node vireg.mjs "$ACTION" "${ARGS[@]:1}"
