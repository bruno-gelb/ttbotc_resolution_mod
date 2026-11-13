/* TZMUS.dll: the winmm functions Tzar imports, with a built-in MIDI synthesizer, for Linux.
 *
 * Under Wine, winmm sends MIDI to whatever synthesizer Linux has, and a desktop usually has none, so Tzar's music is
 * silent. The mod renames WINMM.dll to TZMUS.dll in the exe's import table (exe_patch.MUSIC_PATCH), so the game loads
 * this DLL instead, and nothing else in the process does. It plays the game's midiStream buffers through core.c
 * (TinySoundFont, with TZMUS.sf2 from the game folder) into the real winmm's wave output, and passes the game's wave
 * and MCI calls on to the real winmm unchanged.
 *
 * Exported under winmm's names by tzmus.def. Built by src/tools/build_music.py.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mmsystem.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#include "core.h"

#define RATE 44100
#define WAVE_BUFFERS 4
#define WAVE_FRAMES 1024           /* 23 ms each */
#define MAGIC 0x53554D5Au          /* "ZMUS" */
#define MAX_PENDING 128            /* callbacks waiting to be delivered */

/* --- the real winmm ------------------------------------------------------------------------------------------- */

static HMODULE real;
static CRITICAL_SECTION init_lock;

#define REAL(name) static FARPROC p_##name
REAL(waveOutOpen); REAL(waveOutClose); REAL(waveOutWrite); REAL(waveOutReset); REAL(waveOutPrepareHeader);
REAL(waveOutUnprepareHeader); REAL(waveOutGetNumDevs); REAL(waveOutGetDevCapsA); REAL(waveOutGetVolume);
REAL(waveOutSetVolume); REAL(waveOutGetPosition); REAL(mciSendCommandA);

static int load_real(void) {
    char path[MAX_PATH];
    UINT n;
    EnterCriticalSection(&init_lock);
    if (!real) {
        n = GetSystemDirectoryA(path, MAX_PATH - 12);
        if (n && n < MAX_PATH - 12) {
            strcpy(path + n, "\\winmm.dll");
            real = LoadLibraryA(path);
        }
        if (real) {
#define LOAD(name) p_##name = GetProcAddress(real, #name)
            LOAD(waveOutOpen); LOAD(waveOutClose); LOAD(waveOutWrite); LOAD(waveOutReset);
            LOAD(waveOutPrepareHeader); LOAD(waveOutUnprepareHeader); LOAD(waveOutGetNumDevs);
            LOAD(waveOutGetDevCapsA); LOAD(waveOutGetVolume); LOAD(waveOutSetVolume); LOAD(waveOutGetPosition);
            LOAD(mciSendCommandA);
        }
    }
    LeaveCriticalSection(&init_lock);
    return real != NULL;
}

typedef MMRESULT (WINAPI *open_fn)(LPHWAVEOUT, UINT, LPCWAVEFORMATEX, DWORD_PTR, DWORD_PTR, DWORD);
typedef MMRESULT (WINAPI *handle_fn)(HWAVEOUT);
typedef MMRESULT (WINAPI *header_fn)(HWAVEOUT, LPWAVEHDR, UINT);
typedef UINT (WINAPI *count_fn)(void);
typedef MMRESULT (WINAPI *caps_fn)(UINT_PTR, LPWAVEOUTCAPSA, UINT);
typedef MMRESULT (WINAPI *getvol_fn)(HWAVEOUT, LPDWORD);
typedef MMRESULT (WINAPI *setvol_fn)(HWAVEOUT, DWORD);
typedef MMRESULT (WINAPI *pos_fn)(HWAVEOUT, LPMMTIME, UINT);
typedef MCIERROR (WINAPI *mci_fn)(MCIDEVICEID, UINT, DWORD_PTR, DWORD_PTR);

/* --- passed on unchanged: the game's sound effects and the CD audio mode --------------------------------------- */

