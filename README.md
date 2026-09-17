# Fight A Live

Bare-metal Sega Dreamcast boss-duel action game. No KallistiOS (KOS), no
libc: direct PVR register/framebuffer access and a hand-written SH4 entry
stub, per the CryMon bare-metal playbook (`xenodorian/beelzfight`). This
project is independent of BeelzFight -- no shared code, no shared repo.

## Status

Scaffolding only. `src/` builds a boot skeleton that clears the screen to a
solid color -- the standard first checkpoint before writing game logic
(confirms the toolchain + linker script + PVR init work at all).

**Toolchain not yet verified.** No `sh-elf-gcc` cross-compiler was available
in the environment this was scaffolded in (no Docker daemon access), so
`make` and `make cdi` have not been run, and the PVR init values in
`src/pvr.c` have not been boot-tested in Flycast. See "Building" below.

## Layout

- `src/dc.ld` -- linker script (16MB main RAM, entry at 0x8c010000)
- `src/start.S` -- SH4 entry stub (disables interrupts, sets stack, jumps
  to `game_main`)
- `src/pvr.h` / `src/pvr.c` -- PowerVR2 register access, 640x480 RGB565
  double-buffered framebuffer setup
- `src/render.h` / `src/render.c` -- `put_pixel`/`fill_rect`/`blit_sprite`
  software rendering primitives, magenta (`0xF81F`) color-key transparency
- `src/main.c` -- entry point / main loop
- `tools/gen_sprites.py` -- Pillow-based PNG -> RGB565 C array converter,
  with placeholder-art fallback (writes `ART_NEEDED.md` for anything
  missing)
- `art/sprites/` -- in-repo sprite source PNGs (authoritative once present)

## Building

Requires `sh-elf-gcc`/`as`/`ld`/`objcopy` (SH4 cross toolchain) and
`mkdcdisc` on PATH. See `xenodorian/beelzfight`'s `docker/Dockerfile.romdev`
for one way to build a working toolchain image (same approach applies
here, unmodified -- it's not BeelzFight-specific).

```
python3 tools/gen_sprites.py <path-to-art-source>   # only if sprites changed
make clean && make        # must build with zero warnings
make cdi                  # produces out.cdi
```

Boot `out.cdi` in Flycast and confirm it shows a solid dark-blue screen
before writing any further game logic.

## Design

Single-boss duel: one arena, a player sprite, and a boss cycling through a
small set of telegraphed attack patterns. Chosen to fit both the playbook's
constraints (no 3D, no runtime rotation/scaling, hard color-key
transparency, everything baked into static C arrays, no audio) and the
craftpix "Free Fantasy RPG Pirate Boss Character Pack" sprite pack, which
is a single boss character's animation set rather than a full cast.
