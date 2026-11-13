/* The music synthesizer's core: see core.h. */
#include "core.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

#define TSF_IMPLEMENTATION
#include <tinysoundfont/tsf.h> /* vendored: native/third_party, a system include so its own warnings stay out */

#define QUEUE 64             /* buffers waiting to play: the game keeps a handful in flight */
#define BLOCK 64             /* frames rendered between checks for events */
#define EVENT_SIZE 12        /* delta, stream ID, event */
#define MEVT_F_LONG 0x80u    /* in the event's high byte: parameters follow */
#define MEVT_F_CALLBACK 0x40u
#define MEVT_SHORTMSG 0x00u
#define MEVT_TEMPO 0x01u
#define DRUMS 9              /* MIDI channel 10 */
#define KNEE 0.75f           /* the soft limiter leaves samples below this alone */

struct buffer {
    const uint8_t* events;
    uint32_t length;
    void* tag;
};

struct tzm {
    tsf* synth;
    float mix[BLOCK * 2];
    int sample_rate;
    uint32_t timediv, tempo;
    struct buffer queue[QUEUE];
    int head, count;
    uint32_t offset;   /* in the first queued buffer */
    int delta_taken;   /* the next event's delta time is already counted in wait */
    double wait;       /* frames until the next event */
    int playing;
};

