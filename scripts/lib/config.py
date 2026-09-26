from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROPERTIES_FILE = PROJECT_ROOT / "nova-scrob.properties"


def load_properties(path=PROPERTIES_FILE):
    values = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise RuntimeError(f"Invalid properties line: {raw!r}")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    required = {
        "APP_VERSION",
        "APP_ID",
        "NOVA_TAG",
        "NOVA_BASE_VERSION",
        "NOVA_BASE_COMMIT",
        "NOVA_MANIFEST",
    }
    missing = sorted(required - values.keys())
    if missing:
        raise RuntimeError("Missing required properties: " + ", ".join(missing))
    return values
