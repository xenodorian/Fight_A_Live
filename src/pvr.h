/* pvr.h -- direct PowerVR2 register access, no KOS.
 *
 * All PVR registers are memory-mapped 32-bit words starting at 0xa05f8000.
 */

#ifndef PVR_H
#define PVR_H

#include <stdint.h>

#define PVR_BASE 0xa05f8000u

#define PVR_REG(off) (*(volatile uint32_t *)(PVR_BASE + (off)))

#define PVR_BORDER_COLOR PVR_REG(0x040)
#define PVR_FB_CFG_1     PVR_REG(0x044)
#define PVR_FB_CFG_2     PVR_REG(0x048)
#define PVR_RENDER_MODULO PVR_REG(0x04c)
#define PVR_FB_ADDR      PVR_REG(0x050)
#define PVR_FB_SIZE      PVR_REG(0x05c)
#define PVR_VPOS_IRQ     PVR_REG(0x0cc)
#define PVR_IL_CFG       PVR_REG(0x0d0)
#define PVR_BORDER_X     PVR_REG(0x0d4)
#define PVR_SCAN_CLK     PVR_REG(0x0d8)
#define PVR_BORDER_Y     PVR_REG(0x0dc)
#define PVR_VIDEO_CFG    PVR_REG(0x0e8)
#define PVR_BITMAP_X     PVR_REG(0x0ec)
#define PVR_BITMAP_Y     PVR_REG(0x0f0)
#define PVR_SYNC_STATUS  PVR_REG(0x10c)

#define SCREEN_W 640
#define SCREEN_H 480

/* VRAM base for framebuffer pixel writes (offset 0 into PVR_FB_ADDR space). */
#define VRAM_BASE 0xa5000000u

void pvr_init(void);
void pvr_wait_vblank(void);
void pvr_flip(uint32_t back_buffer_offset);

#endif
