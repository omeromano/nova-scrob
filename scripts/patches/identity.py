import re
import xml.etree.ElementTree as ET

ANDROID_NS = "http://schemas.android.com/apk/res/android"
A = "{" + ANDROID_NS + "}"
ET.register_namespace("android", ANDROID_NS)


def apply(ctx):
    app_id = ctx.values["APP_ID"]
    build = "Video/build.gradle"
    manifest = "Video/AndroidManifest.xml"

    b = ctx.read(build)
    app_id_re = re.compile(r'(?m)^(\s*)applicationId\s*(?:=\s*)?[\"\']org\.courville\.nova[\"\']\s*$')
    matches = list(app_id_re.finditer(b))
    if len(matches) != 1:
        raise RuntimeError(
            f"applicationId patch: expected exactly one active stock NOVA applicationId, found {len(matches)}"
        )
    b = app_id_re.sub(lambda m: f'{m.group(1)}applicationId = "{app_id}"', b, count=1)
    ctx.write(build, b)

    m = ctx.read(manifest).replace("org.courville.nova", app_id)
    try:
        root = ET.fromstring(m)
    except Exception as e:
        raise RuntimeError(f"Could not parse {manifest}: {e}") from e
    app = root.find("application")
    if app is None:
        raise RuntimeError("No <application> in Video/AndroidManifest.xml")
    app.set(A + "label", "NOVA Scrob")
    app.set(A + "icon", "@mipmap/nova_scrob_icon")
    app.set(A + "roundIcon", "@mipmap/nova_scrob_icon")
    for child in list(app):
        if child.tag not in ("activity", "activity-alias"):
            continue
        launcher = False
        for intent_filter in child.findall("intent-filter"):
            actions = {x.get(A + "name", "") for x in intent_filter.findall("action")}
            categories = {x.get(A + "name", "") for x in intent_filter.findall("category")}
            if "android.intent.action.MAIN" in actions and (
                "android.intent.category.LAUNCHER" in categories
                or "android.intent.category.LEANBACK_LAUNCHER" in categories
            ):
                launcher = True
                break
        if launcher:
            child.set(A + "label", "NOVA Scrob")
            child.set(A + "icon", "@mipmap/nova_scrob_icon")
            child.set(A + "roundIcon", "@mipmap/nova_scrob_icon")
    ctx.write(manifest, ET.tostring(root, encoding="unicode"))

    # Flavor manifests have higher merger priority than the base manifest.
    for flavor_manifest in sorted(ctx.path("Video/src").glob("*/AndroidManifest.xml")):
        rel = str(flavor_manifest.relative_to(ctx.root))
        try:
            fm_root = ET.fromstring(ctx.read(rel))
        except Exception as e:
            raise RuntimeError(f"Could not parse flavor manifest {rel}: {e}") from e
        fm_app = fm_root.find("application")
        if fm_app is None:
            continue
        fm_app.set(A + "label", "NOVA Scrob")
        fm_app.set(A + "icon", "@mipmap/nova_scrob_icon")
        fm_app.set(A + "roundIcon", "@mipmap/nova_scrob_icon")
        ctx.write(rel, ET.tostring(fm_root, encoding="unicode"))

    ctx.copy_asset("branding/nova_scrob_icon.png", "Video/res/mipmap-nodpi/nova_scrob_icon.png")
    ctx.copy_asset("branding/nova_scrob_foreground.png", "Video/res/drawable-nodpi/nova_scrob_foreground.png")
    ctx.install_template("Video/res/drawable/nova_scrob_icon_background.xml")
    ctx.install_template("Video/res/mipmap-anydpi-v26/nova_scrob_icon.xml")

    for rel in ("Video/res/xml/file_paths.xml", "Video/res/xml/provider_paths.xml"):
        if ctx.path(rel).exists():
            ctx.write(rel, ctx.read(rel).replace("org.courville.nova", app_id))
