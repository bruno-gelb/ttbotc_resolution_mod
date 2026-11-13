"""The music synthesizer's build pieces: the soundfont trimmer, the C core and the DLL.

The real soundfont is 148 MB and Tzar's music belongs to the game, so these use a tiny synthetic soundfont and MIDI
file. The C code is compiled with Zig from uv.lock (src/tools/build_music.py), here as on CI.
"""

import array
import math
import struct
import subprocess
import sys
from pathlib import Path

import pefile
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "tools"))
import build_music  # noqa: E402
import soundfont  # noqa: E402

RATE = 44100
GAME_IMPORTS = {
    "midiOutGetDevCapsA", "midiOutGetNumDevs", "midiOutGetVolume", "midiOutPrepareHeader", "midiOutReset",
    "midiOutSetVolume", "midiOutUnprepareHeader", "midiStreamClose", "midiStreamOpen", "midiStreamOut",
    "midiStreamPause", "midiStreamProperty", "midiStreamRestart", "midiStreamStop", "mciSendCommandA",
    "waveOutClose", "waveOutGetDevCapsA", "waveOutGetNumDevs", "waveOutGetPosition", "waveOutGetVolume",
    "waveOutOpen", "waveOutPrepareHeader", "waveOutReset", "waveOutSetVolume", "waveOutUnprepareHeader",
    "waveOutWrite",
}


def tone(seed: int, length: int = 4410) -> bytes:
    """A loopable tone, 100 samples a cycle (441 Hz), a little different per seed."""
    return array.array("h", [int(12000 * math.sin(2 * math.pi * i / 100) + seed) for i in range(length)]).tobytes()


def make_sf2(samples: list[tuple[bytes, int, int]],
             presets: list[tuple[int, int, list[tuple[int, int, int]]]]) -> bytes:
    """A SoundFont 2 file. samples: (16-bit data, sample type, link). presets: (bank, program, zones), a zone being
    (low key, high key, sample); each preset gets one instrument with those zones, after a global zone."""
    def chunk(cid, body):
        return cid + struct.pack("<I", len(body)) + body + (b"\0" if len(body) & 1 else b"")

    def lst(kind, parts):
        return chunk(b"LIST", kind + b"".join(parts))

    smpl, shdr = b"", []
    for i, (data, kind, link) in enumerate(samples):
        start = len(smpl) // 2
        end = start + len(data) // 2
        smpl += data + bytes(46 * 2)
        shdr.append(f"s{i}".encode().ljust(20, b"\0") + struct.pack("<IIIIIBbHH", start, end, start, end, RATE, 60, 0,
                                                                    link, kind))
    shdr.append(b"EOS".ljust(20, b"\0") + bytes(26))
    phdr, pbag, pgen, inst, ibag, igen = [], [], [], [], [], []
    for n, (bank, program, zones) in enumerate(presets):
        phdr.append(f"p{n}".encode().ljust(20, b"\0") + struct.pack("<HHHIII", program, bank, len(pbag), 0, 0, 0))
        pbag.append(struct.pack("<HH", len(pgen), 0))
        pgen.append(struct.pack("<HH", 48, 10))  # global zone: a little attenuation
        pbag.append(struct.pack("<HH", len(pgen), 0))
        pgen.append(struct.pack("<HH", 41, n))   # instrument n
        inst.append(f"i{n}".encode().ljust(20, b"\0") + struct.pack("<H", len(ibag)))
        ibag.append(struct.pack("<HH", len(igen), 0))
        igen.append(struct.pack("<HH", 54, 1))   # global zone: loop the samples
        for lo, hi, sample in zones:
            ibag.append(struct.pack("<HH", len(igen), 0))
            igen.append(struct.pack("<HH", 43, lo | hi << 8))
            igen.append(struct.pack("<HH", 53, sample))
    phdr.append(b"EOP".ljust(20, b"\0") + struct.pack("<HHHIII", 0, 0, len(pbag), 0, 0, 0))
    pbag.append(struct.pack("<HH", len(pgen), 0))
    pgen.append(bytes(4))
    inst.append(b"EOI".ljust(20, b"\0") + struct.pack("<H", len(ibag)))
    ibag.append(struct.pack("<HH", len(igen), 0))
    igen.append(bytes(4))
    info = lst(b"INFO", [chunk(b"ifil", struct.pack("<HH", 2, 1)), chunk(b"isng", b"EMU8000\0"),
                         chunk(b"INAM", b"test\0\0")])
    pdta = lst(b"pdta", [chunk(name, b"".join(records)) for name, records in [
        (b"phdr", phdr), (b"pbag", pbag), (b"pmod", [bytes(10)]), (b"pgen", pgen), (b"inst", inst),
        (b"ibag", ibag), (b"imod", [bytes(10)]), (b"igen", igen), (b"shdr", shdr)]])
    body = b"sfbk" + info + lst(b"sdta", [chunk(b"smpl", smpl)]) + pdta
    return b"RIFF" + struct.pack("<I", len(body)) + body


