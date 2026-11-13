/* Renders a MIDI file to a WAV file through the music core, the way the game feeds it: as midiStream buffers, a few
 * in flight at a time, refilled as the player finishes them. For listening tests and for tests/test_music.py.
 *
 * Usage: render <soundfont.sf2> <music.mid> <out.wav> [seconds]
 */
#include "core.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TML_IMPLEMENTATION
#include <tinysoundfont/tml.h>

#define RATE 44100
#define IN_FLIGHT 4
#define EVENTS_PER_BUFFER 64

struct feeder {
    uint8_t buffers[IN_FLIGHT][EVENTS_PER_BUFFER * 12];
    int free[IN_FLIGHT];
    tml_message* next;
    unsigned int last_time;
    int done_count, queued_count;
};

static void put32(uint8_t* p, uint32_t v) {
    p[0] = v & 0xFF; p[1] = (v >> 8) & 0xFF; p[2] = (v >> 16) & 0xFF; p[3] = (v >> 24) & 0xFF;
}

/* Fills free buffers with the next events. One tick is one millisecond: time division 1000 at 60 beats a minute. */
static void feed(struct feeder* f, tzm* m) {
    int i;
    for (i = 0; i < IN_FLIGHT; i++) {
        uint32_t n = 0;
        if (!f->free[i] || !f->next) continue;
        while (f->next && n < EVENTS_PER_BUFFER) {
            tml_message* e = f->next;
            uint32_t message = 0;
            switch (e->type) {
            case TML_NOTE_OFF: case TML_NOTE_ON: case TML_KEY_PRESSURE: case TML_CONTROL_CHANGE:
                message = e->type | e->channel | (uint32_t)e->key << 8 | (uint32_t)e->velocity << 16; break;
            case TML_PROGRAM_CHANGE: case TML_CHANNEL_PRESSURE:
                message = e->type | e->channel | (uint32_t)e->program << 8; break;
            case TML_PITCH_BEND:
                message = e->type | e->channel | (uint32_t)(e->pitch_bend & 0x7F) << 8
                          | (uint32_t)(e->pitch_bend >> 7) << 16; break;
            default: f->next = e->next; continue; /* meta events: tml already turned tempo into times */
            }
            put32(f->buffers[i] + n * 12, e->time - f->last_time);
            put32(f->buffers[i] + n * 12 + 4, 0);
            put32(f->buffers[i] + n * 12 + 8, message);
            f->last_time = e->time;
            f->next = e->next;
            n++;
        }
        if (n) {
            f->free[i] = 0;
            tzm_queue(m, f->buffers[i], n * 12, &f->free[i]);
            f->queued_count++;
        }
    }
}

static void on_callback(void* user, void* tag, int32_t position) {
    struct feeder* f = (struct feeder*)user;
    if (position < 0) {
        *(int*)tag = 1;
        f->done_count++;
    }
}

static void wav_header(FILE* out, uint32_t frames) {
    uint8_t h[44];
    memcpy(h, "RIFF", 4); put32(h + 4, 36 + frames * 4); memcpy(h + 8, "WAVEfmt ", 8);
    put32(h + 16, 16); h[20] = 1; h[21] = 0; h[22] = 2; h[23] = 0; put32(h + 24, RATE); put32(h + 28, RATE * 4);
    h[32] = 4; h[33] = 0; h[34] = 16; h[35] = 0; memcpy(h + 36, "data", 4); put32(h + 40, frames * 4);
    fwrite(h, 1, 44, out);
}

int main(int argc, char** argv) {
    FILE *in, *out;
    long size;
    void* sf2;
    tzm* m;
    struct feeder f;
    int16_t block[1024 * 2];
    uint32_t frames = 0, limit;
    int i, peak = 0;
    if (argc < 4) { fprintf(stderr, "usage: render <soundfont.sf2> <music.mid> <out.wav> [seconds]\n"); return 2; }
    in = fopen(argv[1], "rb");
    if (!in) { perror(argv[1]); return 1; }
    fseek(in, 0, SEEK_END); size = ftell(in); fseek(in, 0, SEEK_SET);
    sf2 = malloc(size);
    if (fread(sf2, 1, size, in) != (size_t)size) { perror(argv[1]); return 1; }
    fclose(in);
    m = tzm_create(sf2, (int)size, RATE);
    if (!m) { fprintf(stderr, "can't read the soundfont\n"); return 1; }
    memset(&f, 0, sizeof f);
    for (i = 0; i < IN_FLIGHT; i++) f.free[i] = 1;
    f.next = tml_load_filename(argv[2]);
    if (!f.next) { fprintf(stderr, "can't read the MIDI file\n"); return 1; }
    limit = argc > 4 ? (uint32_t)(atof(argv[4]) * RATE) : 0xFFFFFFFFu;
    tzm_set_timediv(m, 1000);
    tzm_set_tempo(m, 1000000);
    out = fopen(argv[3], "wb");
    if (!out) { perror(argv[3]); return 1; }
    wav_header(out, 0);
    feed(&f, m);
    tzm_play(m);
    /* until the music and its last notes' release are over */
    while (frames < limit && (f.next || f.done_count < f.queued_count || frames % (RATE * 2) || peak)) {
        int n = 1024;
        tzm_render(m, block, n, on_callback, &f);
        feed(&f, m);
        if (!f.next && f.done_count == f.queued_count) {
            int quiet = 1;
            for (i = 0; i < n * 2; i++) if (block[i] > 8 || block[i] < -8) quiet = 0;
            if (quiet) break;
        }
        for (i = 0; i < n * 2; i++) {
            int v = block[i] < 0 ? -block[i] : block[i];
            if (v > peak) peak = v;
        }
        fwrite(block, 4, n, out);
        frames += n;
    }
    fseek(out, 0, SEEK_SET);
    wav_header(out, frames);
    fclose(out);
    printf("%s: %.1f s, %d buffers played, peak %d of 32767\n", argv[3], frames / (double)RATE, f.done_count, peak);
    tzm_destroy(m);
    free(sf2);
    return 0;
}
