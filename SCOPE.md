# Scope

NOVA Scrob is intentionally a minimal patch.

## In scope

- Local NOVA playback → Scrob.
- Scrob URL.
- Scrob device-link authorization and Bearer-token refresh.
- Persistent configuration across restart/reboot.
- A package/signing identity separate from stock NOVA.

## Out of scope

- Scrob library/history import into NOVA.
- Ratings or lists.
- Nuvio, Jellyfin, Plex, or Emby integration.
- Changes to NOVA's player, scraper, browsing UI, or media library beyond what is required for playback tracking.
- Replacing unrelated Trakt library features.

- v0.1.1 fixes authorization launch/lifecycle and persistence visibility only.
