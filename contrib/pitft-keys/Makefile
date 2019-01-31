OVERLAY?=pitft-keys
SRC=$(OVERLAY).dts
OVL=$(OVERLAY).dtbo

all: $(OVL)

$(OVL): $(SRC)
	dtc -I dts -O dtb -o $@ $<

install: $(OVL)
	sudo cp $(OVL) /boot/overlays/
	@echo "Add 'dtoverlay=$(OVERLAY)' to /boot/config.txt!"

