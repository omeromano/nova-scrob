#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.config import PROJECT_ROOT, load_properties
from lib.patch_context import PatchContext
from patches import identity, player, preferences, transport
from patches.verify import verify


def write_surface_report(ctx, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    upstream_ops = [op for op in ctx.operations if op["initial_exists"]]
    added_ops = [op for op in ctx.operations if not op["initial_exists"]]
    upstream_files = sorted({op["rel"] for op in upstream_ops})
    added_files = sorted({op["rel"] for op in added_ops})
    anchor_ops = [op for op in upstream_ops if op["kind"] == "anchor-replace"]
    player_ops = [op for op in anchor_ops if op["rel"].endswith("PlayerActivity.java")]

    lines = [
        "# NOVA Scrob patch-surface report",
        "",
        f"- Fork: `v{ctx.values['APP_VERSION']}`",
        f"- NOVA base: `{ctx.values['NOVA_TAG']}`",
        f"- Upstream-owned files modified: **{len(upstream_files)}**",
        f"- Upstream anchor replacements: **{len(anchor_ops)}**",
        f"- `PlayerActivity.java` anchor replacements: **{len(player_ops)}**",
        f"- Standalone files/assets added by NOVA Scrob: **{len(added_files)}**",
        "",
        "## Upstream-owned files modified",
        "",
    ]
    for rel in upstream_files:
        rel_ops = [op for op in upstream_ops if op["rel"] == rel]
        lines.append(f"- `{rel}`")
        for op in rel_ops:
            lines.append(f"  - {op['kind']}: {op['label']}")

    lines += ["", "## Standalone NOVA Scrob additions", ""]
    for rel in added_files:
        lines.append(f"- `{rel}`")

    lines += [
        "",
        "## PlayerActivity boundary",
        "",
        "Dev.13 deliberately removes two upstream anchors used by dev.12: the Scrob import insertion and the custom `MENU_BACK_ID` constant insertion.",
        "The bridge field now uses its fully qualified class name, and the Back action uses a standalone generated resource ID (`R.id.scrob_back_menu`).",
        "Playback lifecycle calls are otherwise unchanged.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


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
        "--surface-report",
        help="Write a Markdown inventory of upstream patch surfaces and standalone additions",
    )
    args = parser.parse_args()

    values = load_properties()
    ctx = PatchContext(args.root, PROJECT_ROOT, values, dry_run=args.check)

    # Keep modules in dependency/order-of-risk order: standalone files first,
    # then settings/player anchors, then application identity/branding.
    try:
        transport.apply(ctx)
        preferences.apply(ctx)
        player.apply(ctx)
        identity.apply(ctx)
        verify(ctx)
        if args.surface_report:
            write_surface_report(ctx, args.surface_report)
    except RuntimeError as exc:
        print(f"NOVA Scrob patch compatibility error: {exc}", file=sys.stderr)
        return 2

    mode = "preflight OK" if args.check else "patch applied"
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
