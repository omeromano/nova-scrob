from pathlib import Path
import shutil


class PatchContext:
    """In-memory patch context.

    In dry-run mode all source edits happen in memory, so the same patch logic can be
    used as an upstream compatibility/preflight check without modifying the checkout.
    """

    def __init__(self, root, project_root, values, dry_run=False):
        self.root = Path(root).resolve()
        self.project_root = Path(project_root).resolve()
        self.values = dict(values)
        self.dry_run = dry_run
        self._text = {}
        self.changed = []

    def path(self, rel):
        return self.root / rel

    def require_file(self, rel):
        path = self.path(rel)
        if not path.is_file():
            raise RuntimeError(f"Required upstream file not found: {rel}")
        return path

    def read(self, rel):
        if rel in self._text:
            return self._text[rel]
        path = self.require_file(rel)
        text = path.read_text(encoding="utf-8")
        self._text[rel] = text
        return text

    def write(self, rel, text):
        self._text[rel] = text
        if rel not in self.changed:
            self.changed.append(rel)
        if not self.dry_run:
            path = self.path(rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def replace_once(self, rel, old, new, label=None):
        text = self.read(rel)
        count = text.count(old)
        if count != 1:
            name = label or rel
            preview = old[:120].replace("\n", "\\n")
            raise RuntimeError(
                f"{name}: expected one upstream anchor, found {count}: {preview!r}"
            )
        self.write(rel, text.replace(old, new, 1))

    def render(self, text):
        for key, value in self.values.items():
            text = text.replace("{{" + key + "}}", value)
        return text

    def install_template(self, rel):
        src = self.project_root / "scripts" / "templates" / rel
        if not src.is_file():
            raise RuntimeError(f"Patch template not found: {src}")
        self.write(rel, self.render(src.read_text(encoding="utf-8")))

    def copy_asset(self, source_rel, target_rel):
        src = self.project_root / source_rel
        if not src.is_file():
            raise RuntimeError(f"Required project asset not found: {source_rel}")
        if target_rel not in self.changed:
            self.changed.append(target_rel)
        if not self.dry_run:
            dst = self.path(target_rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

    def result_text(self, rel):
        return self.read(rel)
