"""Trim a SoundFont 2 file down to the presets a game uses.

A SoundFont is a RIFF file: sample data in sdta/smpl (16-bit, optionally sm24 for 24-bit), and in pdta nine tables
that point into each other by index: presets (phdr) have zones (pbag) with generators (pgen) and modulators (pmod);
a preset zone's instrument generator (41) points to an instrument (inst), whose zones (ibag) have generators (igen)
and modulators (imod); an instrument zone's sampleID generator (53) points to a sample header (shdr), which points
into the sample data, and to its stereo partner (sampleLink). Each table ends with a terminal record.

trim() keeps the chosen presets, the instruments they use and the samples those use, and rebuilds the indexes. Given
the notes each preset plays, it also drops the zones whose key range (generator 43) none of them reaches, at the
preset and the instrument level, with their samples. Global zones (the first zone, without an instrument or sample
generator) always stay.
"""

import struct
from dataclasses import dataclass

INSTRUMENT = 41  # preset generator: which instrument
KEY_RANGE = 43   # zone generator: low key in the low byte, high key in the high byte
SAMPLE_ID = 53   # instrument generator: which sample
ALL_NOTES = frozenset(range(128))
PADDING = 46     # zero sample points the SoundFont 2 spec asks for after each sample
ROM = 0x8000     # sampleType flag: the sample lives in a ROM, not in this file

RECORD = {"phdr": 38, "pbag": 4, "pmod": 10, "pgen": 4, "inst": 22, "ibag": 4, "imod": 10, "igen": 4, "shdr": 46}


class SoundFontError(Exception):
    pass


@dataclass
class Sample:
    raw: bytes  # the shdr record
    name: bytes
    start: int
    end: int
    loop_start: int
    loop_end: int
    link: int
    type: int


def _chunks(data: bytes, start: int, end: int) -> dict[bytes, tuple[int, int]]:
    """{chunk id or LIST type: (data start, data end)} for the chunks between start and end."""
    found = {}
    i = start
    while i + 8 <= end:
        cid, size = data[i:i + 4], struct.unpack_from("<I", data, i + 4)[0]
        body = i + 8
        if cid == b"LIST":
            found[data[body:body + 4]] = (body + 4, body + size)
        else:
            found[cid] = (body, body + size)
        i = body + size + (size & 1)
    return found


def _records(data: bytes, span: tuple[int, int], name: str) -> list[bytes]:
    size = RECORD[name]
    start, end = span
    if (end - start) % size:
        raise SoundFontError(f"{name} isn't a whole number of {size}-byte records")
    return [data[i:i + size] for i in range(start, end, size)]


def _u16(record: bytes, offset: int) -> int:
    return struct.unpack_from("<H", record, offset)[0]


def _chunk(cid: bytes, body: bytes) -> bytes:
    return cid + struct.pack("<I", len(body)) + body + (b"\0" if len(body) & 1 else b"")


def _list(kind: bytes, chunks: list[bytes]) -> bytes:
    return _chunk(b"LIST", kind + b"".join(chunks))


def presets(data: bytes) -> list[tuple[int, int, str]]:
    """(bank, program, name) of every preset."""
    top = _chunks(data, 12, len(data))
    pdta = _chunks(data, *top[b"pdta"])
    return [(_u16(r, 22), _u16(r, 20), r[:20].split(b"\0")[0].decode("latin-1"))
            for r in _records(data, pdta[b"phdr"], "phdr")[:-1]]


