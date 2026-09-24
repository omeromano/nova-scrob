# NOVA Scrob

Minimal personal fork of NOVA Video Player that reports local playback directly to a self-hosted Scrob instance without requiring Trakt.

## v0.1.3

This build replaces the experimental device-code/API-key setup with a NOVA-style credential dialog.

In **Settings → Scrob → Scrob account**, enter:

- Scrob URL (for example `https://scrob.example.com`)
- Scrob username
- Scrob password

NOVA Scrob signs in through Scrob's normal `/auth/login` API and stores only the returned bearer token plus the URL and username. **The password is not persisted.** If the Scrob account uses TOTP 2FA, a second dialog asks for the authenticator/backup code.

After login, local playback is reported to Scrob through its Kodi-compatible webhook transport. The patch reuses NOVA's existing playback lifecycle instead of introducing another playback service.

### Persistence

The Scrob URL, username, bearer token, and enabled state use Android persistent `SharedPreferences`, so they should survive app restarts and device reboots. If Scrob later rejects an expired/revoked token, NOVA Scrob clears that token and the account can be signed in again from Settings.

### Scope

NOVA Scrob intentionally does **not** add Scrob browsing, two-way library/history synchronization, Nuvio/Jellyfin integration, ratings, or other NOVA feature changes.

## Build

GitHub Actions fetches the exact NOVA `v6.4.64` source and submodule commits, applies `scripts/apply_nova_scrob.py`, builds the release APK, and signs it with the fork's persistent signing identity.

Run **Actions → Build NOVA Scrob → Run workflow**. The output artifact is `nova-scrob-v0.1.3-apk`.

Pushing a `v0.1.3` tag also publishes the APK to GitHub Releases.


## v0.1.3

Fixes the Preferences crash in v0.1.2 by placing `ScrobLoginPreference` in NOVA's actual Java source set (`Video/src/main/java/...`). No authentication or playback behavior changes are intended in this build.
