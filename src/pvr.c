/*
 * pvr.c -- PVR framebuffer bring-up: 640x480 RGB565, double-buffered.
 *
 * NOTE: these register values are the standard published bare-metal DC
 * PVR init constants (register offsets confirmed against the CryMon
 * bare-metal playbook). They have NOT been boot-tested in this session --
 * no sh-elf-gcc toolchain was available here (no docker daemon). Verify
 * in Flycast before relying on this.
 */

#include "pvr.h"

#define FB_STRIDE_MODULO ((SCREEN_W * 2) / 8)

void pvr_init(void)
{
    PVR_BORDER_COLOR = 0x000000;

    /* 16bpp RGB565 linear framebuffer, enabled. */
    PVR_FB_CFG_1 = 0x00000009;
    PVR_FB_CFG_2 = 0x00000000;

    PVR_RENDER_MODULO = FB_STRIDE_MODULO;

    PVR_FB_ADDR = 0x00000000;
    PVR_FB_SIZE = ((SCREEN_H - 1) << 16) | (FB_STRIDE_MODULO * 4 - 1);

    /* Standard NTSC 640x480 timing. */
    PVR_VPOS_IRQ = 0x00000000;
    PVR_IL_CFG   = 0x00000000;
    PVR_BORDER_X = 0x000000a7;
    PVR_SCAN_CLK = 0x00000000;
    PVR_BORDER_Y = 0x00000012;
    PVR_BITMAP_X = 0x00000000;
    PVR_BITMAP_Y = 0x00000000;

    /* Enable video output last, once everything else is configured. */
    PVR_VIDEO_CFG = 0x00000007;
}

void pvr_wait_vblank(void)
{
    while ((PVR_SYNC_STATUS & 0x1ff) == 0) {}
    while ((PVR_SYNC_STATUS & 0x1ff) != 0) {}
}

void pvr_flip(uint32_t back_buffer_offset)
{
    pvr_wait_vblank();
    PVR_FB_ADDR = back_buffer_offset;
}
