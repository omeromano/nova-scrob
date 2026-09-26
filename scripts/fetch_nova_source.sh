#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="${1:-$PROJECT_ROOT/nova-src}"
LOCK_DIR="${LOCK_DIR:-$PROJECT_ROOT/dist}"
JOBS="${JOBS:-4}"

# shellcheck disable=SC1091
source "$PROJECT_ROOT/nova-scrob.properties"

for name in NOVA_TAG NOVA_BASE_VERSION NOVA_BASE_COMMIT NOVA_MANIFEST; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required metadata: $name" >&2
    exit 2
  fi
done

if [[ -n "${REPO_BIN:-}" ]]; then
  repo_bin="$REPO_BIN"
elif command -v repo >/dev/null 2>&1; then
  repo_bin="$(command -v repo)"
else
  repo_bin="$(mktemp)"
  trap 'rm -f "$repo_bin"' EXIT
  curl -fsSL https://storage.googleapis.com/git-repo-downloads/repo -o "$repo_bin"
  chmod +x "$repo_bin"
fi

rm -rf "$DEST"
mkdir -p "$DEST" "$LOCK_DIR"

(
  cd "$DEST"
  "$repo_bin" init \
    -u https://github.com/nova-video-player/aos-AVP \
    -b "$NOVA_TAG" \
    -m "$NOVA_MANIFEST" \
    --depth=1

  "$repo_bin" sync \
    -c \
    -j"$JOBS" \
    --no-tags \
    --no-clone-bundle

  "$repo_bin" manifest -r > "$LOCK_DIR/UPSTREAM_LOCK.xml"
)

for path in AVP Video MediaLib FileCoreLibrary; do
  if [[ ! -d "$DEST/$path/.git" && ! -f "$DEST/$path/.git" ]]; then
    echo "Required NOVA project is missing after repo sync: $path" >&2
    exit 3
  fi
done

manifest_commit="$(git -C "$DEST/.repo/manifests" rev-parse HEAD)"
case "$manifest_commit" in
  "$NOVA_BASE_COMMIT"*) ;;
  *)
    echo "Expected aos-AVP release-tag commit prefix $NOVA_BASE_COMMIT for $NOVA_TAG, got $manifest_commit" >&2
    exit 4
    ;;
esac

python3 "$PROJECT_ROOT/scripts/summarize_upstream_lock.py" \
  "$LOCK_DIR/UPSTREAM_LOCK.xml" \
  --release "$NOVA_TAG" \
  --version "$NOVA_BASE_VERSION" \
  --manifest-commit "$manifest_commit" \
  > "$LOCK_DIR/UPSTREAM_LOCK.txt"

sha256sum "$LOCK_DIR/UPSTREAM_LOCK.xml" > "$LOCK_DIR/UPSTREAM_LOCK.sha256"

printf 'Resolved NOVA %s source:\n' "$NOVA_TAG"
cat "$LOCK_DIR/UPSTREAM_LOCK.txt"
