# v0.1.7 scope

- Fix playback webhook capture by routing NOVA's existing Trakt playback lifecycle callbacks to Scrob when Scrob is enabled.
- Preserve NOVA's existing scheduler; report progress at the patched 60-second cadence.
- Map initial play/resume to `Player.OnPlay`, periodic samples to `Player.OnAVChange`, pause to `Player.OnPause`, and stop to `Player.OnStop`, matching `scrob-kodi`.
- Add a touch-accessible in-app Back control for Carlinkit-style displays without a physical Back key; keep normal Android Back behavior intact.
- Add lightweight Scrob diagnostics without displaying or logging the API key.
- Display NOVA Scrob v0.1.7 and base NOVA v6.4.64 in diagnostics/preferences.
- Add `UPSTREAM.md` provenance.
- Keep package ID, signing identity, Scrob API-key configuration, and branding unchanged.
