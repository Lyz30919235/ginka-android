"""Restore resource leaf names referenced by converted PBD data, preserving inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("converted_pbd", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--name", action="append", default=[])
    parser.add_argument("--hints", type=Path, help="JSON list of script resource-name hints")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("Source and output must be separate trees")
    lookup = {}
    for path in source.rglob("*"):
        if path.is_file() and re.fullmatch(r"[0-9a-f]{64}", path.name):
            lookup.setdefault(path.name, []).append(path)
    names = set(args.name)
    if args.hints:
        names.update(json.loads(args.hints.read_text(encoding="utf-8")))
    for path in args.converted_pbd.rglob("*.tjs"):
        text = path.read_text(encoding="utf-16")
        for name in re.findall(r'"((?:\\.|[^"\\])*)"', text):
            if re.fullmatch(r"[\w./ -]{1,140}", name):
                names.add(name)
                stem, dot, extension = name.rpartition(".")
                if not dot:
                    stem, extension = name, ""
                for language in ("_cn", "_en", "_jp"):
                    names.add(stem + language + ("." + extension if dot else ""))
    added = []
    suffixes = ("", ".tlg", ".png", ".jpg", ".pbd", ".tjs", ".asd", ".ogg", ".tft", ".ttf", ".otf", ".amv", ".ks", ".scn", ".stand", ".sinfo", ".stage", ".wmv", ".bmp", ".wav", ".ogg.sli", ".psb", ".ajp", ".jpeg", ".txt", ".csv", ".json", ".ini")
    for hint in sorted(names):
        leaf = hint.lower().split("/")[-1]
        if leaf in ("", ".", ".."):
            continue
        # UI storage names are also derived by replacing .pimg with .pbd.
        # Accept a candidate only when its full name hashes to an input entry.
        stems = {leaf}
        if "." in leaf:
            stems.add(leaf.rsplit(".", 1)[0])
        for stem in sorted(stems):
            for suffix in suffixes:
                name = stem + suffix
                digest = hashlib.blake2s((name + "xp3hnp").encode("utf-16le")).hexdigest()
                for original in lookup.get(digest, []):
                    target = output / original.parent.relative_to(source) / name
                    if target.exists():
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.link(original, target)
                    added.append(str(target.relative_to(output)))
    args.report.write_text(json.dumps({"added": added, "hints": len(names)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"aliases_added": len(added)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
