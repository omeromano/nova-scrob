# Scrob integration architecture for upstream NOVA

The upstream-facing feature is deliberately independent of the NOVA Scrob fork identity.

```text
NOVA PlayerActivity
    |  six shallow lifecycle anchors
    v
ScrobPlaybackBridge
    |-- playback snapshot / live-player fallback
    |-- 60-second progress scheduling
    |-- duplicate-stop suppression
    v
Scrob transport/client
    |-- ScrobConfig
    |-- ScrobCredentials
    |-- ScrobAuthManager
    |-- ScrobConnection / state
    v
Scrob server
```

The six current `PlayerActivity` anchors are bridge initialization, play, pause, completion, finish, and destroy. Scrob implementation details, timers, HTTP behavior, credential persistence, and progress calculation do not live in `PlayerActivity`.

The NOVA Scrob fork additionally carries its own application identity/branding, fork diagnostics presentation, reproducible-build/source-lock machinery, and a custom ActionBar Back item. Those are intentionally excluded from the upstream feature proposal.
