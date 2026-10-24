"""Assemble recovered archives and compatibility overlays without editing inputs."""
import argparse
import json
import os
from pathlib import Path


def assemble(recovered, overlays, plugins, output):
    roots = [recovered, *overlays]
    if any(output == p or p in output.parents or output in p.parents for p in roots):
        raise ValueError("Output must be separate from every input tree")
    output.mkdir(parents=True, exist_ok=False)
    files = 0
    for root in roots:
        for archive in root.iterdir():
            if not archive.is_dir() or archive.suffix != ".xp3":
                continue
            for source in archive.rglob("*"):
                if not source.is_file():
                    continue
                relative = source.relative_to(root)
                if relative.as_posix() == "data.xp3/startup.tjs":
                    continue
                target = output / relative
                if target.exists():
                    if not os.path.samefile(source, target):
                        raise ValueError(f"Conflicting overlay: {relative}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                os.link(source, target)
                files += 1
    if plugins:
        for source in plugins.glob("*.dll"):
            target = output / "data.xp3/plugin" / source.name.lower()
            target.parent.mkdir(parents=True, exist_ok=True)
            os.link(source, target)
            files += 1
    routes = []
    for archive in sorted(output.iterdir()):
        routes.append([archive.name, ""])
        for directory in sorted(p for p in archive.rglob("*") if p.is_dir()):
            routes.append([archive.name, directory.relative_to(archive).as_posix() + "/"])
    data = output / "data.xp3"
    (data / "ginka_paths.tjs").write_text("(" + json.dumps(routes, ensure_ascii=False) + ")", encoding="utf-16")
    source = Path(__file__).resolve().parent / "android/startup.tjs"
    (data / "startup.tjs").write_text(source.read_text(encoding="utf-8"), encoding="utf-16")
    return {"linked_files": files, "search_routes": len(routes), "archives": sorted(p.name for p in output.iterdir())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recovered", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--overlay", type=Path, action="append", default=[])
    parser.add_argument("--plugins", type=Path)
    args = parser.parse_args()
    print(json.dumps(assemble(args.recovered.resolve(), [p.resolve() for p in args.overlay],
                              args.plugins.resolve() if args.plugins else None, args.output.resolve())))