MMRESULT WINAPI tz_waveOutOpen(LPHWAVEOUT h, UINT id, LPCWAVEFORMATEX fmt, DWORD_PTR cb, DWORD_PTR inst, DWORD fl) {
    return load_real() && p_waveOutOpen ? ((open_fn)p_waveOutOpen)(h, id, fmt, cb, inst, fl) : MMSYSERR_ERROR;
}
MMRESULT WINAPI tz_waveOutClose(HWAVEOUT h) {
    return load_real() && p_waveOutClose ? ((handle_fn)p_waveOutClose)(h) : MMSYSERR_ERROR;
}
MMRESULT WINAPI tz_waveOutReset(HWAVEOUT h) {
    return load_real() && p_waveOutReset ? ((handle_fn)p_waveOutReset)(h) : MMSYSERR_ERROR;
}
MMRESULT WINAPI tz_waveOutWrite(HWAVEOUT h, LPWAVEHDR hdr, UINT size) {
    return load_real() && p_waveOutWrite ? ((header_fn)p_waveOutWrite)(h, hdr, size) : MMSYSERR_ERROR;
}
MMRESULT WINAPI tz_waveOutPrepareHeader(HWAVEOUT h, LPWAVEHDR hdr, UINT size) {
    return load_real() && p_waveOutPrepareHeader ? ((header_fn)p_waveOutPrepareHeader)(h, hdr, size) : MMSYSERR_ERROR;
}
MMRESULT WINAPI tz_waveOutUnprepareHeader(HWAVEOUT h, LPWAVEHDR hdr, UINT size) {
    return load_real() && p_waveOutUnprepareHeader ? ((header_fn)p_waveOutUnprepareHeader)(h, hdr, size)
                                                   : MMSYSERR_ERROR;
}
UINT WINAPI tz_waveOutGetNumDevs(void) {
    return load_real() && p_waveOutGetNumDevs ? ((count_fn)p_waveOutGetNumDevs)() : 0;
}
MMRESULT WINAPI tz_waveOutGetDevCapsA(UINT_PTR id, LPWAVEOUTCAPSA caps, UINT size) {
    return load_real() && p_waveOutGetDevCapsA ? ((caps_fn)p_waveOutGetDevCapsA)(id, caps, size) : MMSYSERR_ERROR;
}
MMRESULT WINAPI tz_waveOutGetVolume(HWAVEOUT h, LPDWORD volume) {
    return load_real() && p_waveOutGetVolume ? ((getvol_fn)p_waveOutGetVolume)(h, volume) : MMSYSERR_ERROR;
}
MMRESULT WINAPI tz_waveOutSetVolume(HWAVEOUT h, DWORD volume) {
    return load_real() && p_waveOutSetVolume ? ((setvol_fn)p_waveOutSetVolume)(h, volume) : MMSYSERR_ERROR;
}
MMRESULT WINAPI tz_waveOutGetPosition(HWAVEOUT h, LPMMTIME time, UINT size) {
    return load_real() && p_waveOutGetPosition ? ((pos_fn)p_waveOutGetPosition)(h, time, size) : MMSYSERR_ERROR;
}
MCIERROR WINAPI tz_mciSendCommandA(MCIDEVICEID id, UINT msg, DWORD_PTR p1, DWORD_PTR p2) {
    return load_real() && p_mciSendCommandA ? ((mci_fn)p_mciSendCommandA)(id, msg, p1, p2) : MCIERR_INTERNAL;
}

/* --- the soundfont, loaded once ---------------------------------------------------------------------------------- */

static HMODULE self;
static void* soundfont;
static int soundfont_size;

static int load_soundfont(void) {
    char path[MAX_PATH];
    char* slash;
    HANDLE file;
    DWORD size, read = 0;
    if (soundfont) return 1;
    if (!GetModuleFileNameA(self, path, MAX_PATH - 16)) return 0;
    slash = strrchr(path, '\\');
    strcpy(slash ? slash + 1 : path, "TZMUS.sf2");
    file = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (file == INVALID_HANDLE_VALUE) return 0;
    size = GetFileSize(file, NULL);
    if (size != INVALID_FILE_SIZE && size > 0) {
        soundfont = malloc(size);
        if (soundfont && (!ReadFile(file, soundfont, size, &read, NULL) || read != size)) {
            free(soundfont);
            soundfont = NULL;
        }
    }
    CloseHandle(file);
    soundfont_size = soundfont ? (int)size : 0;
    return soundfont != NULL;
}

/* --- MIDI streams -------------------------------------------------------------------------------------------- */

struct pending {
    UINT message;
    LPMIDIHDR header;
};

struct stream {
    DWORD magic;
    tzm* core;
    CRITICAL_SECTION lock;
    HWAVEOUT wave;
    HANDLE wave_done, thread;
    volatile LONG quit;
    WAVEHDR wave_headers[WAVE_BUFFERS];
    short pcm[WAVE_BUFFERS][WAVE_FRAMES * 2];
    DWORD_PTR callback, instance;
    DWORD flags;
    DWORD volume;
    struct pending pending[MAX_PENDING];
    int pending_count;
};

