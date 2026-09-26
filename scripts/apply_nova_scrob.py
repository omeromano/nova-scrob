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
