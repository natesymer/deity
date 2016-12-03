#!/usr/bin/env python3

# IDEA:
# Use evdev and the system locale to bind key combinations to
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

# TODO: 
# 1. Stop event propagation if an event is recognized
# 2. Detect new devices (hotplug)
# 3. Multitouch gestures for trackpads

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
  return c

configs = list(map(load_config, ls("/etc/kbmapper/kbmapper.d/").append("/etc/kbmapper/kbmapper.conf")))

def exec_config(key):
  for cfg in configs:
    if k in cfg:
      v = cfg[k]
      cmd = v.get("Exec", None)
      if cmd is not None:
        print(os.system(cmd))
        return True
  return False
      

def map_keycode(keycode):
  raw = xkb.keysym_get_name(state.key_get_one_sym(keycode + keymap.min_keycode() - 1))
  if raw == "NoSymbol":
    return None
  elif '_' in raw:
    return raw.split('_')[0]
  else:
    return raw

def emit_keystroke(keycodes):
  return exec_config('+'.join(list(map(map_keycode,keycodes))))

def emit_lid(closed=False):
  return exec_config("lid_close" if closed else "lid_open")

def emit_headphone(plugged_in=False):
  return exec_config("headphones_" + ("in" if pluggen_in else "out"))

keystack = []
cur_ev = None

# TODO: key events need to be synchronized!!!
# (or maybe synchronization makes keys too slow!)
@asyncio.coroutine
def listen_events(d):
  global keystack
  global cur_ev
  while True:
    events = yield from d.async_read()
    for e in events:
      if e.type is 1: # Key action
        if e.value is 1: # press down
          if e.code not in keystack:
            keystack.append(e.code)
        elif e.value is 0: # lift up
          if e.code in keystack:
            if emit_keystroke(keystack):
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

for fn in evdev.list_devices():
  d = evdev.InputDevice(fn)
  c = d.capabilities()
  if 1 in c or 5 in c: # 1 is EV_KEY and 5 is EV_SW
    asyncio.async(listen_events((d)))

loop = asyncio.get_event_loop()
  
def signal_handler(signal, frame):
  loop.stop()
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

loop.run_forever()
