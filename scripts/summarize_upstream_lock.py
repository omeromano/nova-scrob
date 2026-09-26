#!/usr/bin/env python3
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Render a human-readable summary of a repo resolved manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--release", default="")
    parser.add_argument("--version", default="")
    parser.add_argument("--manifest-commit", default="")
    args = parser.parse_args()

    root = ET.parse(args.manifest).getroot()
    projects = []
    for project in root.findall("project"):
        path = project.get("path") or project.get("name") or ""
        name = project.get("name") or ""
        revision = project.get("revision") or ""
        projects.append((path, name, revision))

    if args.release:
        print(f"NOVA release: {args.release}")
    if args.version:
        print(f"Expected APK base version: {args.version}")
    if args.manifest_commit:
        print(f"aos-AVP release-tag commit: {args.manifest_commit}")
    print(f"Resolved projects: {len(projects)}")
    print()
    for path, name, revision in sorted(projects):
        print(f"{path}\t{name}\t{revision}")


if __name__ == "__main__":
    main()
