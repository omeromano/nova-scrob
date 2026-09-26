# NOVA Scrob v0.1.7

Minimal NOVA Video Player fork for direct playback tracking to a self-hosted Scrob instance.

This build is based on v0.1.5 and mirrors the API-key path used by `ellite/scrob-kodi`:
- Scrob URL + API key
- `POST /api/proxy/webhooks/kodi?api_key=...`
- Kodi-compatible playback payloads
- 60-second progress reporting
- authenticated connection test through `webhooks/kodi/history`
- no username/password handling in NOVA Scrob

App identity remains `org.courville.novascrob`.

Launcher branding uses the exact supplied NOVA/Scrob artwork for legacy launchers and adaptive Android icon resources derived from that artwork for Android 8+.
