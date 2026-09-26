# NOVA Scrob v0.1.5

Minimal NOVA Video Player fork that adds direct playback reporting to a self-hosted Scrob instance.

## v0.1.5 identity / branding pass

- Keeps the v0.1.3 Scrob username/password login and Preferences crash fix.
- Fixes package identity so the active Android `applicationId` is `org.courville.novascrob`.
- Changes the visible launcher/app label to **NOVA Scrob**.
- Adds the Scrob-themed NOVA launcher icon.
- Applies the label/icon to launcher and Leanback launcher activities as well as the application.
- CI inspects the final signed APK with `aapt dump badging` and fails unless package ID, label and icon are correct.
- Keeps the persistent NOVA Scrob signing key so future builds can update this package in place.

The Scrob password is used only during sign-in and is not persisted. The returned bearer token is stored in app preferences.


Build fix: branding is applied to NOVA flavor manifests (including noamazon) as well as the base manifest to avoid Android manifest-merger icon conflicts.


### v0.1.5 build-check fix
The final APK branding check validates the resolved application label and icon entry rather than the source resource name, because AAPT may rename compiled resources (for example to `res/go.png`).

## v0.1.5 notes

- Keeps the permanent Android package identity `org.courville.novascrob` and the existing NOVA Scrob signing key so releases from this point forward update in place.
- Uses the exact user-supplied recolored NOVA icon from `branding/nova_scrob_icon.png` (not a regenerated icon).
- Scrob password login still submits OAuth2 form data (`username` / `password`).
- Login now preserves POST bodies across HTTP redirects, detects HTML/non-API responses, and falls back from the public `/api/proxy/auth/login` route to `/auth/login` for deployments exposing the backend route directly.
- 2FA uses the same proxy/direct fallback behavior.
- Error messages no longer dump an entire HTML document into an Android toast.
