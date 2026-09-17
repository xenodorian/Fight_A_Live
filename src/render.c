#include "render.h"

void fb_init(framebuffer_t *fb, uint32_t back_buffer_offset)
{
    fb->pixels = (uint16_t *)(VRAM_BASE + back_buffer_offset);
    fb->stride = SCREEN_W;
}

void put_pixel(framebuffer_t *fb, int x, int y, uint16_t color)
{
    if (x < 0 || y < 0 || x >= SCREEN_W || y >= SCREEN_H) {
        return;
    }
    fb->pixels[y * fb->stride + x] = color;
}

void fill_rect(framebuffer_t *fb, int x, int y, int w, int h, uint16_t color)
{
    for (int row = 0; row < h; row++) {
        int py = y + row;
        if (py < 0 || py >= SCREEN_H) {
            continue;
        }
        for (int col = 0; col < w; col++) {
            put_pixel(fb, x + col, py, color);
        }
    }
}

void blit_sprite(framebuffer_t *fb, const uint16_t *pixels, int sw, int sh, int x, int y)
{
    for (int row = 0; row < sh; row++) {
        int py = y + row;
        if (py < 0 || py >= SCREEN_H) {
            continue;
        }
        for (int col = 0; col < sw; col++) {
            uint16_t color = pixels[row * sw + col];
            if (color == TRANSPARENT_KEY) {
                continue;
            }
            put_pixel(fb, x + col, py, color);
        }
    }
}
