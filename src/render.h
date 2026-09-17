/* render.h -- software rendering primitives over the raw RGB565 framebuffer. */

#ifndef RENDER_H
#define RENDER_H

#include <stdint.h>
#include "pvr.h"

#define TRANSPARENT_KEY 0xF81Fu /* magenta */

static inline uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b)
{
    return (uint16_t)(((r & 0xf8) << 8) | ((g & 0xfc) << 3) | (b >> 3));
}

typedef struct {
    uint16_t *pixels;   /* VRAM pointer for the active draw buffer */
    uint32_t stride;    /* pixels per row */
} framebuffer_t;

void fb_init(framebuffer_t *fb, uint32_t back_buffer_offset);
void put_pixel(framebuffer_t *fb, int x, int y, uint16_t color);
void fill_rect(framebuffer_t *fb, int x, int y, int w, int h, uint16_t color);
void blit_sprite(framebuffer_t *fb, const uint16_t *pixels, int sw, int sh, int x, int y);

#endif
