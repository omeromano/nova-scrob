# Draft proposal to NOVA maintainers: optional Scrob playback tracking

I maintain a small NOVA-derived build that adds optional playback-progress reporting to a self-hosted Scrob server. During development, the integration was refactored so the tracking feature is isolated from the fork's branding/package/build machinery and can be evaluated independently.

The feature currently consists of:

- an optional Scrob settings entry (server URL, enabled state, API-key authentication);
- a small `ScrobPlaybackBridge` that owns playback lifecycle/progress scheduling;
- a Scrob client/transport layer with credential-safe connection state/diagnostics; and
- six shallow integration points in `PlayerActivity`: bridge initialization, play, pause, completion, finish, and destroy.

The portable profile is continuously preflighted against the exact NOVA v6.4.72 release manifest and has executable regression coverage for play, periodic progress, pause/stop, duplicate-stop suppression, playback-snapshot fallback, disabled tracking, and transport failures.

The proposed upstream feature explicitly excludes the fork's package ID, launcher branding/icon, fork-version diagnostics UI, custom Back button, and source-lock/build infrastructure.

If this is a feature direction you would consider, I can adapt the implementation to your preferred branch, naming, configuration UX, and testing conventions before opening a formal PR. I can also provide the generated feature-only patch and patch-surface report for review first.
