#!/usr/bin/env bash
# Container entrypoint for vireg.
#
# Ensures npm dependencies are present, runs the requested command, then
# restores ownership of the generated project files to the host user so they
# are not left owned by root on the host filesystem.

set -euo pipefail

# Install dependencies if the volume was wiped/never seeded.
if [ ! -d node_modules ] || [ -z "$(ls -A node_modules 2>/dev/null)" ]; then
  echo "[vireg] node_modules not found, installing dependencies..."
  npm ci --no-audit --no-fund
  echo "[vireg] Dependencies installed."
fi

# Run the requested command; capture the exit status.
set +e
"$@"
status=$?
set -e

# Give generated files back to the host user when invoked via vireg.sh.
if [ -n "${VIREG_UID:-}" ] && [ -n "${VIREG_GID:-}" ] && [ "${VIREG_UID}" != "0" ]; then
  chown -R "${VIREG_UID}:${VIREG_GID}" /app/projects 2>/dev/null || true
fi

exit "${status}"
