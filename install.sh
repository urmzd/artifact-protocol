#!/usr/bin/env sh
# Install gap-cli — uses uv if available, falls back to pip.
set -e

PACKAGE="gap-cli"

if command -v uv > /dev/null 2>&1; then
    echo "Installing ${PACKAGE} with uv..."
    uv tool install "${PACKAGE}"
else
    echo "uv not found — falling back to pip..."
    pip install --upgrade "${PACKAGE}"
fi

echo "Done. Run 'gap-evals --help' to get started."
