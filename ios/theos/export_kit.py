"""Export arm64 inputs selected by the Apple linker for the WSL relink."""
import argparse
import os
import pathlib
import re
import shutil
import subprocess
import tarfile

Path = pathlib.Path


def output(*args):
    return subprocess.check_output(args, text=True)


def inputs(linkmap):
    for line in linkmap:
        if line.rstrip() == b"# Object files:":
            break
    for raw_line in linkmap:
        if raw_line.startswith(b"#"):
            break
        line = os.fsdecode(raw_line)
        match = re.match(r"^\[\s*\d+\]\s+(.+)$", line)
        if match:
            path = match[1].strip()
            if path.startswith("/"):
                yield Path(re.sub(r"(?:\[(?:arm64|\d+)\])?\([^()]+\)$", "", path))


def export(build, kit, archive):
    app = build / "Release-iphoneos/Kioku.app"
    binary = app / "Kioku"
    models = app / "app_packages/aqt/rwkv_inference"
    if not (models / "sm106/weights.f32.bin").is_file():
        raise RuntimeError("RWKV weights missing from device build")
    kit.mkdir()
    shutil.copytree(app, kit / "resources", symlinks=True,
                    ignore=lambda p, names: {"_CodeSignature", "embedded.mobileprovision"}
                    | ({"Kioku"} if Path(p) == app else set()))
    libs = kit / "link"
    libs.mkdir()
    flags = []
    entry = None
    linkage = ""
    with (build / "kioku-arm64.map").open("rb") as linkmap:
        paths = dict.fromkeys(inputs(linkmap))
    for index, path in enumerate(paths):
        if ".sdk/" in str(path):
            continue
        if path.name == "main.o" and "Kioku.build" in path.parts:
            symbols = output("nm", "-gjU", path).splitlines()
            candidates = [s[1:] for s in symbols if s in ("_qt_main", "_main", "__Z7qt_mainiPPc")]
            if len(candidates) != 1:
                raise RuntimeError(f"Unexpected launcher symbols in {path}: {candidates}")
            entry, = candidates
            if entry == "_Z7qt_mainiPPc":
                entry = "qt_main"
            elif entry != "main":
                linkage = "-DKIOKU_ENTRY_EXTERN_C"
            continue
        name = f"{index}{'.o' if path.suffix == '.o' else '.a'}"
        shutil.copyfile(path, libs / name)
        flags.append("kit/link/" + name)
    if entry is None:
        raise RuntimeError("Missing Kioku launcher in link map")
    for line in output("otool", "-L", binary).splitlines()[1:]:
        dep = line.strip().split(" (", 1)[0]
        if dep.startswith("/usr/lib/") and dep.endswith(".dylib"):
            name = dep.split("/lib")[-1].split(".")[0]
            if name != "System":
                flags.append("-l" + name)
        elif ".framework/" in dep:
            flags.extend(["-framework", dep.split(".framework/")[0].split("/")[-1]])
        else:
            raise RuntimeError(f"Unsupported runtime dependency {dep}")
    (kit / "link.rsp").write_text("\n".join(flags) + "\n")
    ios = Path(__file__).resolve().parents[1]
    headers = ios / "deps/python-ios/Python.xcframework/ios-arm64/include"
    header, = headers.glob("python*/Python.h")
    shutil.copytree(header.parent, kit / "include", symlinks=False)
    (kit / "config.mk").write_text(f"PY_VERSION := {header.parent.name[6:]}\nENTRY := {entry}\nENTRY_LINKAGE := {linkage}\n")
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(kit, arcname="kit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("build", "kit", "archive"):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()
    export(args.build.resolve(), args.kit, args.archive)