static DWORD default_volume = 0xFFFFFFFF;

static struct stream* as_stream(void* h) {
    struct stream* s = (struct stream*)h;
    if (!s || (UINT_PTR)s < 0x10000) return NULL; /* a device ID, not a handle */
    return s->magic == MAGIC ? s : NULL;
}

static void apply_volume(struct stream* s) {
    float left = (s->volume & 0xFFFF) / 65535.0f, right = (s->volume >> 16) / 65535.0f;
    tzm_set_volume(s->core, (left + right) / 2);
}

/* Sends a MOM_* notification the way the game asked for in midiStreamOpen. Never called while holding s->lock: the
 * game may queue its next buffer from inside its callback. */
static void notify(struct stream* s, UINT message, LPMIDIHDR header) {
    switch (s->flags & CALLBACK_TYPEMASK) {
    case CALLBACK_FUNCTION:
        if (s->callback) ((LPDRVCALLBACK)s->callback)((HDRVR)s, message, s->instance, (DWORD_PTR)header, 0);
        break;
    case CALLBACK_WINDOW:
        if (s->callback) PostMessageA((HWND)s->callback, message, (WPARAM)s, (LPARAM)header);
        break;
    case CALLBACK_THREAD:
        if (s->callback) PostThreadMessageA((DWORD)s->callback, message, (WPARAM)s, (LPARAM)header);
        break;
    case CALLBACK_EVENT:
        if (s->callback) SetEvent((HANDLE)s->callback);
        break;
    default:
        break;
    }
}

/* core.c's callback, under s->lock: updates the header now, and leaves the notification for flush(). */
static void on_core(void* user, void* tag, int32_t position) {
    struct stream* s = (struct stream*)user;
    LPMIDIHDR header = (LPMIDIHDR)tag;
    if (position < 0) {
        header->dwFlags = (header->dwFlags & ~MHDR_INQUEUE) | MHDR_DONE;
    } else {
        header->dwOffset = (DWORD)position;
    }
    if (s->pending_count < MAX_PENDING) {
        s->pending[s->pending_count].message = position < 0 ? MOM_DONE : MOM_POSITIONCB;
        s->pending[s->pending_count].header = header;
        s->pending_count++;
    }
}

/* Leaves s->lock and delivers the notifications collected under it. */
static void unlock_and_flush(struct stream* s) {
    struct pending batch[MAX_PENDING];
    int i, n = s->pending_count;
    memcpy(batch, s->pending, n * sizeof batch[0]);
    s->pending_count = 0;
    LeaveCriticalSection(&s->lock);
    for (i = 0; i < n; i++) notify(s, batch[i].message, batch[i].header);
}

static DWORD WINAPI render_thread(LPVOID arg) {
    struct stream* s = (struct stream*)arg;
    int i;
    for (i = 0; i < WAVE_BUFFERS; i++) s->wave_headers[i].dwFlags |= WHDR_DONE; /* all free to fill at first */
    while (!s->quit) {
        for (i = 0; i < WAVE_BUFFERS && !s->quit; i++) {
            WAVEHDR* w = &s->wave_headers[i];
            if (!(w->dwFlags & WHDR_DONE)) continue;
            EnterCriticalSection(&s->lock);
            tzm_render(s->core, s->pcm[i], WAVE_FRAMES, on_core, s);
            unlock_and_flush(s);
            w->dwFlags &= ~WHDR_DONE;
            tz_waveOutWrite(s->wave, w, sizeof *w);
        }
        WaitForSingleObject(s->wave_done, 100);
    }
    return 0;
}

static void close_stream(struct stream* s) {
    int i;
    InterlockedExchange(&s->quit, 1);
    SetEvent(s->wave_done);
    WaitForSingleObject(s->thread, INFINITE);
    CloseHandle(s->thread);
    tz_waveOutReset(s->wave);
    for (i = 0; i < WAVE_BUFFERS; i++) tz_waveOutUnprepareHeader(s->wave, &s->wave_headers[i], sizeof(WAVEHDR));
    tz_waveOutClose(s->wave);
    CloseHandle(s->wave_done);
}

