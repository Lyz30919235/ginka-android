"""Pack a prepared resource tree and record checksums for the separate bundle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from pack_xp3 import pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--archive", help="Rebuild one prepared archive in an existing bundle")
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("Source and output must be separate trees")
    folders = sorted(p for p in source.iterdir() if p.is_dir() and p.suffix == ".xp3")
    if args.archive:
        folders = [p for p in folders if p.name == args.archive]
        if len(folders) != 1 or not output.is_dir():
            raise ValueError("Archive must name one existing prepared resource directory")
        report = json.loads((output / "resource-manifest.json").read_text(encoding="utf-8"))
    else:
        output.mkdir(parents=True, exist_ok=False)
        report = {}
    for folder in folders:
        target = output / folder.name
        pending = output / (folder.name + ".pending")
        stats = pack(folder, pending)
        with pending.open("rb") as stream:
            stats["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
        os.replace(pending, target)
        report[folder.name] = stats
        print(json.dumps({"archive": folder.name, **stats}), flush=True)
    # The supplied input has no optional append packs; configure an empty list.
    append = output / "append"
    append.mkdir(exist_ok=True)
    (append / "!appendlist.txt").write_text("# No optional append packs are configured.\n", encoding="utf-16")
    shutil.copyfile(Path(__file__).resolve().parent / "android/Kirikiroid2Preference.xml",
                    output / "Kirikiroid2Preference.xml")
    (output / "resource-manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