static uint32_t read32(const uint8_t* p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static void reset_channels(tzm* m) {
    int ch;
    for (ch = 0; ch < 16; ch++) {
        tsf_channel_sounds_off_all(m->synth, ch);
        tsf_channel_midi_control(m->synth, ch, 121, 0); /* reset all controllers */
        tsf_channel_set_bank(m->synth, ch, ch == DRUMS ? 128 : 0);
        tsf_channel_set_presetnumber(m->synth, ch, 0, ch == DRUMS);
    }
}

tzm* tzm_create(const void* sf2, int size, int sample_rate) {
    tzm* m = (tzm*)calloc(1, sizeof(tzm));
    if (!m) return NULL;
    m->synth = tsf_load_memory(sf2, size);
    if (!m->synth) { free(m); return NULL; }
    m->sample_rate = sample_rate;
    tsf_set_output(m->synth, TSF_STEREO_INTERLEAVED, sample_rate, -6.0f); /* headroom for 16 channels at once */
    tsf_set_max_voices(m->synth, 128);
    m->timediv = 96;
    m->tempo = 500000; /* 120 beats per minute, MIDI's default */
    reset_channels(m);
    return m;
}

void tzm_destroy(tzm* m) {
    if (!m) return;
    tsf_close(m->synth);
    free(m);
}

uint32_t tzm_timediv(const tzm* m) { return m->timediv; }
void tzm_set_timediv(tzm* m, uint32_t ticks) { m->timediv = ticks ? ticks : 96; }
uint32_t tzm_tempo(const tzm* m) { return m->tempo; }
void tzm_set_tempo(tzm* m, uint32_t microseconds) { m->tempo = microseconds ? microseconds : 500000; }
void tzm_set_volume(tzm* m, float gain) { tsf_set_volume(m->synth, gain); }
int tzm_playing(const tzm* m) { return m->playing; }

int tzm_queue(tzm* m, const uint8_t* events, uint32_t length, void* tag) {
    struct buffer* b;
    if (m->count == QUEUE) return 0;
    b = &m->queue[(m->head + m->count) % QUEUE];
    b->events = events;
    b->length = length;
    b->tag = tag;
    m->count++;
    return 1;
}

void tzm_play(tzm* m) { m->playing = 1; }

void tzm_pause(tzm* m) {
    int ch;
    m->playing = 0;
    for (ch = 0; ch < 16; ch++) tsf_channel_note_off_all(m->synth, ch);
}

void tzm_stop(tzm* m, tzm_callback callback, void* user) {
    tzm_pause(m);
    while (m->count) {
        void* tag = m->queue[m->head].tag;
        m->head = (m->head + 1) % QUEUE;
        m->count--;
        if (callback) callback(user, tag, -1);
    }
    m->offset = 0;
    m->delta_taken = 0;
    m->wait = 0;
}

void tzm_reset(tzm* m, tzm_callback callback, void* user) {
    tzm_stop(m, callback, user);
    reset_channels(m);
}

void tzm_short_message(tzm* m, uint32_t message) {
    int status = message & 0xFF, channel = status & 0x0F;
    int a = (message >> 8) & 0x7F, b = (message >> 16) & 0x7F;
    switch (status & 0xF0) {
    case 0x80: tsf_channel_note_off(m->synth, channel, a); break;
    case 0x90:
        if (b) tsf_channel_note_on(m->synth, channel, a, b / 127.0f);
        else tsf_channel_note_off(m->synth, channel, a);
        break;
    case 0xB0: tsf_channel_midi_control(m->synth, channel, a, b); break;
    /* A program missing from the trimmed soundfont keeps the channel's previous one: TinySoundFont falls back to
     * bank 0 and the standard drum kit by itself. */
    case 0xC0: tsf_channel_set_presetnumber(m->synth, channel, a, channel == DRUMS); break;
    case 0xE0: tsf_channel_set_pitchwheel(m->synth, channel, a | b << 7); break;
    default: break; /* aftertouch: TinySoundFont doesn't use it */
    }
}

static double frames_per_tick(const tzm* m) {
    return (double)m->tempo / m->timediv * m->sample_rate / 1000000.0;
}

/* Plays the events that are due. */
static void play_due(tzm* m, tzm_callback callback, void* user) {
    while (m->playing && m->count) {
        struct buffer* b = &m->queue[m->head];
        uint32_t event, size;
        if (m->offset + EVENT_SIZE > b->length) { /* done with this buffer */
            void* tag = b->tag;
            m->head = (m->head + 1) % QUEUE;
            m->count--;
            m->offset = 0;
            m->delta_taken = 0;
            if (callback) callback(user, tag, -1);
            continue;
        }
        if (!m->delta_taken) {
            m->wait += read32(b->events + m->offset) * frames_per_tick(m);
            m->delta_taken = 1;
        }
        if (m->wait >= 1.0) return;
        event = read32(b->events + m->offset + 8);
        size = EVENT_SIZE;
        if ((event >> 24) & MEVT_F_LONG) {
            size += ((event & 0xFFFFFF) + 3) & ~3u; /* system exclusive and the like: skipped */
        } else if (((event >> 24) & 0x3F) == MEVT_SHORTMSG) {
            tzm_short_message(m, event & 0xFFFFFF);
        } else if (((event >> 24) & 0x3F) == MEVT_TEMPO) {
            tzm_set_tempo(m, event & 0xFFFFFF);
        }
        if (((event >> 24) & MEVT_F_CALLBACK) && callback) callback(user, b->tag, (int32_t)m->offset);
        m->offset += size;
        m->delta_taken = 0;
    }
}

/* Rounds off the rare peaks above full scale (a loud chord on a drum hit), instead of clipping them, and leaves
 * everything below KNEE as it is. */
static int16_t limit(float x) {
    float a = x < 0 ? -x : x;
    if (a > KNEE) a = KNEE + (1.0f - KNEE) * tanhf((a - KNEE) / (1.0f - KNEE));
    return (int16_t)((x < 0 ? -a : a) * 32767.0f);
}

void tzm_render(tzm* m, int16_t* out, int frames, tzm_callback callback, void* user) {
    while (frames > 0) {
        int i, chunk = frames < BLOCK ? frames : BLOCK;
        play_due(m, callback, user);
        if (m->playing && m->count && m->delta_taken && m->wait < chunk) chunk = (int)m->wait;
        if (chunk < 1) chunk = 1;
        tsf_render_float(m->synth, m->mix, chunk, 0);
        for (i = 0; i < chunk * 2; i++) out[i] = limit(m->mix[i]);
        if (m->playing && m->count) m->wait -= chunk;
        out += chunk * 2;
        frames -= chunk;
    }
}