MMRESULT WINAPI tz_midiStreamOpen(LPHMIDISTRM out, LPUINT device, DWORD count, DWORD_PTR callback,
                                  DWORD_PTR instance, DWORD flags) {
    struct stream* s;
    WAVEFORMATEX format;
    int i;
    (void)device;
    if (!out) return MMSYSERR_INVALPARAM;
    *out = NULL;
    if (count != 1) return MMSYSERR_INVALPARAM;
    if (!load_real() || !load_soundfont()) return MMSYSERR_NODRIVER;
    s = (struct stream*)calloc(1, sizeof *s);
    if (!s) return MMSYSERR_NOMEM;
    s->core = tzm_create(soundfont, soundfont_size, RATE);
    if (!s->core) { free(s); return MMSYSERR_NODRIVER; }
    InitializeCriticalSection(&s->lock);
    s->callback = callback;
    s->instance = instance;
    s->flags = flags;
    s->volume = default_volume;
    apply_volume(s);
    s->wave_done = CreateEventA(NULL, FALSE, FALSE, NULL);
    memset(&format, 0, sizeof format);
    format.wFormatTag = WAVE_FORMAT_PCM;
    format.nChannels = 2;
    format.nSamplesPerSec = RATE;
    format.wBitsPerSample = 16;
    format.nBlockAlign = 4;
    format.nAvgBytesPerSec = RATE * 4;
    if (tz_waveOutOpen(&s->wave, WAVE_MAPPER, &format, (DWORD_PTR)s->wave_done, 0, CALLBACK_EVENT)
        != MMSYSERR_NOERROR) {
        CloseHandle(s->wave_done);
        DeleteCriticalSection(&s->lock);
        tzm_destroy(s->core);
        free(s);
        return MMSYSERR_ALLOCATED;
    }
    for (i = 0; i < WAVE_BUFFERS; i++) {
        s->wave_headers[i].lpData = (LPSTR)s->pcm[i];
        s->wave_headers[i].dwBufferLength = sizeof s->pcm[i];
        tz_waveOutPrepareHeader(s->wave, &s->wave_headers[i], sizeof(WAVEHDR));
    }
    s->magic = MAGIC;
    s->thread = CreateThread(NULL, 0, render_thread, s, 0, NULL);
    *out = (HMIDISTRM)s;
    notify(s, MOM_OPEN, NULL);
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiStreamClose(HMIDISTRM h) {
    struct stream* s = as_stream(h);
    if (!s) return MMSYSERR_INVALHANDLE;
    EnterCriticalSection(&s->lock);
    tzm_stop(s->core, on_core, s);
    unlock_and_flush(s);
    close_stream(s);
    s->magic = 0;
    notify(s, MOM_CLOSE, NULL);
    DeleteCriticalSection(&s->lock);
    tzm_destroy(s->core);
    free(s);
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiStreamOut(HMIDISTRM h, LPMIDIHDR header, UINT size) {
    struct stream* s = as_stream(h);
    int queued;
    if (!s) return MMSYSERR_INVALHANDLE;
    if (!header || size < offsetof(MIDIHDR, dwOffset) || !header->lpData) return MMSYSERR_INVALPARAM;
    if (!(header->dwFlags & MHDR_PREPARED)) return MIDIERR_UNPREPARED;
    if (header->dwFlags & MHDR_INQUEUE) return MIDIERR_STILLPLAYING;
    EnterCriticalSection(&s->lock);
    header->dwFlags = (header->dwFlags & ~MHDR_DONE) | MHDR_INQUEUE;
    queued = tzm_queue(s->core, (const uint8_t*)header->lpData, header->dwBytesRecorded, header);
    if (!queued) header->dwFlags &= ~MHDR_INQUEUE;
    LeaveCriticalSection(&s->lock);
    return queued ? MMSYSERR_NOERROR : MMSYSERR_NOMEM;
}

MMRESULT WINAPI tz_midiStreamRestart(HMIDISTRM h) {
    struct stream* s = as_stream(h);
    if (!s) return MMSYSERR_INVALHANDLE;
    EnterCriticalSection(&s->lock);
    tzm_play(s->core);
    LeaveCriticalSection(&s->lock);
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiStreamPause(HMIDISTRM h) {
    struct stream* s = as_stream(h);
    if (!s) return MMSYSERR_INVALHANDLE;
    EnterCriticalSection(&s->lock);
    tzm_pause(s->core);
    LeaveCriticalSection(&s->lock);
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiStreamStop(HMIDISTRM h) {
    struct stream* s = as_stream(h);
    if (!s) return MMSYSERR_INVALHANDLE;
    EnterCriticalSection(&s->lock);
    tzm_stop(s->core, on_core, s);
    unlock_and_flush(s);
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiStreamProperty(HMIDISTRM h, LPBYTE data, DWORD property) {
    struct stream* s = as_stream(h);
    MMRESULT result = MMSYSERR_NOERROR;
    if (!s) return MMSYSERR_INVALHANDLE;
    if (!data) return MMSYSERR_INVALPARAM;
    EnterCriticalSection(&s->lock);
    if (property & MIDIPROP_TIMEDIV) {
        MIDIPROPTIMEDIV* p = (MIDIPROPTIMEDIV*)data;
        if (property & MIDIPROP_GET) p->dwTimeDiv = tzm_timediv(s->core);
        else if (p->dwTimeDiv & 0x8000) result = MMSYSERR_NOTSUPPORTED; /* SMPTE time: Tzar uses ticks */
        else tzm_set_timediv(s->core, p->dwTimeDiv);
    } else if (property & MIDIPROP_TEMPO) {
        MIDIPROPTEMPO* p = (MIDIPROPTEMPO*)data;
        if (property & MIDIPROP_GET) p->dwTempo = tzm_tempo(s->core);
        else tzm_set_tempo(s->core, p->dwTempo);
    } else {
        result = MMSYSERR_INVALPARAM;
    }
    LeaveCriticalSection(&s->lock);
    return result;
}

MMRESULT WINAPI tz_midiOutPrepareHeader(HMIDIOUT h, LPMIDIHDR header, UINT size) {
    (void)h;
    if (!header || size < offsetof(MIDIHDR, dwOffset) || !header->lpData) return MMSYSERR_INVALPARAM;
    header->dwFlags |= MHDR_PREPARED;
    header->dwFlags &= ~MHDR_DONE;
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiOutUnprepareHeader(HMIDIOUT h, LPMIDIHDR header, UINT size) {
    (void)h;
    if (!header || size < offsetof(MIDIHDR, dwOffset)) return MMSYSERR_INVALPARAM;
    if (header->dwFlags & MHDR_INQUEUE) return MIDIERR_STILLPLAYING;
    header->dwFlags &= ~MHDR_PREPARED;
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiOutReset(HMIDIOUT h) {
    struct stream* s = as_stream(h);
    if (!s) return MMSYSERR_INVALHANDLE;
    EnterCriticalSection(&s->lock);
    tzm_reset(s->core, on_core, s);
    unlock_and_flush(s);
    return MMSYSERR_NOERROR;
}

UINT WINAPI tz_midiOutGetNumDevs(void) { return 1; }

MMRESULT WINAPI tz_midiOutGetDevCapsA(UINT_PTR device, LPMIDIOUTCAPSA caps, UINT size) {
    MIDIOUTCAPSA c;
    if (!caps) return MMSYSERR_INVALPARAM;
    if (device != 0 && device != MIDI_MAPPER && !as_stream((void*)device)) return MMSYSERR_BADDEVICEID;
    memset(&c, 0, sizeof c);
    c.wMid = 0xFFFF; /* MM_UNMAPPED: no registered manufacturer */
    c.wPid = 0xFFFF;
    c.vDriverVersion = 0x0100;
    strcpy(c.szPname, "Tzar widescreen mod synth");
    c.wTechnology = MOD_SWSYNTH;
    c.wVoices = 128;
    c.wNotes = 128;
    c.wChannelMask = 0xFFFF;
    c.dwSupport = MIDICAPS_VOLUME | MIDICAPS_LRVOLUME | MIDICAPS_STREAM;
    memcpy(caps, &c, size < sizeof c ? size : sizeof c);
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiOutSetVolume(HMIDIOUT h, DWORD volume) {
    struct stream* s = as_stream(h);
    if (!s) { default_volume = volume; return MMSYSERR_NOERROR; } /* by device ID: for the streams to come */
    EnterCriticalSection(&s->lock);
    s->volume = volume;
    apply_volume(s);
    LeaveCriticalSection(&s->lock);
    return MMSYSERR_NOERROR;
}

MMRESULT WINAPI tz_midiOutGetVolume(HMIDIOUT h, LPDWORD volume) {
    struct stream* s = as_stream(h);
    if (!volume) return MMSYSERR_INVALPARAM;
    *volume = s ? s->volume : default_volume;
    return MMSYSERR_NOERROR;
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved) {
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        self = instance;
        InitializeCriticalSection(&init_lock);
        DisableThreadLibraryCalls(instance);
    }
    return TRUE;
}
