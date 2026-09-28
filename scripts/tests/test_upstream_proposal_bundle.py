#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FEATURE_PATHS = [
    "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConfig.java",
    "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobCredentials.java",
    "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnectionState.java",
    "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnectionCheck.java",
    "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnection.java",
    "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobAuthManager.java",
    "MediaLib/src/com/archos/mediacenter/utils/scrob/Scrob.java",
    "Video/res/xml/preferences_video.xml",
    "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobLoginPreference.java",
    "Video/res/values/scrob_strings.xml",
    "Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java",
    "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobPlaybackBridge.java",
]


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        pristine = t / "pristine"
        patched = t / "patched"
        output = t / "bundle"
        for i, rel in enumerate(FEATURE_PATHS):
            b = patched / rel
            b.parent.mkdir(parents=True, exist_ok=True)
            if i in (7, 10):
                a = pristine / rel
                a.parent.mkdir(parents=True, exist_ok=True)
                a.write_text(f"upstream {rel}\n", encoding="utf-8")
                b.write_text(f"upstream {rel}\nportable feature change\n", encoding="utf-8")
            else:
                b.write_text(f"portable feature file {rel}\n", encoding="utf-8")
        surface = t / "surface.md"
        surface.write_text("portable feature surface\n", encoding="utf-8")
        subprocess.run(
            [
                "python3",
                str(ROOT / "scripts/generate_upstream_proposal_bundle.py"),
                str(pristine),
                str(patched),
                str(output),
                "--surface-report",
                str(surface),
            ],
            check=True,
        )
        patch = (output / "UPSTREAM_FEATURE.patch").read_text(encoding="utf-8")
        for forbidden in ("org.courville.novascrob", "scrob_back_menu"):
            if forbidden in patch:
                raise SystemExit("fork-only marker leaked into generated proposal patch: " + forbidden)
        for required in ("PlayerActivity.java", "ScrobPlaybackBridge.java", "Scrob.java"):
            if required not in patch:
                raise SystemExit("expected portable feature path missing from generated patch: " + required)
        for required_file in (
            "PATCH_SUMMARY.md",
            "UPSTREAM_FEATURE.md",
            "PROPOSAL_DRAFT.md",
            "PR_DRAFT.md",
            "ARCHITECTURE.md",
            "UPSTREAM_FEATURE_SURFACE.md",
        ):
            if not (output / required_file).is_file():
                raise SystemExit("proposal bundle output missing: " + required_file)
    print("Scrob upstream proposal bundle generation test passed")


if __name__ == "__main__":
    main()
