# Draft PR: optional Scrob playback tracking

## Summary

Adds optional Scrob playback tracking without changing NOVA's default behavior when Scrob is unconfigured or disabled.

## Architecture

- `ScrobPlaybackBridge` owns playback lifecycle/progress behavior.
- Scrob transport/configuration/authentication are separate from `PlayerActivity`.
- `PlayerActivity` contains six shallow lifecycle integration points only.
- Existing NOVA playback position ownership is respected via `PlayerService.PlaybackSnapshot`, with live-player fallback.

## Behavior covered

- play event;
- approximately 60-second progress updates;
- pause event;
- stop/completion event;
- duplicate-stop suppression;
- safe behavior when playback state is unavailable;
- connection/authentication/server error classification without exposing the API key.

## Deliberately not included

- NOVA Scrob package/branding/icon;
- custom NOVA Scrob Back button;
- fork-version diagnostics presentation;
- fork source-lock/build/release infrastructure.

## Validation

The feature-only profile is preflighted independently against locked NOVA source and is required to remain at six `PlayerActivity` anchors with zero fork-overlay operations. The playback lifecycle harness compiles and exercises the real bridge implementation against deterministic stubs before the full NOVA build.
