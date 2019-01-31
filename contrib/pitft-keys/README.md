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

### Calibration Tool

An X11 based calibration tool is needed to calculate the calibration matrix:

```
sudo apt-get install libxaw7-dev libxxf86vm-dev libxaw7-dev libxft-dev
git clone https://github.com/KurtJacobson/xtcal
cd xtcal
make
```

### Setup Minimal X11

If you are running a X11-less (lite) distri then add minimal server with:

```
sudo apt-get install xserver-xorg xserver-xorg-video-fbdev xinit
```

Allow anybody to startx:

```
sudo vi /etc/X11/Xwrapper.config

allowed_users=anybody
```

Select Framebuffer:

```
sudo vi /usr/share/X11/xorg.conf.d/99-fbdev.conf

Section "Device"  
  Identifier "myfb"
  Driver "fbdev"
  Option "fbdev" "/dev/fb1"
EndSection
```

### Perform Calibration

Run X11 Server for framebuffer once:

```
$ startx &
```

Reset Calibration Matrix:

```
$ DISPLAY=:0.0 xinput set-prop "stmpe-ts" 'Coordinate Transformation Matrix' 1 0 0 0 1 0 0 0 1
```

Run the calibration tool:

```
$ DISPLAY=:0.0 ./xtcal -geometry 320x240
```

Pick the drawn crosshairs and after that you get the matrix reported:

```
xinput set-prop <device name> 'Coordinate Transformation Matrix' 0.015731 -1.135927 1.014818 1.123037 0.017117 -0.062198 0 0 1
```

This calibration matrix is what we need...

Stop X11 again:

```
pkill startx
```

# Store Calibration Matrix

The PiTFT Installer has created a rules file. There we need to add the matrix:

Note: Only the first 6 values are needed.

```
/etc/udev/rules.d/95-stmpe.rules:
SUBSYSTEM=="input", ATTRS{name}=="*stmpe*", ENV{DEVNAME}=="*event*", SYMLINK+="input/touchscreen", ENV{LIBINPUT_CALIBRATION_MATRIX}="1.143981 -0.006342 -0.106502 0.000513 1.102468 -0.044724"
```

Reboot your Pi to make this change active:

```
$ sudo libinput-list-devices
```

[1]: https://octoprint.org/download/
[2]: https://www.adafruit.com/product/2423
[3]: https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi
[4]: https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h