def trim(data: bytes, keep: dict[tuple[int, int], set[int] | None]) -> bytes:
    """data with only the presets whose (bank, program) is in keep, and what they need to play the notes keep maps
    them to (None: every note)."""
    if data[:4] != b"RIFF" or data[8:12] != b"sfbk":
        raise SoundFontError("not a SoundFont 2 file")
    top = _chunks(data, 12, len(data))
    for kind in (b"INFO", b"sdta", b"pdta"):
        if kind not in top:
            raise SoundFontError(f"no {kind.decode()} list")
    sdta = _chunks(data, *top[b"sdta"])
    pdta = _chunks(data, *top[b"pdta"])
    t = {name: _records(data, pdta[name.encode()], name) for name in RECORD}
    smpl_start, _ = sdta[b"smpl"]
    sm24 = sdta.get(b"sm24")

    phdr = t["phdr"]
    chosen = [p for p in range(len(phdr) - 1) if (_u16(phdr[p], 22), _u16(phdr[p], 20)) in keep]
    missing = set(keep) - {(_u16(phdr[p], 22), _u16(phdr[p], 20)) for p in chosen}
    if missing:
        raise SoundFontError(f"presets not in the file (bank, program): {sorted(missing)}")

    def zones(headers, bags, at: int, p: int):
        """(bag, gens range, mods range) of header p's zones."""
        for b in range(_u16(headers[p], at), _u16(headers[p + 1], at)):
            yield b, (_u16(bags[b], 0), _u16(bags[b + 1], 0)), (_u16(bags[b], 2), _u16(bags[b + 1], 2))

    def zone(gens_table, gens, link_oper) -> tuple[frozenset[int], int | None]:
        """(keys the zone covers, the index its link generator points to, or None for a global zone)."""
        keys, link = ALL_NOTES, None
        for g in range(*gens):
            oper, amount = _u16(gens_table[g], 0), _u16(gens_table[g], 2)
            if oper == KEY_RANGE:
                keys = frozenset(range(amount & 0xFF, (amount >> 8) + 1))
            elif oper == link_oper:
                link = amount
        return keys, link

    # what the chosen presets need: preset zones the notes reach, their instruments, and the notes reaching each
    kept_pbags, instrument_notes = set(), {}
    for p in chosen:
        notes = keep[(_u16(phdr[p], 22), _u16(phdr[p], 20))]
        notes = ALL_NOTES if notes is None else frozenset(notes)
        for b, gens, _ in zones(phdr, t["pbag"], 24, p):
            keys, instrument = zone(t["pgen"], gens, INSTRUMENT)
            reached = keys & notes
            if instrument is None or reached:
                kept_pbags.add(b)
            if instrument is not None and reached:
                instrument_notes[instrument] = instrument_notes.get(instrument, frozenset()) | reached
    instruments = sorted(instrument_notes)
    kept_ibags, samples = set(), set()
    for i in instruments:
        for b, gens, _ in zones(t["inst"], t["ibag"], 20, i):
            keys, sample = zone(t["igen"], gens, SAMPLE_ID)
            if sample is None or keys & instrument_notes[i]:
                kept_ibags.add(b)
                if sample is not None:
                    samples.add(sample)
    headers = [Sample(r, r[:20], *struct.unpack_from("<IIII", r, 20), *struct.unpack_from("<HH", r, 42))
               for r in t["shdr"][:-1]]
    todo = list(samples)
    while todo:  # stereo partners, which may point further
        s = todo.pop()
        if headers[s].type & 0x0E and headers[s].link not in samples and headers[s].link < len(headers):
            samples.add(headers[s].link)
            todo.append(headers[s].link)
    samples = sorted(samples)
    new_instrument = {old: new for new, old in enumerate(instruments)}
    new_sample = {old: new for new, old in enumerate(samples)}

    # sample data and headers
    smpl, s24, shdr = bytearray(), bytearray(), []
    for old in samples:
        h = headers[old]
        if h.type & ROM:
            raise SoundFontError(f"sample {h.name!r} is in a ROM")
        lo, hi = min(h.start, h.loop_start), max(h.end, h.loop_end)
        base = len(smpl) // 2 - lo
        smpl += data[smpl_start + lo * 2:smpl_start + hi * 2] + bytes(PADDING * 2)
        if sm24:
            s24 += data[sm24[0] + lo:sm24[0] + hi] + bytes(PADDING)
        link = new_sample.get(h.link, 0)
        shdr.append(h.raw[:20] + struct.pack("<IIII", h.start + base, h.end + base, h.loop_start + base,
                                             h.loop_end + base) + h.raw[36:42] + struct.pack("<HH", link, h.type))
    shdr.append(t["shdr"][-1])

    def rebuild(headers, bags, gens, mods, at: int, keep_headers, kept_bags, link_oper, remap):
        """New (headers, bags, gens, mods) with only the kept zones, and link_oper generators' amounts remapped."""
        nh, nb, ng, nm = [], [], [], []
        for h in keep_headers:
            nh.append(headers[h][:at] + struct.pack("<H", len(nb)) + headers[h][at + 2:])
            for b, (g0, g1), (m0, m1) in zones(headers, bags, at, h):
                if b not in kept_bags:
                    continue
                nb.append(struct.pack("<HH", len(ng), len(nm)))
                for g in range(g0, g1):
                    oper, amount = _u16(gens[g], 0), _u16(gens[g], 2)
                    ng.append(struct.pack("<HH", oper, remap[amount]) if oper == link_oper else gens[g])
                nm.extend(mods[m0:m1])
        terminal = headers[-1]
        nh.append(terminal[:at] + struct.pack("<H", len(nb)) + terminal[at + 2:])
        nb.append(struct.pack("<HH", len(ng), len(nm)))
        ng.append(gens[-1])
        nm.append(mods[-1])
        return nh, nb, ng, nm

    p_h, p_b, p_g, p_m = rebuild(phdr, t["pbag"], t["pgen"], t["pmod"], 24, chosen, kept_pbags, INSTRUMENT,
                                 new_instrument)
    i_h, i_b, i_g, i_m = rebuild(t["inst"], t["ibag"], t["igen"], t["imod"], 20, instruments, kept_ibags, SAMPLE_ID,
                                 new_sample)

    info = _chunk(b"LIST", data[top[b"INFO"][0] - 4:top[b"INFO"][1]])
    sdta_out = _list(b"sdta", [_chunk(b"smpl", bytes(smpl))] + ([_chunk(b"sm24", bytes(s24))] if sm24 else []))
    pdta_out = _list(b"pdta", [_chunk(name.encode(), b"".join(records)) for name, records in [
        ("phdr", p_h), ("pbag", p_b), ("pmod", p_m), ("pgen", p_g),
        ("inst", i_h), ("ibag", i_b), ("imod", i_m), ("igen", i_g), ("shdr", shdr)]])
    body = b"sfbk" + info + sdta_out + pdta_out
    return b"RIFF" + struct.pack("<I", len(body)) + body
