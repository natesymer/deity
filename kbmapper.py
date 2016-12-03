#!/usr/bin/env python3

# IDEA:
#Use evdev and the system locale to bind key combinations to
# arbitrary shell commands.

# Configuration:
# lid_open=echo "lid opened."
# lid_close=echo "lid closed."
# headphones_in=echo "headphones in."
# headphones_out=echo "headphones out."
# <keysym>

# Configuration: (GLib format)
#
#     [lidopen]
#     # Exec=
#
#     [lidclose]
#     # Exec=
#
#     [heaphonesin]
#     # Exec=
#
#     [headphonesout
#
#     [<keysym>]
#     # Exec=
#
# Either add to /etc/kbmapper/kbmapper
#
# /etc/kbmapper/mappings.d/
#
# TODO: configure via glib
# https://github.com/joehakimrahme/Agros/wiki/Parsing-the-conf-file-with-GLib

import asyncio
import evdev
from xkbcommon import xkb

ctx = xkb.Context()
keymap = ctx.keymap_new_from_names()
state = keymap.state_new()
# TODO: block event propagation if accepted as a binding

def map_keycode(keycode):
  return xkb.keysym_to_string(state.key_get_one_sym(keycode + keymap.min_keycode() - 1))

def emit_keystroke(keycodes):
  keysyms = [map_keycode(kc) for kc in keycodes]
  print("Pressed: " + str(keysyms))
  return False

def emit_lid(closed=False):
  print("Lid closed: " + str(closed))
  return True

def emit_headphone(plugged_in=False):
  print("Headphones plugged in: " + str(plugged_in))
  return True

keystack = []
cur_ev = None

# 163 (track next)
# 165 (track prev)

@asyncio.coroutine
def listen_events(d):
  global keystack
  global cur_ev
  while True:
    events = yield from d.async_read()
    for e in events:
      if e.type is 1:         # Key action
        if e.value is 1: # press down
          if e.code not in keystack:
            keystack.append(e.code)
        elif e.value is 0: # lift up
          if e.code in keystack:
            if emit_keystroke(keystack): # The keystack was recognized as a keybinding
              keystack = []
            else:
              keystack.remove(e.code)
      elif e.type is 5:
        cur_ev = (e.code, e.value)
      elif e.type is 0:
        if cur_ev is not None and cur_ev[0] is 0: # lid event
          emit_lid(cur_ev[1] == 0)
        if cur_ev is not None and cur_ev[0] is 2: # headphone jack event 
          emit_headphone(cur_ev[1] is 1)

# GET DEVICES FROM EVDEV
# We want:
# All EV_KEY (1)
# EV_SW (5) -> [SW_LID]

# TODO: listen for new devices!

for fn in evdev.list_devices():
  d = evdev.InputDevice(fn)
  c = d.capabilities()
  if 1 in c or 5 in c:
   # print(d)
   # print({1: c.get(1, None), 5: c.get(5, None)})
    asyncio.async(listen_events((d)))
  # print(d.name, d.capabilities(verbose=True), sep=": ")

loop = asyncio.get_event_loop()
loop.run_forever()
