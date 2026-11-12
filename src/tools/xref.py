"""Cross-reference helper for a 32-bit Windows exe.

Usage: uv run tools/xref.py EXE <query> [, <query> ...]   (several queries share one disassembly pass)

Queries (addresses in hex, without 0x):
  str <text>          VA of an ASCII string and the code that references it
  ref <va>            code that references a VA (immediate or memory displacement)
  dis <va> <count>    disassemble <count> instructions from <va>
  calls <va>          call/jmp sites of a function
  imm <hexvalue>      every instruction with that immediate, e.g. imm 400 for 1024
  data <va> <bytes>   raw bytes at a VA
"""

import sys

import capstone
import pefile

pe = pefile.PE(sys.argv[1])
base = pe.OPTIONAL_HEADER.ImageBase
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
iat = {}
for imp in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
    for i in imp.imports:
        iat[i.address] = f"{imp.dll.decode()}!{i.name.decode() if i.name else i.ordinal}"

text = next(s for s in pe.sections if s.Characteristics & 0x20000000)
code = text.get_data()
code_va = base + text.VirtualAddress
_cache = None


def all_ins():
    global _cache
    if _cache is None:
        _cache = [i for i in md.disasm(code, code_va) if i.id != 0]
    return _cache


def cstr(va):
    try:
        rva = va - base
        sec = pe.get_section_by_rva(rva)
        if not sec or sec.Characteristics & 0x20000000:
            return None
        data = pe.get_data(rva, 80)
        end = data.find(b"\0")
        if end < 2:
            return None
        s = data[:end]
        if all(32 <= c < 127 for c in s):
            return s.decode()
    except Exception:
        return None
    return None


def fmt(i):
    s = f"{i.address:08x}: {i.mnemonic:6} {i.op_str}"
    if i.id == 0:  # bytes Capstone couldn't decode (skipped as data)
        return s
    for op in i.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.disp in iat:
            s += f"    ; {iat[op.mem.disp]}"
        if op.type == capstone.x86.X86_OP_IMM:
            st = cstr(op.imm & 0xFFFFFFFF)
            if st:
                s += f'    ; "{st}"'
    return s


def refs(va):
    out = []
    for i in all_ins():
        for op in i.operands:
            if (op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == va) or (
                    op.type == capstone.x86.X86_OP_MEM and (op.mem.disp & 0xFFFFFFFF) == va):
                out.append(i)
                break
    return out


def find_str(text):
    needle = text.encode() + b"\0"
    for s in pe.sections:
        data = s.get_data()
        pos = data.find(needle)
        while pos != -1:
            va = base + s.VirtualAddress + pos
            print(f"string at {va:08x}")
            for i in refs(va):
                print("  " + fmt(i))
            pos = data.find(needle, pos + 1)


def dis(va, n):
    off = va - code_va
    for k, i in enumerate(md.disasm(code[off:off + n * 16], va)):
        if k >= n:
            break
        print(fmt(i))


def run(argv):
    cmd = argv[0]
    if cmd == "str":
        find_str(argv[1])
    elif cmd == "ref":
        for i in refs(int(argv[1], 16)):
            print(fmt(i))
    elif cmd == "dis":
        dis(int(argv[1], 16), int(argv[2]))
    elif cmd == "calls":
        va = int(argv[1], 16)
        for i in all_ins():
            if i.mnemonic in ("call", "jmp") and i.operands and i.operands[0].type == capstone.x86.X86_OP_IMM \
                    and (i.operands[0].imm & 0xFFFFFFFF) == va:
                print(fmt(i))
    elif cmd == "imm":
        val = int(argv[1], 16)
        for i in all_ins():
            if any(op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == val for op in i.operands):
                print(fmt(i))
    elif cmd == "field":
        # struct field access: [reg + off], e.g. field 60; optional: only where an immediate shows up nearby
        off = int(argv[1], 16)
        near = int(argv[2], 16) if len(argv) > 2 else None
        ins = all_ins()
        for k, i in enumerate(ins):
            if any(op.type == capstone.x86.X86_OP_MEM and op.mem.base != 0 and op.mem.index == 0
                   and op.mem.disp == off for op in i.operands):
                if near is not None:
                    window = ins[max(0, k - 8): k + 9]
                    if not any(op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == near
                               for w in window for op in w.operands):
                        continue
                print(fmt(i))
    elif cmd == "data":
        va, n = int(argv[1], 16), int(argv[2])
        print(f"{va:08x}: {pe.get_data(va - base, n).hex(' ')}")
    else:
        sys.exit(f"unknown query: {cmd}")


groups, cur = [], []
for a in sys.argv[2:]:
    if a == ",":
        groups.append(cur)
        cur = []
    else:
        cur.append(a)
groups.append(cur)
for g in groups:
    print(f"### {' '.join(g)}")
    run(g)
