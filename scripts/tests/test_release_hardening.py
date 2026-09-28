#!/usr/bin/env python3
"""Release-hardening invariants for the frozen dev.15 runtime baseline."""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_PROPERTIES = {
    "APP_ID": "org.courville.novascrob",
    "NOVA_TAG": "v6.4.72",
    "NOVA_BASE_VERSION": "6.4.72",
    "NOVA_MANIFEST": "manifest.xml",
}
EXPECTED_PREF_KEYS = {
    "scrob_url": "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConfig.java",
    "scrob_api_key": "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobCredentials.java",
    "scrob_enabled": "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConfig.java",
}
# Frozen against validated v0.2.0-dev.15. dev.16 is release hardening only.
EXPECTED_RUNTIME_SHA256 = {
    "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/Scrob.java": "b5605c6262635db36645bd388b6a6cf2d3e94adf36d0f5c3441a7bb0d6757443",
    "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobAuthManager.java": "b12432056b36eaebc70161e2e4333cb0fb312763087d210a2d56b6160ba95098",
    "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConfig.java": "4e067fd6433859772b0d9a885db87618043183b03e77cc1f70dc2f79452bb7da",
    "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnection.java": "cd1409bd2ab353ad533f13e1bc364265e5850b176e23cc6d214815531dae1e20",
    "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnectionCheck.java": "f5aa88951e5c5c307c5eac2d08b753631fc67035331a34cbcce6ab8726d89807",
    "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnectionState.java": "b89de1dd303a10bc4d302a5b73dce29a7fe0b38f147269c56c9fb8019facf9d6",
    "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobCredentials.java": "8756d17b7a7b8054077ddd7e7254100d8aaabc8d9ecac91b35895e7b6d13cf0e",
    "scripts/templates/Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobDiagnosticsPreference.java": "c20d7a8da5d04aebbeedd16ee4c536ad188376acebbbd0ce63b1345ab4cc8ae1",
    "scripts/templates/Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobLoginPreference.java": "8a914845b63791911248acf7daa616830958ccad837857c2b9b87cd2cd8ffcc1",
    "scripts/templates/Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobPlaybackBridge.java": "763bf86082bbe6342ff049b1d3a4ede9f78a8a3b670c41c9c8685f6715cee1ef",
    "scripts/patches/player.py": "00651a9e9bd5f409f8c4bb0ee31504ec6db4c90ac000bd529bd3528320b2a07a",
    "scripts/patches/fork_ui.py": "c24b76b194fded824aa8b314943147fa4ec3d6f211e61c7c5f72d2d6e15b3aef",
    "scripts/patches/preferences.py": "cc7b78792d603f586354aede1b51c145b34eee7295c25eb0216dbd0e474f5b6e",
    "scripts/patches/transport.py": "1543f8a54a6737e247fa991b986af17800a2d74f1435b5557dcfeeef9f23ff0c",
    "scripts/patches/identity.py": "f9b57f563a833ce1215e1ac98dc293dc1e37caadbb246bdf7457b3ae223f795e",
}
EXPECTED_SIGNING_KEY_SHA256 = "ba6ed472e2ab2073bed02eb2ebe8eb26995899fc0c4a1a26d87af76c5e5164a8"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(rel: str) -> str:
    return sha256_bytes((ROOT / rel).read_bytes())


def load_properties() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in (ROOT / "nova-scrob.properties").read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw and not raw.startswith("#"):
            key, value = raw.split("=", 1)
            values[key] = value
    return values


def main() -> None:
    props = load_properties()
    if props.get("APP_VERSION") != "0.2.0-dev.16":
        raise SystemExit(f"Unexpected dev.16 APP_VERSION: {props.get('APP_VERSION')!r}")
    for key, expected in EXPECTED_PROPERTIES.items():
        actual = props.get(key)
        if actual != expected:
            raise SystemExit(f"Release invariant changed: {key}={actual!r}, expected {expected!r}")

    for key, rel in EXPECTED_PREF_KEYS.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        if f'"{key}"' not in text:
            raise SystemExit(f"Upgrade preference key changed or disappeared: {key}")

    for rel, expected in EXPECTED_RUNTIME_SHA256.items():
        actual = sha256_file(rel)
        if actual != expected:
            raise SystemExit(
                "Frozen dev.15 runtime surface changed during release hardening: "
                f"{rel}\nexpected={expected}\nactual={actual}"
            )

    encoded = b"".join((ROOT / "signing/nova-scrob.jks.b64").read_bytes().split())
    signing_bytes = base64.b64decode(encoded, validate=True)
    signing_hash = sha256_bytes(signing_bytes)
    if signing_hash != EXPECTED_SIGNING_KEY_SHA256:
        raise SystemExit(
            "Signing key identity changed; install-over continuity would be at risk: "
            + signing_hash
        )

    workflow = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
    for forbidden in ("actions/checkout@v4", "actions/upload-artifact@v4"):
        if forbidden in workflow:
            raise SystemExit("Deprecated Node-20 action remains in release workflow: " + forbidden)

    print("NOVA Scrob dev.16 release-hardening invariants passed")
    print(" - package identity frozen")
    print(" - legacy Scrob preference keys frozen")
    print(" - validated dev.15 runtime/patch implementation frozen")
    print(" - signing key identity frozen")


if __name__ == "__main__":
    main()
