"""Build the dedicated offline GINKA launcher from the pinned Android runtime.

All intermediates, signing material and final binaries belong in ignored trees.
Compile-only Java declarations and native import stubs are never packaged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

RUNTIME_SHA256 = "443be0d4d76c5026c7980eb625bef482c7c43275b3176bc2b6b7399c5755f497"
ANDROID = "http://schemas.android.com/apk/res/android"
TARGETS = {"armeabi-v7a": "armv7-linux-androideabi", "arm64-v8a": "aarch64-linux-android"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("runtime", "apktool", "sdk", "java-home", "rust", "work", "output", "signing-dir"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--build-tools", default="35.0.1")
    p.add_argument("--android-api", default="35")
    p.add_argument("--abis", nargs="+", choices=TARGETS, default=list(TARGETS))
    p.add_argument("--version-name", default="0.1.0")
    p.add_argument("--version-code", type=int, default=1)
    args = p.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    if args.output.exists():
        raise FileExistsError(args.output)
    if hashlib.file_digest(args.runtime.open("rb"), "sha256").hexdigest() != RUNTIME_SHA256:
        raise ValueError("Runtime hash differs from the reviewed v1.4.4 artifact")
    source = Path(__file__).resolve().parent / "android"
    work = args.work.resolve()
    java = args.java_home / "bin/java.exe"
    tools = args.sdk / "build-tools" / args.build_tools
    android_jar = args.sdk / "platforms" / ("android-" + args.android_api) / "android.jar"
    env = os.environ.copy()

    def run(command, name):
        result = subprocess.run([str(x) for x in command], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (work / (name + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"{name} failed ({result.returncode}); see its log")
        print(name + ": OK", flush=True)

    decoded = work / "decoded"
    run([java, "-jar", args.apktool, "d", "-s", args.runtime, "-o", decoded], "decode")
    ET.register_namespace("android", ANDROID)
    manifest = decoded / "AndroidManifest.xml"
    xml = ET.parse(manifest)
    root = xml.getroot()
    root.set("package", "org.ginka.launcher")
    for element in root.iter():
        for key, value in list(element.attrib.items()):
            if "org.github.krkr2.DYNAMIC_RECEIVER" in value or value == "org.github.krkr2.androidx-startup":
                element.set(key, value.replace("org.github.krkr2", "org.ginka.launcher"))
    for permission in root.findall("uses-permission"):
        if permission.get(f"{{{ANDROID}}}name") == "android.permission.INTERNET":
            root.remove(permission)
    application = root.find("application")
    application.set(f"{{{ANDROID}}}label", "GINKA")
    application.set(f"{{{ANDROID}}}extractNativeLibs", "true")
    application.set(f"{{{ANDROID}}}allowBackup", "false")
    activity = application.find("activity")
    activity.set(f"{{{ANDROID}}}name", "org.ginka.launcher.GameActivity")
    xml.write(manifest, encoding="utf-8", xml_declaration=True)
    config = decoded / "apktool.yml"
    settings = config.read_text(encoding="utf-8")
    settings = re.sub(r"(?m)^  versionCode:.*$", "  versionCode: " + str(args.version_code), settings)
    settings = re.sub(r"(?m)^  versionName:.*$", "  versionName: " + args.version_name, settings)
    config.write_text(settings, encoding="utf-8")

    classes = work / "classes"
    classes.mkdir()
    javac_sources = sorted((source / "java").rglob("*.java")) + sorted((source / "compile-stubs").rglob("*.java"))
    run([args.java_home / "bin/javac.exe", "--release", "8", "-encoding", "UTF-8", "-classpath", android_jar,
         "-d", classes, *javac_sources], "javac")
    dex = work / "dex"
    dex.mkdir()
    # Deliberately select only our launcher package; the runtime supplies the stubs.
    own_classes = sorted((classes / "org/ginka/launcher").rglob("*.class"))
    run([java, "-cp", tools / "lib/d8.jar", "com.android.tools.r8.D8", "--min-api", "29", "--lib", android_jar,
         "--output", dex, *own_classes], "dex")
    number = 2
    while (decoded / f"classes{number}.dex").exists():
        number += 1
    shutil.copy2(dex / "classes.dex", decoded / f"classes{number}.dex")

    rustc = args.rust / "bin/rustc.exe"
    linker = args.rust / "lib/rustlib/x86_64-pc-windows-gnu/bin/gcc-ld/ld.lld.exe"
    for abi, target in TARGETS.items():
        destination = decoded / "lib" / abi
        if abi not in args.abis:
            # This only removes the verified copied runtime directory in this build.
            if destination.resolve().parent != (decoded / "lib").resolve():
                raise ValueError("Unexpected ABI destination")
            shutil.rmtree(destination)
            continue
        native = work / abi
        native.mkdir()
        common = [rustc, "--edition=2024", "--crate-type=cdylib", "--target", target, "-C", "panic=abort",
                  "-C", "opt-level=s", "-C", f"linker={linker}", "-C", "linker-flavor=ld"]
        for library, cfg in (("dl", "dl_stub"), ("c", "c_stub")):
            run([*common, "--cfg", cfg, "-C", f"link-arg=-soname=lib{library}.so", source / "native/link_stubs.rs",
                 "-o", native / f"lib{library}.so"], f"{abi}-stub-{library}")
        run([*common, "-C", "link-arg=-zmax-page-size=16384", "-L", f"native={native}", source / "native/launcher.rs",
             "-o", native / "libginkalaunch.so"], f"{abi}-launcher")
        shutil.copy2(native / "libginkalaunch.so", destination / "libginkalaunch.so")

    unsigned = work / "unsigned.apk"
    run([java, "-jar", args.apktool, "b", decoded, "-o", unsigned], "apktool-build")
    with zipfile.ZipFile(unsigned) as archive:
        forbidden = [n for n in archive.namelist() if n.endswith(("/libc.so", "/libdl.so"))]
        if forbidden:
            raise ValueError(f"Link-only stubs in APK: {forbidden}")
        native_files = sorted(n for n in archive.namelist() if n.startswith("lib/"))
    aligned = work / "aligned.apk"
    run([tools / "zipalign.exe", "-P", "16", "4", unsigned, aligned], "zipalign")
    args.signing_dir.mkdir(parents=True, exist_ok=True)
    password_file = args.signing_dir / "password.txt"
    key = args.signing_dir / "ginka-local.p12"
    if key.exists() and not password_file.exists():
        raise ValueError("Signing key exists without its local password file")
    if not password_file.exists():
        password_file.write_text(secrets.token_urlsafe(36), encoding="ascii")
    env["GINKA_STOREPASS"] = password_file.read_text(encoding="ascii").strip()
    if not key.exists():
        run([args.java_home / "bin/keytool.exe", "-genkeypair", "-keystore", key, "-storetype", "PKCS12", "-alias", "ginka-local",
             "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-dname", "CN=GINKA Local Build",
             "-storepass:env", "GINKA_STOREPASS", "-keypass:env", "GINKA_STOREPASS"], "key-generation")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    run([java, "-jar", tools / "lib/apksigner.jar", "sign", "--ks", key, "--ks-key-alias", "ginka-local",
         "--ks-pass", "env:GINKA_STOREPASS", "--key-pass", "env:GINKA_STOREPASS", "--out", args.output, aligned], "sign")
    run([java, "-jar", tools / "lib/apksigner.jar", "verify", "--verbose", args.output], "verify-signature")
    report = {"runtime_sha256": RUNTIME_SHA256, "abis": args.abis, "native_files": native_files,
              "apk_bytes": args.output.stat().st_size,
              "apk_sha256": hashlib.file_digest(args.output.open("rb"), "sha256").hexdigest()}
    (work / "build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
