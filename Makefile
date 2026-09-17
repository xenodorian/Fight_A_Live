# Makefile -- bare-metal Dreamcast build, no KOS.

CC = sh-elf-gcc
AS = sh-elf-as
LD = sh-elf-ld
OBJCOPY = sh-elf-objcopy

ARCHFLAGS = -m4-single-only -ml

CFLAGS = $(ARCHFLAGS) -O2 -fno-builtin -ffreestanding -fomit-frame-pointer \
         -Wall -Wextra -nostdlib -nostartfiles -nodefaultlibs -Isrc
LDFLAGS = $(ARCHFLAGS) -nostdlib -nostartfiles -nodefaultlibs \
          -T src/dc.ld -Wl,--build-id=none

SRC_C = src/main.c src/pvr.c src/render.c
SRC_S = src/start.S
OBJ = $(SRC_S:.S=.o) $(SRC_C:.c=.o)

TARGET = fightalive.elf
CDI = out.cdi

.PHONY: all clean cdi

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $(OBJ) -lgcc

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.o: %.S
	$(CC) $(CFLAGS) -c -o $@ $<

cdi: $(TARGET)
	mkdcdisc -e $(TARGET) -o $(CDI) -n "FIGHT A LIVE" -a "xenodorian" -N --allow-overwrite

clean:
	rm -f $(OBJ) $(TARGET) $(CDI)
