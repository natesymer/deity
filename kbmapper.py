#!/usr/bin/env python3

# IDEA:
#Use evdev and the system locale to bind key combinations to
# arbitrary shell commands.

# Configuration:
# 
# Typical GLib key-value config format. Each section represents
# a stimulus:
# 
# - `lid_open`
# - `lid_close`
# - `headphones_in`
# - `headphones_out`
# - XKB keysyms composed together with `+`
#
# For each section, there is a single key, `Exec`. When this
# stimulus is activated, the command specified by `Exec` will
# be executed.
#
# Config is either stored in /etc/kbmapper/kbmapper.conf
# or in separate files /etc/kbmapper/kbmapper.d/*.conf
#
# Typical linux config precendence follows.

import configparser
import atexit
import asyncio
import evdev
from xkbcommon import xkb
import sys
import os
import signal

ctx = xkb.Context()
keymap = ctx.keymap_new_from_names()
state = keymap.state_new()

def ls(direc):
  for dpth, _, fnames in os.walk(direc):
    for f in fnames:
      yield os.path.abspath(os.path.join(dpth, f))

def load_config(f):
  c = configparser.ConfigParser()
  c.read(f)
  d = {}
  for sec in c:
    d[sec] = c[sec].get("Exec", None)
  return d

# TODO: kbmapper.d config isn't loaded yet.

config = load_config("./kbmapper.conf")

def map_keycode(keycode):
  raw = xkb.keysym_get_name(state.key_get_one_sym(keycode + keymap.min_keycode() - 1))
  if raw == "NoSymbol":
    return None
  elif '_' in raw:
    return raw.split('_')[0]
  else:
    return raw

def emit_keystroke(keycodes):
  keysyms = [map_keycode(kc) for kc in keycodes]
  cmd = config.get('+'.join(keysyms), None)
  if cmd is not None:
    print(os.system(cmd))
    return True
  return False

def emit_lid(closed=False):
  v = "close" if closed else "open"
  cmd = config.get("lid_" + v, None)
  if cmd is not None:
    print(os.system(cmd))
    return True
  return False

def emit_headphone(plugged_in=False):
  cmd = config.get("headphones_" + ("in" if plugged_in else "out"), None)
  if cmd is not None:
    print(os.system(cmd))
    return True
  return False

# TODO: block event propagation if accepted as a binding

keystack = []
cur_ev = None

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
        cur_ev = None

# GET DEVICES FROM EVDEV
# We want:
# All EV_KEY (1)
# EV_SW (5) -> [SW_LID]

# TODO: listen for new devices!

for fn in evdev.list_devices():
  d = evdev.InputDevice(fn)
  c = d.capabilities()
  if 1 in c or 5 in c:
    asyncio.async(listen_events((d)))

loop = asyncio.get_event_loop()
  
def signal_handler(signal, frame):
  loop.stop()
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

loop.run_forever()
