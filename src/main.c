#include <stdint.h>
#include "pvr.h"
#include "render.h"

#define BACK_BUFFER_OFFSET (SCREEN_W * SCREEN_H * 2)

void game_main(void)
{
    pvr_init();

    uint32_t draw_offset = BACK_BUFFER_OFFSET;
    uint32_t show_offset = 0;

    for (;;) {
        framebuffer_t fb;
        fb_init(&fb, draw_offset);

        fill_rect(&fb, 0, 0, SCREEN_W, SCREEN_H, rgb565(20, 20, 60));

        pvr_flip(draw_offset);

        uint32_t tmp = draw_offset;
        draw_offset = show_offset;
        show_offset = tmp;
    }
}
