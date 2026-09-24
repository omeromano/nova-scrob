# v0.1.4 scope

Identity/branding pass on top of the v0.1.3 stability fix.

In scope:
- effective package ID: `org.courville.novascrob`
- visible app name: `NOVA Scrob`
- Scrob-themed launcher icon
- final-APK package/label/icon assertions
- preserve v0.1.3 login and playback behavior unchanged

Out of scope:
- library sync
- ratings sync
- Jellyfin/Nuvio integration
- playback metadata redesign
- changes to Scrob authentication behavior


Build fix: branding is applied to NOVA flavor manifests (including noamazon) as well as the base manifest to avoid Android manifest-merger icon conflicts.
