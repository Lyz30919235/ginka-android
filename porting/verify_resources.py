"""Independently verify plain XP3 indexes, shared data segments and bundle hashes."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import zlib

MAGIC = b"XP3\r\n \n\x1a\x8bg\x01"


def blocks(data):
    cursor = 0
    while cursor < len(data):
        if cursor + 12 > len(data):
            raise ValueError("Truncated XP3 block header")
        tag = data[cursor:cursor + 4]
        length = struct.unpack_from("<Q", data, cursor + 4)[0]
        cursor += 12
        if length > len(data) - cursor:
            raise ValueError("XP3 block exceeds its container")
        yield tag, data[cursor:cursor + length]
        cursor += length


def verify(path, expected):
    with path.open("rb") as stream:
        if stream.read(11) != MAGIC:
            raise ValueError("Invalid XP3 header")
        index_offset = struct.unpack("<Q", stream.read(8))[0]
        stream.seek(index_offset)
        if stream.read(1) != b"\x01":
            raise ValueError("Unexpected index encoding")
        compressed, raw = struct.unpack("<QQ", stream.read(16))
        if raw > 128 * 1024 * 1024 or index_offset + 17 + compressed != path.stat().st_size:
            raise ValueError("Invalid XP3 index bounds")
        index = zlib.decompress(stream.read(compressed))
        if len(index) != raw:
            raise ValueError("XP3 index length mismatch")
        names, unique = set(), {}
        total = 0
        for tag, entry in blocks(index):
            if tag != b"File":
                raise ValueError("Unexpected top-level XP3 chunk")
            fields = dict(blocks(entry))
            flags, original, archived, characters = struct.unpack_from("<IQQH", fields[b"info"])
            name_bytes = fields[b"info"][22:]
            if len(name_bytes) != characters * 2 or flags or original != archived:
                raise ValueError("Invalid plain-file metadata")
            name = name_bytes.decode("utf-16le")
            relative = PurePosixPath(name)
            if relative.is_absolute() or ".." in relative.parts or name.lower() in names:
                raise ValueError("Invalid or duplicate archive path")
            names.add(name.lower())
            method, offset, stored, expanded = struct.unpack("<IQQQ", fields[b"segm"])
            if method or stored != expanded or expanded != original or offset < 19 or offset + stored > index_offset:
                raise ValueError("Invalid plain data segment")
            checksum = struct.unpack("<I", fields[b"adlr"])[0]
            identity = (offset, stored)
            if identity not in unique:
                stream.seek(offset)
                remaining, adler = stored, 1
                while remaining:
                    data = stream.read(min(4 * 1024 * 1024, remaining))
                    if not data:
                        raise ValueError("Truncated archive data")
                    adler = zlib.adler32(data, adler)
                    remaining -= len(data)
                unique[identity] = adler
            if unique[identity] != checksum:
                raise ValueError("Resource Adler-32 mismatch: " + name)
            total += original
        stream.seek(0)
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != expected["sha256"] or len(names) != expected["files"] or total != expected["resource_bytes"]:
        raise ValueError("Resource manifest mismatch")
    return {"files": len(names), "unique_segments": len(unique), "archive_bytes": path.stat().st_size, "sha256": digest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--archive", help="Verify one changed archive and update the existing report")
    args = parser.parse_args()
    manifest = json.loads((args.bundle / "resource-manifest.json").read_text(encoding="utf-8"))
    if args.archive:
        if args.archive not in manifest:
            raise ValueError("Archive not present in manifest")
        selected = {args.archive: manifest[args.archive]}
        results = json.loads(args.report.read_text(encoding="utf-8")) if args.report.exists() else {}
    else:
        selected, results = manifest, {}
    for name, expected in selected.items():
        if Path(name).name != name or not name.endswith(".xp3"):
            raise ValueError("Invalid manifest entry")
        results[name] = verify(args.bundle / name, expected)
        print(json.dumps({"archive": name, **results[name]}), flush=True)
    args.report.write_text(json.dumps(results, indent=2), encoding="utf-8")
