#!/bin/sh
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$(mktemp -d)"
printf '{"name": "/", "type": "dir",\n' > "$WORK/broken.json"
printf '{"name": "/", "type": "socket"}\n' > "$WORK/bad_node.json"
echo "=== образ VFS не найден ==="
"$ROOT/run.sh" --vfs "$WORK/nosuch.json" < /dev/null
echo "код возврата: $?"
echo "=== неверный формат образа VFS ==="
"$ROOT/run.sh" --vfs "$WORK/broken.json" < /dev/null
echo "код возврата: $?"
echo "=== неизвестный тип узла VFS ==="
"$ROOT/run.sh" --vfs "$WORK/bad_node.json" < /dev/null
echo "код возврата: $?"
echo "=== vfs-init очищает физическое представление VFS ==="
cp "$ROOT/tests/data/vfs_deep.json" "$WORK/vfs.json"
echo "размер образа до: $(wc -c < "$WORK/vfs.json") байт"
printf 'vfs-init\nvfs-init arg\n' | "$ROOT/run.sh" --vfs "$WORK/vfs.json"
echo "размер образа после: $(wc -c < "$WORK/vfs.json") байт"
rm -rf "$WORK"
