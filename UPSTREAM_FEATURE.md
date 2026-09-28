# NOVA Scrob — upstream feature boundary (0.2.0-rc.1)

This document describes the portion of NOVA Scrob intended to be portable to official NOVA. It is not a proposal to merge the NOVA Scrob fork itself.

## Portable Scrob feature

The `--feature-only` patch profile contains:

- Scrob URL/enabled configuration and API-key credential abstraction.
- Connection/authentication state and credential-safe diagnostics data.
- Webhook transport/client behavior.
- Scrob login/settings entry.
- `ScrobPlaybackBridge`.
- Six shallow `PlayerActivity` lifecycle anchors: bridge initialization, play, pause, completion, finish, and destroy.

The playback bridge owns the 60-second progress scheduler, duplicate-stop suppression, `PlayerService.PlaybackSnapshot` handling, live-player fallback, progress calculation, and webhook dispatch.

## Explicitly excluded fork overlay

The feature-only profile excludes:

- `org.courville.novascrob` package identity.
- NOVA Scrob launcher name/icon/manifest branding.
- Fork build/source-lock infrastructure.
- Fork-version diagnostics preference/UI.
- The custom ActionBar Back button and its resources.

The custom Back button remains in the complete fork because it is useful on the target installation, but Scrob tracking does not require NOVA upstream to adopt it.

## Verification

CI preflights the feature-only profile separately against the locked NOVA v6.4.72 release source and requires exactly six `PlayerActivity` anchors with zero fork-overlay operations. The complete fork is then preflighted separately and requires seven anchors. Both profiles share the same lifecycle/auth/transport regression gates.

## RC1 release-hardening output

The CI pipeline now creates a reviewable upstream proposal bundle from a real `--feature-only` application to the locked v6.4.72 source. The generated patch is checked to exclude `org.courville.novascrob` and `scrob_back_menu`, and is shipped with a generated file/diff summary plus proposal/PR drafts. The portable runtime itself remains unchanged from validated dev.15.
