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

mkdir -p "$LOCK_DIR"
MANIFEST_URL="https://github.com/nova-video-player/aos-AVP/releases/download/${NOVA_TAG}/manifest.xml"
LOCK_XML="$LOCK_DIR/UPSTREAM_LOCK.xml"

printf 'Downloading resolved NOVA release manifest: %s\n' "$MANIFEST_URL"
curl -fL --retry 3 --retry-all-errors "$MANIFEST_URL" -o "$LOCK_XML"

python3 "$PROJECT_ROOT/scripts/fetch_nova_release.py" \
  "$LOCK_XML" \
  "$DEST" \
  --jobs "$JOBS" \
  --expected-avp-prefix "$NOVA_BASE_COMMIT"

for path in AVP Video MediaLib FileCoreLibrary; do
  if [[ ! -d "$DEST/$path/.git" && ! -f "$DEST/$path/.git" ]]; then
    echo "Required NOVA project is missing after release-manifest materialization: $path" >&2
    exit 3
  fi
done

AVP_SHA="$(git -C "$DEST/AVP" rev-parse HEAD)"
case "$AVP_SHA" in
  "$NOVA_BASE_COMMIT"*) ;;
  *)
    echo "Expected aos-AVP release commit prefix $NOVA_BASE_COMMIT for $NOVA_TAG, got $AVP_SHA" >&2
    exit 4
    ;;
esac

# Verify the resolved Video source is actually the requested release before patching.
if ! grep -Eq "versionName[[:space:]]*=[[:space:]]*['\"]${NOVA_BASE_VERSION}['\"]" "$DEST/Video/build.gradle"; then
  echo "Resolved Video source does not declare NOVA versionName ${NOVA_BASE_VERSION}" >&2
  grep -n "versionName" "$DEST/Video/build.gradle" | head -20 >&2 || true
  exit 5
fi

python3 "$PROJECT_ROOT/scripts/summarize_upstream_lock.py" \
  "$LOCK_XML" \
  --release "$NOVA_TAG" \
  --version "$NOVA_BASE_VERSION" \
  --manifest-commit "$AVP_SHA" \
  > "$LOCK_DIR/UPSTREAM_LOCK.txt"

sha256sum "$LOCK_XML" > "$LOCK_DIR/UPSTREAM_LOCK.sha256"

printf 'Resolved NOVA %s source from release manifest:\n' "$NOVA_TAG"
cat "$LOCK_DIR/UPSTREAM_LOCK.txt"
