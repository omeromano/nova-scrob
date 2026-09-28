#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPLIER = ROOT / "scripts" / "apply_nova_scrob.py"
PREFERENCES = ROOT / "scripts" / "patches" / "preferences.py"
FORK_UI = ROOT / "scripts" / "patches" / "fork_ui.py"
CORE_STRINGS = ROOT / "scripts" / "templates" / "Video" / "res" / "values" / "scrob_strings.xml"
FORK_STRINGS = ROOT / "scripts" / "templates" / "Video" / "res" / "values" / "nova_scrob_diagnostics_strings.xml"


def require(text, needle, label):
    if needle not in text:
        raise AssertionError(f"{label} missing: {needle}")


def forbid(text, needle, label):
    if needle in text:
        raise AssertionError(f"{label} unexpectedly contains: {needle}")


def main():
    applier = APPLIER.read_text(encoding="utf-8")
    prefs = PREFERENCES.read_text(encoding="utf-8")
    fork_ui = FORK_UI.read_text(encoding="utf-8")
    core_strings = CORE_STRINGS.read_text(encoding="utf-8")
    fork_strings = FORK_STRINGS.read_text(encoding="utf-8")

    require(applier, '"--feature-only"', "feature-only CLI")
    require(applier, "verify_feature(ctx)", "feature-only verifier")
    require(applier, "fork_ui.apply(ctx)", "fork-only UI overlay")
    require(applier, "identity.apply(ctx)", "fork identity overlay")
    require(applier, "include_fork_diagnostics=False", "feature-only diagnostics exclusion")
    require(applier, "include_fork_diagnostics=True", "full-fork diagnostics inclusion")

    require(prefs, "FORK_DIAGNOSTICS_PREFERENCE", "fork diagnostics preference fragment")
    require(prefs, "include_fork_diagnostics", "diagnostics mode boundary")
    forbid(core_strings, "NOVA Scrob diagnostics", "portable Scrob strings")
    require(fork_strings, "NOVA Scrob diagnostics", "fork diagnostics strings")

    require(fork_ui, "custom Back item", "fork Back documentation")
    forbid(fork_ui, "ScrobPlaybackBridge.java", "fork UI must not own bridge implementation")

    print("Scrob portable-feature/fork-overlay separation checks passed")


if __name__ == "__main__":
    main()
