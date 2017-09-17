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
import subprocess
import pwd
import shlex

#
## XKB Keysyms
#

ctx = xkb.Context()
keymap = ctx.keymap_new_from_names()
state = keymap.state_new()

def map_keycode(keycode):
  if type(keycode) is str:
    return keycode
  
  raw = xkb.keysym_get_name(state.key_get_one_sym(keycode + keymap.min_keycode() - 1))
  if raw == "NoSymbol":
    return None
  elif '_' in raw:
    return raw.split('_')[0]
  else:
    return raw

#
## Configuration
#

def ls(direc):
  xs = []
  for dpth, _, fnames in os.walk(direc):
    for f in fnames:
      xs.append(os.path.abspath(os.path.join(dpth, f)))
  return xs

def load_config(f):
  c = configparser.ConfigParser()
  c.read(f)
  return c

def config_true(c, k):
  return str(c.get(k, "")).lower() == "true"

paths = ls("/etc/kbmapper/kbmapper.d/")
paths.append("/etc/kbmapper/kbmapper.conf")
configs = list(map(load_config, paths))

#
## Event Handling
#

# Takes: a list of keysyms
# Returns: (reset_stack, pop_stack)
def emit(keys):
  not_none = lambda v: v is not None
  keysym = '+'.join(list(filter(not_none, map(map_keycode, keys))))
  for cfg in configs:
    if keysym in cfg:
      v = cfg[keysym]
      cmd = v.get("Exec", None) # Command to execute on event
      if cmd is not None:
        subproc(
          cmd,
          cwd=v.get("Directory", None),
          user=v.get("User", None),
          xdg=config_true(v, "NeedsXDG"),
          dbus=config_true(v, "NeedsDBus"),
          wayland=config_true(v, "NeedsWayland"),
          sway=config_true(v, "NeedsSway")
        )
        return (not config_true(v, "AllowsRepeat"), False)
  return (False, True)

#
## Event Implementation
#

stack = []

def handle_key(keycode, pressed, isrepeat):
  global stack
  if pressed and not isrepeat:
    if keycode not in stack:
      stack.append(keycode)
  else:
    if keycode in stack:
      reset_stack, pop_stack = emit(stack)
      if reset_stack:
        stack = []
      elif pop_stack or not isrepeat:
        stack.remove(keycode)

# TODO: make lid and audiojack events behave more like keys
def handle_lid(closed):
  global stack
  emit(stack + ["LidClosed" if closed else "LidOpen"])

def handle_audiojack(plugged):
  global stack
  emit(stack + ["AudioPlugged" if plugged else "AudioUnplugged"])

def handle_event(code, typ, value):
  if typ is 1:
    handle_key(code, value > 0, value == 2)
  elif typ is 5:
    if code is 0:
      handle_lid(value is 1)
    elif code is 2: # headphone jack event
      handle_audiojack(value is 1)

#
## Evdev Listener
#

@asyncio.coroutine
def listen_events(d):
  cur_ev = None
  while True:
    events = yield from d.async_read()
    for e in events:
      if e.type is 0: # EV_SYN
        if cur_ev is not None:
          # TODO: handle EV_SYN behavior
          handle_event(cur_ev.code, cur_ev.type, cur_ev.value)
          cur_ev = None
      else:
        cur_ev = e

#
## Subprocess
#

# TODO: don't execute command if xdg, dbus, wayland, or sway is not found.
def subproc(cmd, cwd=None, user=None, xdg=False, dbus=False, wayland=False, sway=False):
  env = os.environ.copy()
  pw = pwd.getpwnam(user if user is not None else env['USER'])
  # env.clear()
  wd = cwd if cwd is not None else pw.pw_dir
  print(cmd, pw.pw_name, wd, xdg)
  env['HOME'] = pw.pw_dir
  env['LOGNAME'] = pw.pw_name
  env['PWD'] = wd
  env['USER'] = pw.pw_name
  if xdg:
    runtime_dir = "/run/user/" + str(pw.pw_uid)
    env['XDG_RUNTIME_DIR'] = runtime_dir
    env['XDG_CONFIG_HOME'] = pw.pw_dir + "/.config"
    for pth in ls(runtime_dir):
      fname = pth.split('/')[-1]
      if dbus and fname == "bus":
        env['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=' + pth
      elif wayland and "wayland" in fname and "lock" not in fname:
        env['WAYLAND_DISPLAY'] = fname
      elif sway and "sway-ipc" in fname:
        v = runtime_dir + '/' + fname
        env['SWAYSOCK'] = v
        env['I3SOCK'] = v
  uid = pw.pw_uid
  gid = pw.pw_gid
  def demote():
    os.setgid(gid)
    os.setuid(uid)
  p = subprocess.Popen(cmd, preexec_fn=demote, cwd=wd, env=env, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  print(p.communicate())

#
## Main
#

def main(args):
  for fn in evdev.list_devices():
    d = evdev.InputDevice(fn)
    c = d.capabilities()
    if 1 in c or 5 in c: # 1 is EV_KEY and 5 is EV_SW
      # TODO: get keyboard, lid, and headphone jack status before running
      asyncio.async(listen_events((d)))

  loop = asyncio.get_event_loop()
  
  def signal_handler(signal, frame):
    loop.stop()
    sys.exit(0)

  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  loop.run_forever()

main(sys.argv)
