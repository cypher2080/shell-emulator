#!/bin/sh
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$ROOT/tests/scripts/stage3_all.vsh"
WORK="$(mktemp -d)"
cp "$ROOT/tests/data/"vfs_*.json "$WORK"
for name in vfs_min vfs_files vfs_deep; do
    echo "=== VFS: $name ==="
    "$ROOT/run.sh" --vfs "$WORK/$name.json" --script "$SCRIPT" < /dev/null
done
rm -rf "$WORK"
