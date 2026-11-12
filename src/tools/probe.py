"""Static probe of an old Win32 game exe: PE layout, imports, and hardcoded screen-size immediates."""

import sys
from collections import defaultdict

import capstone
import pefile

SIZES = {640, 480, 800, 600, 1024, 768, 1152, 864, 1280, 960, 720, 1600, 1200, 1920, 1080, 1360, 1366}
WIDTHS = {640, 800, 1024, 1152, 1280, 1600, 1920, 1360, 1366}
HEIGHTS = {480, 600, 768, 864, 960, 720, 1024, 1200, 1080}
MODES = {(640, 480), (800, 600), (1024, 768), (1152, 864), (1280, 960), (1280, 1024), (1600, 1200), (1280, 720),
         (1920, 1080), (1366, 768), (1360, 768)}


def main(path: str, mode: str = "all") -> None:
    pe = pefile.PE(path)
    base = pe.OPTIONAL_HEADER.ImageBase
    print(f"== {path}")
    print(f"machine={hex(pe.FILE_HEADER.Machine)} timestamp={pe.FILE_HEADER.TimeDateStamp} base={hex(base)} "
          f"entry={hex(base + pe.OPTIONAL_HEADER.AddressOfEntryPoint)}")
    for s in pe.sections:
        print(f"  section {s.Name.rstrip(b'\0').decode(errors='replace'):8} va={hex(base + s.VirtualAddress)} "
              f"vsize={hex(s.Misc_VirtualSize)} rawsize={hex(s.SizeOfRawData)} chars={hex(s.Characteristics)}")
    if hasattr(pe, "FileInfo"):
        for fi in pe.FileInfo:
            for entry in fi:
                for st in getattr(entry, "StringTable", []):
                    for k, v in st.entries.items():
                        print(f"  version {k.decode()}: {v.decode(errors='replace')}")

    iat = {}
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        for imp in pe.DIRECTORY_ENTRY_IMPORT:
            names = [(i.name.decode() if i.name else f"#{i.ordinal}") for i in imp.imports]
            for i in imp.imports:
                iat[i.address] = f"{imp.dll.decode()}!{i.name.decode() if i.name else i.ordinal}"
            if mode in ("all", "imports"):
                print(f"  import {imp.dll.decode()}: {len(names)} funcs")
                interesting = [n for n in names if any(k in n.lower() for k in (
                    "directdraw", "metrics", "createwindow", "displaysettings", "setwindowpos", "cursor",
                    "getprivateprofile", "clip", "adjustwindow", "movewindow", "getclientrect"))]
                if imp.dll.decode().lower() in ("ddraw.dll", "d3d8.dll", "d3d9.dll", "dsound.dll", "dinput.dll"):
                    interesting = names
                if interesting:
                    print("    " + ", ".join(interesting))
    if mode == "imports":
        return

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    hits = []
    iat_refs = defaultdict(list)
    for s in pe.sections:
        if not s.Characteristics & 0x20000000:  # IMAGE_SCN_MEM_EXECUTE
            continue
        code = s.get_data()
        start = base + s.VirtualAddress
        for ins in md.disasm(code, start):
            if ins.id == 0:
                continue
            for op in ins.operands:
                if op.type == capstone.x86.X86_OP_IMM and op.imm in SIZES:
                    hits.append((ins.address, ins.mnemonic, ins.op_str, op.imm))
                if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                    if op.mem.disp in iat:
                        iat_refs[iat[op.mem.disp]].append(ins.address)

    print(f"\n== size immediates in code: {len(hits)}")
    by_val = defaultdict(int)
    for h in hits:
        by_val[h[3]] += 1
    print("  counts: " + ", ".join(f"{k}:{v}" for k, v in sorted(by_val.items())))

    # Width/height pairs close to each other are the strongest resolution candidates.
    hits.sort()
    pairs = []
    for i, (a, mn, ops, v) in enumerate(hits):
        if v not in WIDTHS:
            continue
        for b, mn2, ops2, v2 in hits[max(0, i - 6): i + 7]:
            if 0 < abs(b - a) <= 48 and (v, v2) in MODES:
                pairs.append((a, v, b, v2))
    seen = set()
    print(f"\n== width/height pairs within 48 bytes:")
    for a, v, b, v2 in pairs:
        key = (min(a, b), max(a, b))
        if key in seen:
            continue
        seen.add(key)
        print(f"  {hex(a)} {v}  ~  {hex(b)} {v2}")

    if mode == "all":
        print("\n== all size immediates")
        for a, mn, ops, v in hits:
            print(f"  {hex(a)}: {mn} {ops}")

    print("\n== call sites of interesting imports")
    for name, refs in sorted(iat_refs.items()):
        if any(k in name.lower() for k in ("directdraw", "metrics", "createwindow", "displaysettings",
                                            "getprivateprofile", "clipcursor", "setwindowpos")):
            print(f"  {name}: {', '.join(hex(r) for r in refs[:12])}{' ...' if len(refs) > 12 else ''}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "all")
