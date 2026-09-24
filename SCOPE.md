# NOVA Scrob scope

## Included

- Permanent parallel package identity: `org.courville.novascrob`
- Direct Scrob playback reporting from NOVA's existing playback callbacks
- 60-second progress reporting
- NOVA-style Scrob login dialog: URL + username + password
- Scrob TOTP/backup-code login when required
- Persistent URL, username, bearer token, and enabled state
- Disconnect/re-login flow
- Stable signing identity for in-place NOVA Scrob upgrades
- GitHub Actions APK artifact and release-on-tag

## Deliberately excluded

- API-key entry in the Android UI
- Kodi device-code authorization UI
- Scrob-to-NOVA history/resume synchronization
- Jellyfin or Nuvio changes
- Ratings/collection synchronization
- Unrelated NOVA UI or playback changes
