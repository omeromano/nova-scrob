# NOVA Scrob

A deliberately small personal fork/patch of NOVA Video Player that sends **local playback** to a self-hosted Scrob instance instead of requiring Trakt for live scrobbling.

## Baseline

- NOVA upstream: **v6.4.64**
- NOVA Scrob: **v0.1.0**
- Android package: **`org.courville.novascrob`**
- Scrob authentication: **device-link / Bearer token**

The package ID is intentionally different from stock NOVA, so both apps can coexist on the same Android device. The build also uses one persistent signing key so future NOVA Scrob APKs can update the same installation.

## What v0.1.0 changes

Only the minimum needed for Scrob:

- Adds **Settings → Scrob**.
- Stores the Scrob base URL persistently using Android `SharedPreferences`.
- Adds **Authorize with Scrob** using Scrob's short-code device-link flow.
- Persists access token, refresh token, and token expiry across app restarts/reboots.
- Refreshes the Bearer token when needed.
- Sends NOVA's existing playback callbacks to Scrob's Kodi-compatible webhook:
  - play
  - progress (about every 60 seconds)
  - pause
  - stop/completion
- Leaves the rest of NOVA as close to upstream as possible.

There is **no API-key text field**, no Scrob library browser, and no Scrob→NOVA history synchronization.

## Create the repository using only GitHub's web interface

1. Create a new GitHub repository named `nova-scrob` (or any name you prefer).
2. Upload the contents of this bundle preserving these paths:

```text
.github/workflows/build.yml
scripts/apply_nova_scrob.py
signing/nova-scrob.jks.b64
.gitignore
README.md
SCOPE.md
```

3. Commit to `main` with something like:

```text
Initial NOVA Scrob v0.1.0
```

4. Open **Actions → Build NOVA Scrob → Run workflow**.
5. Download the artifact named **`nova-scrob-v0.1.0-apk`**.
6. Install `nova-scrob-v0.1.0.apk` using APKInstaller.

## First-time setup on Android

1. Open **NOVA Scrob → Settings → Scrob**.
2. Enter only the Scrob base URL, for example `https://scrob.example.com`.
3. Select **Authorize with Scrob**.
4. NOVA Scrob displays a short code and your Scrob `/link` address.
5. On your phone or computer, open that address, sign in, and approve the device.
6. Return to NOVA Scrob; it should display **Authorized ✓**.
7. Enable **Use Scrob for playback tracking**.

The URL and authorization tokens are persisted locally and should survive an app restart or Android reboot.

## Signing note

`signing/nova-scrob.jks.b64` is a dedicated **personal-build signing key** included only so successive APKs from this repository have the same Android signature. It is not intended for Google Play or public production distribution. If this project is ever published broadly, replace it with a private release key stored in GitHub Secrets.
