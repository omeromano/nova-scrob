#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURES="$ROOT/scripts/tests/java/playback"
BRIDGE="$ROOT/scripts/templates/Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobPlaybackBridge.java"
BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_DIR"' EXIT

mapfile -t FIXTURE_SOURCES < <(find "$FIXTURES" -type f -name '*.java' | sort)

javac \
  -encoding UTF-8 \
  --release 17 \
  -d "$BUILD_DIR/classes" \
  "$BRIDGE" \
  "${FIXTURE_SOURCES[@]}"

java -cp "$BUILD_DIR/classes" tests.ScrobPlaybackBridgeLifecycleTest
