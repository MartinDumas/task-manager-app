#!/bin/sh
set -eu
# Run in application repo only. Installs project-level pre-push hook.
# Warning: this changes the repository-local core.hooksPath setting.
git rev-parse --show-toplevel >/dev/null
chmod +x .githooks/pre-push
git config --local core.hooksPath .githooks
echo 'Git pre-push protection enabled in this app repository.'