SAMPLES = [(tone(0), 1, 0), (tone(1), 4, 2), (tone(2), 2, 1), (tone(3), 1, 0),
           (tone(4, 800), 1, 0), (tone(5, 800), 1, 0), (tone(6, 800), 1, 0)]
PRESETS = [
    (0, 0, [(36, 59, 0), (60, 84, 1), (60, 84, 2)]),  # low notes, and a stereo pair for the high ones
    (0, 1, [(0, 127, 3)]),
    (128, 0, [(38, 38, 4), (40, 40, 5), (49, 49, 6)]),  # drums: one sample per note
]


def tables(data: bytes) -> dict[str, list[bytes]]:
    top = soundfont._chunks(data, 12, len(data))
    pdta = soundfont._chunks(data, *top[b"pdta"])
    return {name: soundfont._records(data, pdta[name.encode()], name) for name in soundfont.RECORD}


def sample_data(data: bytes, header: bytes) -> bytes:
    top = soundfont._chunks(data, 12, len(data))
    smpl = soundfont._chunks(data, *top[b"sdta"])[b"smpl"][0]
    start, end = struct.unpack_from("<II", header, 20)
    return data[smpl + start * 2:smpl + end * 2]


def test_trim_keeps_only_what_the_notes_need():
    full = make_sf2(SAMPLES, PRESETS)
    trimmed = soundfont.trim(full, {(0, 0): {60, 61}, (128, 0): {38}})
    assert [(bank, program) for bank, program, _ in soundfont.presets(trimmed)] == [(0, 0), (128, 0)]
    t = tables(trimmed)
    names = [h[:20].split(b"\0")[0] for h in t["shdr"]]
    assert names == [b"s1", b"s2", b"s4", b"EOS"]  # the stereo pair for notes 60-61 and the snare; not s0, s3, s5, s6
    for new, old in [(0, 1), (1, 2), (2, 4)]:
        assert sample_data(trimmed, t["shdr"][new]) == SAMPLES[old][0]
    links = [struct.unpack_from("<H", h, 42)[0] for h in t["shdr"][:2]]
    assert links == [1, 0]  # still each other's partners, at their new indexes
    assert len(t["inst"]) == 3 and len(t["phdr"]) == 3  # two of each, and the terminal records
    assert len(trimmed) < len(full)


def test_trim_refuses_presets_the_file_doesnt_have():
    with pytest.raises(soundfont.SoundFontError, match="not in the file"):
        soundfont.trim(make_sf2(SAMPLES, PRESETS), {(0, 5): None})


def midi_file() -> bytes:
    """Format 0, 480 ticks a quarter at 120 beats a minute: middle C from 1.0 s to 1.5 s."""
    track = (b"\x00\xff\x51\x03\x07\xa1\x20"   # tempo 500000 us a quarter
             b"\x00\xc0\x00"                    # program 0
             b"\x87\x40\x90\x3c\x64"            # 960 ticks later: note on
             b"\x83\x60\x80\x3c\x00"            # 480 ticks later: note off
             b"\x00\xff\x2f\x00")
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) + b"MTrk" + struct.pack(">I", len(track)) + track


@pytest.fixture(scope="module")
def render(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("native") / ("render.exe" if sys.platform == "win32" else "render")
    return build_music.build_render(out)


def test_the_core_plays_notes_on_time(render, tmp_path):
    sf2 = tmp_path / "test.sf2"
    sf2.write_bytes(soundfont.trim(make_sf2(SAMPLES, PRESETS), {(0, 0): set(range(36, 85))}))
    (tmp_path / "test.mid").write_bytes(midi_file())
    wav = tmp_path / "out.wav"
    result = subprocess.run([str(render), str(sf2), str(tmp_path / "test.mid"), str(wav), "3"],
                            capture_output=True, text=True, check=True)
    assert "buffers played" in result.stdout
    pcm = array.array("h")
    pcm.frombytes(wav.read_bytes()[44:])

    def loudest(start: float, end: float) -> int:
        return max((abs(v) for v in pcm[int(start * RATE) * 2:int(end * RATE) * 2]), default=0)

    assert loudest(0.0, 0.95) == 0     # nothing before the note
    assert loudest(1.05, 1.45) > 2000  # the note
    assert loudest(1.7, 3.0) < 50      # gone after its release (render stops writing once it's quiet)
    assert 1.5 < len(pcm) / 2 / RATE < 2.5


def test_the_dll_has_the_games_imports(tmp_path):
    dll = build_music.build_dll(tmp_path)
    pe = pefile.PE(str(dll))
    assert pe.FILE_HEADER.Machine == 0x14C  # 32-bit x86, like the game
    assert pe.DIRECTORY_ENTRY_EXPORT.name == b"TZMUS.dll"
    assert {e.name.decode() for e in pe.DIRECTORY_ENTRY_EXPORT.symbols} == GAME_IMPORTS
    assert {i.dll.decode().lower() for i in pe.DIRECTORY_ENTRY_IMPORT} >= {"kernel32.dll"}
    assert "winmm.dll" not in {i.dll.decode().lower() for i in pe.DIRECTORY_ENTRY_IMPORT}  # loaded by full path
