/*
 * start.S -- bare-metal SH4 entry point.
 *
 * 1. Disable interrupts, set a known-good status register.
 * 2. Set the stack pointer to the top of main RAM.
 * 3. Jump to the C entry function (never returns).
 * 4. Safety net: spin forever if it somehow does return.
 */

    .section .text.start, "ax"
    .global _start
    .align 2

_start:
    mov.l   sr_init, r0
    ldc     r0, sr

    mov.l   stack_top, r15

    mov.l   main_entry, r1
    jsr     @r1
    nop

halt_loop:
    bra     halt_loop
    nop

    .align 4
sr_init:
    .long   0x500000f0
stack_top:
    .long   0x8cfffff0
main_entry:
    .long   game_main
