Deity
==

DE features without a DE.

First, make sure you have libpulse and pulseaudio installed. Then,
`pip install -r requirements.txt`. Finally, you can run `pip install .`
Also note that the brightness functionality needs to be enabled. Included is a udev rule that can help. It grants access to /sys/class/backlight/intel_backlight/brightness & friends to a group called video. You must add your user to video.

KBMAPPER.PY
=

DEPENDENCIES:

- `evdev`

Provides configurable keybinding functionality.
