# NOVA Scrob v0.1.7 playback/player fix

- Wire Scrob directly to NOVA `PlayerActivity.PlayerListener` callbacks, independent of Trakt authentication.
- `Player.OnPlay` on real play/resume, `Player.OnPause` on real pause, `Player.OnStop` on completion/intentional exit.
- Emit `Player.OnAVChange` every 60 seconds while playing using live player position/duration.
- Diagnostics expose the last internal stage before/through HTTP transport.
- Add a Back arrow to the player ActionBar beside NOVA's Info/audio/subtitle/brightness actions.
- Remove the previous global/floating Back control.
- Preserve package ID `org.courville.novascrob`, branding, signing, and NOVA v6.4.64 base.
