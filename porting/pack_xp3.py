"""Pack a resource directory into an unencrypted XP3 without changing inputs."""
import argparse
import json
from pathlib import Path
import struct
import zlib

MAGIC = b"XP3\r\n \n\x1a\x8bg\x01"


def block(tag, data):
    return tag + struct.pack("<Q", len(data)) + data


def pack(source, output):
    source, output = source.resolve(), output.resolve()
    if output == source or source in output.parents:
        raise ValueError("Output must be outside the input tree")
    files = sorted(p for p in source.rglob("*") if p.is_file())
    output.parent.mkdir(parents=True, exist_ok=True)
    index = bytearray()
    total = 0
    unique = {}
    unique_bytes = 0
    with output.open("xb") as dst:
        dst.write(MAGIC + bytes(8))
        for path in files:
            name = path.relative_to(source).as_posix().encode("utf-16le")
            stat = path.stat()
            identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns) if stat.st_ino else None
            if identity is not None and identity in unique:
                offset, size, checksum = unique[identity]
            else:
                offset, size, checksum = dst.tell(), 0, 1
                with path.open("rb") as src:
                    while data := src.read(4 * 1024 * 1024):
                        dst.write(data)
                        size += len(data)
                        checksum = zlib.adler32(data, checksum)
                if identity is not None:
                    unique[identity] = (offset, size, checksum)
                unique_bytes += size
            entry = block(b"info", struct.pack("<IQQH", 0, size, size, len(name) // 2) + name)
            entry += block(b"segm", struct.pack("<IQQQ", 0, offset, size, size))
            entry += block(b"adlr", struct.pack("<I", checksum))
            index.extend(block(b"File", entry))
            total += size
        offset = dst.tell()
        compressed = zlib.compress(index)
        dst.write(b"\x01" + struct.pack("<QQ", len(compressed), len(index)) + compressed)
        dst.seek(len(MAGIC))
        dst.write(struct.pack("<Q", offset))
    return {"files": len(files), "resource_bytes": total, "unique_bytes": unique_bytes, "archive_bytes": output.stat().st_size}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(pack(args.source, args.output)))
