#!/usr/bin/env python3
import argparse
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def run(cmd, *, cwd=None, capture=False):
    kwargs = {
        "cwd": cwd,
        "check": True,
        "text": True,
    }
    if capture:
        kwargs["stdout"] = subprocess.PIPE
    subprocess.run(cmd, **kwargs)


def capture(cmd, *, cwd=None):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def parse_manifest(path: Path):
    root = ET.parse(path).getroot()
    projects = []
    for node in root.findall("project"):
        name = node.get("name") or ""
        project_path = node.get("path") or name
        revision = node.get("revision") or ""
        if not name or not project_path or not revision:
            raise RuntimeError(f"Incomplete project entry in {path}: name={name!r} path={project_path!r} revision={revision!r}")
        if not SHA_RE.fullmatch(revision):
            raise RuntimeError(
                f"Release manifest is not fully resolved: {project_path} has non-SHA revision {revision!r}"
            )
        copyfiles = []
        for copy_node in node.findall("copyfile"):
            src = copy_node.get("src") or ""
            dest = copy_node.get("dest") or ""
            if not src or not dest:
                raise RuntimeError(f"Invalid copyfile entry for {project_path}")
            copyfiles.append((src, dest))
        projects.append(
            {
                "name": name,
                "path": project_path,
                "revision": revision.lower(),
                "copyfiles": copyfiles,
            }
        )
    if not projects:
        raise RuntimeError(f"No projects found in {path}")
    return projects


def clone_project(project, dest_root: Path, base_url: str):
    path = dest_root / project["path"]
    url = f"{base_url.rstrip('/')}/{project['name']}.git"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)

    run(["git", "init", "-q"], cwd=path)
    run(["git", "remote", "add", "origin", url], cwd=path)
    try:
        run(["git", "fetch", "--depth=1", "origin", project["revision"]], cwd=path)
    except subprocess.CalledProcessError:
        # Some servers do not allow direct fetch-by-SHA. Fall back to fetching
        # all advertised heads/tags shallowly enough for Git to locate it.
        run(["git", "fetch", "origin", "+refs/heads/*:refs/remotes/origin/*", "+refs/tags/*:refs/tags/*"], cwd=path)
    run(["git", "checkout", "-q", "--detach", project["revision"]], cwd=path)
    actual = capture(["git", "rev-parse", "HEAD"], cwd=path).lower()
    if actual != project["revision"]:
        raise RuntimeError(f"Revision mismatch for {project['path']}: expected {project['revision']}, got {actual}")
    return project["path"], actual


def main():
    parser = argparse.ArgumentParser(description="Materialize a NOVA resolved release manifest at exact project SHAs.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("dest", type=Path)
    parser.add_argument("--base-url", default="https://github.com/nova-video-player")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()

    projects = parse_manifest(args.manifest)

    avp = next((p for p in projects if p["path"] == "AVP" or p["name"] == "aos-AVP"), None)
    if avp is None:
        raise RuntimeError("Resolved release manifest does not contain the AVP project")
    if args.dest.exists():
        shutil.rmtree(args.dest)
    args.dest.mkdir(parents=True)

    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        future_map = {
            pool.submit(clone_project, project, args.dest, args.base_url): project
            for project in projects
        }
        for future in concurrent.futures.as_completed(future_map):
            project = future_map[future]
            try:
                path, revision = future.result()
                print(f"resolved {path}: {revision}", flush=True)
            except Exception as exc:
                failures.append((project["path"], exc))
                print(f"ERROR resolving {project['path']}: {exc}", file=sys.stderr, flush=True)

    if failures:
        details = "; ".join(f"{path}: {exc}" for path, exc in failures)
        raise RuntimeError(f"Failed to materialize {len(failures)} project(s): {details}")

    for project in projects:
        project_root = args.dest / project["path"]
        for src, dest in project["copyfiles"]:
            source = project_root / src
            target = args.dest / dest
            if not source.is_file():
                raise RuntimeError(f"copyfile source does not exist: {project['path']}/{src}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    print(f"Materialized {len(projects)} NOVA projects from resolved release manifest.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"NOVA release source error: {exc}", file=sys.stderr)
        sys.exit(1)
