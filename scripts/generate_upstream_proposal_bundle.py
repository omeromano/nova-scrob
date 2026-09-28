#!/usr/bin/env python3
"""Generate a reviewable upstream-facing patch bundle from pristine and feature-only NOVA trees."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import shutil
from pathlib import Path

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


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pristine")
    ap.add_argument("patched")
    ap.add_argument("output")
    ap.add_argument("--surface-report")
    args = ap.parse_args()

    pristine = Path(args.pristine).resolve()
    patched = Path(args.patched).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    chunks: list[str] = []
    modified: list[str] = []
    added: list[str] = []
    for rel in FEATURE_PATHS:
        a = pristine / rel
        b = patched / rel
        if not b.exists():
            raise SystemExit(f"Expected feature path missing from patched tree: {rel}")
        a_lines = read_lines(a)
        b_lines = read_lines(b)
        if a_lines == b_lines:
            raise SystemExit(f"Expected feature path did not change: {rel}")
        if a.exists():
            modified.append(rel)
            from_name = "a/" + rel
        else:
            added.append(rel)
            from_name = "/dev/null"
        diff = difflib.unified_diff(
            a_lines,
            b_lines,
            fromfile=from_name,
            tofile="b/" + rel,
            n=3,
        )
        chunks.extend(diff)

    patch_text = "".join(chunks)
    patch_path = output / "UPSTREAM_FEATURE.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    patch_sha = hashlib.sha256(patch_path.read_bytes()).hexdigest()

    plus = sum(1 for line in patch_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    minus = sum(1 for line in patch_text.splitlines() if line.startswith("-") and not line.startswith("---"))
    summary = [
        "# Generated upstream feature patch summary",
        "",
        "This bundle is generated from the portable `--feature-only` profile against pristine locked NOVA v6.4.72 source.",
        "It deliberately excludes NOVA Scrob package identity, branding, fork diagnostics UI, build-lock machinery, and the custom Back button.",
        "",
        f"- Files modified in upstream: **{len(modified)}**",
        f"- New feature files: **{len(added)}**",
        f"- Approximate diff additions: **{plus}**",
        f"- Approximate diff deletions: **{minus}**",
        f"- Patch SHA-256: `{patch_sha}`",
        "",
        "## Modified upstream files",
        "",
    ]
    summary.extend(f"- `{x}`" for x in modified)
    summary.extend(["", "## New feature files", ""])
    summary.extend(f"- `{x}`" for x in added)
    (output / "PATCH_SUMMARY.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    project_root = Path(__file__).resolve().parents[1]
    for rel in (
        "UPSTREAM_FEATURE.md",
        "upstream-proposal/PROPOSAL_DRAFT.md",
        "upstream-proposal/PR_DRAFT.md",
        "upstream-proposal/ARCHITECTURE.md",
    ):
        src = project_root / rel
        shutil.copyfile(src, output / src.name)
    if args.surface_report:
        shutil.copyfile(args.surface_report, output / "UPSTREAM_FEATURE_SURFACE.md")

    print(f"Generated upstream proposal bundle: {output}")
    print(f"Portable feature patch SHA-256: {patch_sha}")


if __name__ == "__main__":
    main()
