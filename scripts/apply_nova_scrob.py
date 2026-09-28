#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.config import PROJECT_ROOT, load_properties
from lib.patch_context import PatchContext
from patches import fork_ui, identity, player, preferences, transport
from patches.verify import verify_feature, verify_fork


def _is_fork_operation(op):
    rel = op["rel"]
    label = op["label"]
    if label.startswith("fork ") or label.startswith("NOVA Scrob fork"):
        return True
    return rel in {
        "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobDiagnosticsPreference.java",
        "Video/res/values/nova_scrob_diagnostics_strings.xml",
        "Video/res/drawable/ic_nova_scrob_back.xml",
        "Video/res/values/scrob_ids.xml",
        "Video/res/mipmap-nodpi/nova_scrob_icon.png",
        "Video/res/drawable-nodpi/nova_scrob_foreground.png",
        "Video/res/drawable/nova_scrob_icon_background.xml",
        "Video/res/mipmap-anydpi-v26/nova_scrob_icon.xml",
    }


def write_surface_report(ctx, output_path, *, feature_only):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    upstream_ops = [op for op in ctx.operations if op["initial_exists"]]
    added_ops = [op for op in ctx.operations if not op["initial_exists"]]
    upstream_files = sorted({op["rel"] for op in upstream_ops})
    added_files = sorted({op["rel"] for op in added_ops})
    anchor_ops = [op for op in upstream_ops if op["kind"] == "anchor-replace"]
    player_ops = [op for op in anchor_ops if op["rel"].endswith("PlayerActivity.java")]
    fork_ops = [op for op in ctx.operations if _is_fork_operation(op)]
    feature_ops = [op for op in ctx.operations if not _is_fork_operation(op)]

    mode = "portable Scrob feature only" if feature_only else "complete NOVA Scrob fork"
    lines = [
        "# NOVA Scrob patch-surface report",
        "",
        f"- Mode: **{mode}**",
        f"- Fork source version: `v{ctx.values['APP_VERSION']}`",
        f"- NOVA base: `{ctx.values['NOVA_TAG']}`",
        f"- Upstream-owned files modified: **{len(upstream_files)}**",
        f"- Upstream anchor replacements: **{len(anchor_ops)}**",
        f"- `PlayerActivity.java` anchor replacements: **{len(player_ops)}**",
        f"- Standalone files/assets added: **{len(added_files)}**",
        f"- Portable feature operations: **{len(feature_ops)}**",
        f"- Fork-overlay operations: **{len(fork_ops)}**",
        "",
        "## Upstream-owned files modified",
        "",
    ]
    for rel in upstream_files:
        rel_ops = [op for op in upstream_ops if op["rel"] == rel]
        lines.append(f"- `{rel}`")
        for op in rel_ops:
            scope = "fork overlay" if _is_fork_operation(op) else "portable feature"
            lines.append(f"  - {op['kind']}: {op['label']} ({scope})")

    lines += ["", "## Standalone additions", ""]
    for rel in added_files:
        scope = "fork overlay" if any(op["rel"] == rel and _is_fork_operation(op) for op in added_ops) else "portable feature"
        lines.append(f"- `{rel}` — {scope}")

    lines += ["", "## PlayerActivity boundary", ""]
    if feature_only:
        lines += [
            "The portable Scrob feature uses six `PlayerActivity` anchors:",
            "bridge field initialization, play, pause, completion, finish, and destroy.",
            "The NOVA Scrob custom ActionBar Back item is intentionally absent.",
        ]
    else:
        lines += [
            "The complete NOVA Scrob fork uses seven `PlayerActivity` anchors.",
            "Six belong to the portable Scrob playback feature; one belongs to the fork-only custom Back-button UX.",
            "This separation is structural: the installed fork retains the validated stop-then-Back behavior while the upstream-oriented feature can be preflighted independently.",
        ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_portable_feature(ctx, *, include_fork_diagnostics=False):
    transport.apply(ctx)
    preferences.apply(ctx, include_fork_diagnostics=include_fork_diagnostics)
    player.apply(ctx)


def main():
    parser = argparse.ArgumentParser(
        description="Apply or preflight the NOVA Scrob patch against an upstream NOVA checkout."
    )
    parser.add_argument("root", help="Path to the upstream NOVA checkout")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run the complete patch in memory and verify anchors without modifying the checkout",
    )
    parser.add_argument(
        "--feature-only",
        action="store_true",
        help="Apply/preflight only the portable Scrob feature; exclude NOVA Scrob package identity, branding, diagnostics UI, and custom Back-button UX",
    )
    parser.add_argument(
        "--surface-report",
        help="Write a Markdown inventory of upstream patch surfaces and standalone additions",
    )
    args = parser.parse_args()

    values = load_properties()
    ctx = PatchContext(args.root, PROJECT_ROOT, values, dry_run=args.check)

    try:
        if args.feature_only:
            apply_portable_feature(ctx, include_fork_diagnostics=False)
            verify_feature(ctx)
        else:
            # Full fork: portable feature first, then fork-only UX/identity overlay.
            apply_portable_feature(ctx, include_fork_diagnostics=True)
            fork_ui.apply(ctx)
            identity.apply(ctx)
            verify_fork(ctx)
        if args.surface_report:
            write_surface_report(ctx, args.surface_report, feature_only=args.feature_only)
    except RuntimeError as exc:
        print(f"NOVA Scrob patch compatibility error: {exc}", file=sys.stderr)
        return 2

    mode = "portable feature preflight OK" if args.feature_only and args.check else (
        "portable feature applied" if args.feature_only else ("preflight OK" if args.check else "patch applied")
    )
    print(
        f'NOVA Scrob v{values["APP_VERSION"]} {mode}; '
        f'base={values["NOVA_TAG"]}; appId={values["APP_ID"]}'
    )
    if ctx.changed:
        print("Touched patch surfaces:")
        for rel in ctx.changed:
            print(" - " + rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
