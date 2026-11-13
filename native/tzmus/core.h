/* The music synthesizer's core: plays winmm midiStream buffers through TinySoundFont.
 *
 * Plain C, no Windows headers, so the same code runs in the DLL (tzmus.c) and in native tests (render.c). A buffer is
 * a list of MIDIEVENT records, as midiStreamOut takes them: delta time in ticks (4 bytes), stream ID (4, unused),
 * event (4: type in the high byte, parameters in the low 24 bits), then for long events their parameters, padded to
 * 4 bytes. Ticks become samples through the time division (ticks per quarter note) and the tempo (microseconds per
 * quarter note), which MEVT_TEMPO events can change on the way.
 *
 * Not thread-safe: the DLL calls it under its own lock.
 */
#ifndef TZMUS_CORE_H
#define TZMUS_CORE_H

#include <stdint.h>

typedef struct tzm tzm;

/* Called when the player is done with a buffer (position < 0), or reaches an event flagged MEVT_F_CALLBACK
 * (position = the event's offset in the buffer). tag is what tzm_queue was given. */
typedef void (*tzm_callback)(void* user, void* tag, int32_t position);

/* A synthesizer for the soundfont in sf2 (which must stay valid until tzm_destroy), at this sample rate. NULL if the
 * soundfont can't be read. */
tzm* tzm_create(const void* sf2, int size, int sample_rate);
void tzm_destroy(tzm* m);

uint32_t tzm_timediv(const tzm* m);
void tzm_set_timediv(tzm* m, uint32_t ticks_per_quarter);
uint32_t tzm_tempo(const tzm* m);
void tzm_set_tempo(tzm* m, uint32_t microseconds_per_quarter);
void tzm_set_volume(tzm* m, float gain);

/* Adds a buffer to play after the ones already queued. The buffer must stay valid until its callback. 0 if the queue
 * is full. */
int tzm_queue(tzm* m, const uint8_t* events, uint32_t length, void* tag);
void tzm_play(tzm* m);
/* Stops playing and silences the notes, keeping the queue and the position. */
void tzm_pause(tzm* m);
/* Stops, silences the notes, and gives every queued buffer back through callback, position back at the start. */
void tzm_stop(tzm* m, tzm_callback callback, void* user);
/* tzm_stop, and resets every channel's controllers and program. */
void tzm_reset(tzm* m, tzm_callback callback, void* user);
int tzm_playing(const tzm* m);

/* A MIDI short message: status in the low byte, then the two data bytes. */
void tzm_short_message(tzm* m, uint32_t message);

/* Renders frames of interleaved 16-bit stereo, playing the queued events that fall within them. */
void tzm_render(tzm* m, int16_t* out, int frames, tzm_callback callback, void* user);

#endif
