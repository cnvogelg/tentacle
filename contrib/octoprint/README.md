# My OctoPrint Installation

Some remarks (mostly for myself) on my current OctoPrint installation.
Its based on the official [OctoPi][1] distribution with some minor tweaks.

## Raspi Cam

I have installed a Raspberry Pi Cam and added the Video4Linux driver for it
in  `/etc/modules`:

```
bcm2835_v4l2
```

The image had the wrong orientation so I had to adjust it in `/etc/rc.local`:

```
v4l2-ctl --set-ctrl vertical_flip=1 --set-ctrl horizontal_flip=1
```

The tool is found in the `v4l-utils` package.

Then auto detection of `mjpeg streamer` in OctoPrint works as expected.

## PiTFT+ 2.8 with Hardkeys

My display for `tentacle` is an [Adafruit PiTFT+ 2.8"][2] with either
capacitive or resistive touch screen and 4 hard keys.

Install like described by Adafruit in [the manual][3].
It boils down to adding the HAT in `/etc/config.txt`:

```
dtparam=spi=on
dtparam=i2c1=on
dtparam=i2c_arm=on
dtoverlay=pitft28-resistive,rotate=90,speed=64000000,fps=30
```

Note the rotation of 90 degrees so I can use landscape mode with the correct
orientation.

## Setup Hardkeys

The following GPIOs are connected to the PiTFT+ Hardkeys (from top to bottom):

* 17
* 22
* 23
* 27

I added a device tree file that maps these to the following input keys (see
the [Linux Kernel input event header][4] for the codes):

* 17: Escape (1)
* 22: Cursor Up (103)
* 23: Enter (28)
* 27: Cursor Down (108)

Just run the supplied `Makefile` in this directory to build the device tree
overlay binary and install it in `/boot/`:

```
make install
```

Note: It will ask for your user password to install the file.

## Touchscreen

I have the resistive touchscreen and the associated driver is called `stmpe`.
An associated udev rule is found here:

```
/etc/udev/rules.d/95-stmpe.rules:
SUBSYSTEM=="input", ATTRS{name}=="*stmpe*", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen", ENV{LIBINPUT_CALIBRATION_MATRIX}="0 -1 1  1 0 0"
```

Note the input calibration matrix I have added. This matrix applies the
transformation to map the input coordinates to the same 90 degree landscape
orientation that was setup with the display driver above.

Either reboot your Pi to make this change active or re-load udev rules:

```
$ sudo udevadm control --reload-rules
```

[1]: https://octoprint.org/download/
[2]: https://www.adafruit.com/product/2423
[3]: https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi
[4]: https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h