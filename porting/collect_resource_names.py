"""Collect resource-name hints from selected script metadata, without running it."""
import argparse
import json
from pathlib import Path
import re
import struct
import sys
import zlib


def psb_strings(data):
    """Read the PSB string table only; do not interpret scenario instructions."""
    if data.startswith(b"mdf\0"):
        expected = struct.unpack_from("<I", data, 4)[0]
        data = zlib.decompress(data[8:])
        if len(data) != expected:
            raise ValueError("MDF length mismatch")
    if not data.startswith(b"PSB\0"):
        return []
    offset, base = struct.unpack_from("<II", data, 16)
    count_size = data[offset] - 0x0c
    if not 1 <= count_size <= 8:
        raise ValueError("Invalid PSB string-array count")
    count = int.from_bytes(data[offset + 1:offset + 1 + count_size], "little")
    entry_size = data[offset + 1 + count_size] - 0x0c
    position = offset + 2 + count_size
    if count > 1000000 or not 1 <= entry_size <= 4 or position + count * entry_size > len(data):
        raise ValueError("Invalid PSB string-array bounds")
    out = []
    for index in range(count):
        start = position + index * entry_size
        relative = int.from_bytes(data[start:start + entry_size], "little")
        absolute = base + relative
        end = data.find(b"\0", absolute)
        if not 0 <= absolute <= end < len(data):
            raise ValueError("Invalid PSB string offset")
        out.append(data[absolute:end].decode("utf-8"))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decompiler", type=Path, required=True)
    parser.add_argument("--psb-root", type=Path, action="append", default=[], help="Explicit dependency scope for unnamed PSB/script metadata")
    args = parser.parse_args()
    sys.path.insert(0, str(args.decompiler.resolve()))
    from tjs2_decompiler import BytecodeLoader

    hints = set()
    scripts = 0
    failed = []
    unnamed = []
    for folder in args.psb_root:
        for path in folder.rglob("*"):
            if path.is_file() and not path.suffix:
                with path.open("rb") as stream:
                    head = stream.read(8)
                if head.startswith((b"PSB\0", b"mdf\0", b"TJS2100\0", b"\xff\xfe")):
                    unnamed.append(path)
    # Scope is script dependencies only; image, audio and video bodies are skipped.
    named = (p for p in args.source.rglob("*") if p.suffix.lower() in (".tjs", ".ks", ".txt", ".csv", ".stand", ".sinfo", ".stage"))
    for path in [*named, *unnamed]:
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if raw.startswith((b"PSB\0", b"mdf\0")):
            strings = psb_strings(raw)
        elif raw.startswith(b"TJS2100\0"):
            loader = BytecodeLoader(raw)
            if not loader.load():
                failed.append(str(path.relative_to(args.source)))
                continue
            strings = loader.string_array
        else:
            encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8"
            text = raw.decode(encoding, errors="replace")
            strings = re.findall(r'''[\w./ -]{1,140}(?:\.[a-zA-Z0-9]{2,5})?''', text)
            strings += re.findall(r'''["']([^"'\n]{1,140})["']''', text)
        scripts += 1
        for value in strings:
            for name in (value, *re.findall(r"[\w./-]+\.[a-zA-Z0-9]{2,5}", value)):
                if not re.fullmatch(r"[\w./ -]{1,140}", name):
                    continue
                leaf = name.rsplit("/", 1)[-1].strip()
                if not leaf or leaf in (".", ".."):
                    continue
                hints.add(leaf)
                stem, dot, extension = leaf.rpartition(".")
                if not dot:
                    stem, extension = leaf, ""
                for language in ("_cn", "_en", "_jp", "_sc"):
                    hints.add(stem + language + ("." + extension if dot else ""))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(sorted(hints), ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"script_files": scripts, "hints": len(hints), "unparsed_scripts": failed}, ensure_ascii=False))


if __name__ == "__main__":
    main()
