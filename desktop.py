#!/usr/bin/env python3

"""
desktop.py
Control common desktop functionality without a DE.

Please note that brightness functionality requires access to
/sys/class/backlight/intel_backlight/brightness. Other tools
use setuid (eek) for this functionality

Dependencies:
pulsectl (pip)
pulseaudio (pacman)
"""

from pulsectl import Pulse
from argparse import ArgumentParser
from subprocess import Popen,PIPE
from json import dumps
import time
import os.path
from re import split
from math import floor,log
import sys

def main(args):
  if args.command == "audio":
    with Audio("desktop.py") as a:
      if args.list_outputs:
        for o in a.outputs:
          print(str(o))

      if args.toggle_mute:
        a.output.muted = not a.output.muted

      if args.toggle_mic:
        os.system("patctl set-source-mute @DEFAULT_SOURCE@ toggle")

      o = args.set_output
      if o != None:
        a.output = o

      vol_adj = args.adjust_volume
      if vol_adj != None:
        a.output.volume = a.output.volume + int(vol_adj)

      if args.sanitize:
        a.sanitize()
  elif args.command == "screenshot":
    direc = args.destination.rstrip('/')
    os.system("mkdir -p " + direc)
    os.system("swaygrab " + direc + time.strftime("/%-m-%-d-%y_%-H:%M:%S.png"))
  elif args.command == "i3bar": 
    status(args)
  elif args.command == "brightness":
    if args.auto:
      while True:
        autoadjust_brightness(args.lower_threshold, args.upper_threshold, args.backlight, args.backlight_class)
        time.sleep(5)
    elif args.set is not None:
      set_brightness(args.backlight,int(args.set), args.backlight_class)
    elif args.adjust is not None:
      adjust_brightness(args.backlight, int(args.adjust), args.backlight_class)
    else:
      b = get_brightness(args.backlight, args.backlight_class)
      if b is not None:
        sys.stdout.write(str(b) + '%\n')
      else:
        sys.stdout.write("failed to read brightness: cannot read /sys/class/" + args.backlight_class + "/" + args.backlight + "/*brightness")

#
## DRY
#

def read_file(path):
  with open(path, 'r') as f:
    with f.read() as v:
      return v
  return None

def write_file(path, data):
  with open(path, 'w') as f:
    try:
      f.write(str(data))
      f.flush()
      return True
    except:
      return False
  return False

def read_sys(klass, iface, *props):
  bp = '/'.join(["", "sys", "class", str(klass), str(iface), ""])
  for prop in props:
    v = read_file(bp + prop)
    if v is not None:
      return v.rstrip('\n')
  return None

def write_sys(klass, iface, prop, value):
  pth = '/'.join(["", "sys", "class", str(klass), str(iface), str(prop)])
  return write_file(pth, str(value) + '\n')

#
## Pulse Audio
# Implements a wrapper around the sink/sink-input model of PulseAudio.
#

# An abstraction over PulseAudio
class Audio(object):
  pulses = {}

  def __init__(self, name):
    self.name = name

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

  def close(self):
    if self.pulse is not None:
      self.pulse.close()
      self.pulse = None

  @property
  def pulse(self):
    p = self.__class__.pulses.get(self.name, None)
    if p is None:
      p = Pulse(self.name)
      self.__class__.pulses[self.name] = p
    return p

  @pulse.setter
  def pulse(self, p):
    self.__class__.pulses[self.name] = p

  @property
  def outputs(self):
    return list(map(lambda x: Output(x, self.pulse), self.pulse.sink_list()))

  @property
  def output(self):
    for s in self.pulse.sink_list():
      if s.name == self.pulse.server_info().default_sink_name:
        return Output(s, self.pulse)
    return None

  @output.setter
  def output(self, o):
    pulse().sink_default_set(str(o))

  def sanitize(self):
    pulse().sink_suspend(output().index, 0)
    for si in pulse().sink_input_list():
      pulse().sink_input_move(si.index, output().index)
    for s in pulse().sink_list():
      if s.name != output().name:
        pulse().sink_suspend(s.index, 1)

# An output is an abstraction over a sink.
class Output(object):
  def __init__(self, sink, pulse):
    self.sink = sink
    self.pulse = pulse

  @property
  def volume(self):
    return int(round(self.sink.volume.value_flat * 100))

  @volume.setter
  def volume(self, v):
    vp = v
    if vp < 0:
      vp = 0
    elif vp > 100:
      vp = 100
    self.pulse.volume_set_all_chans(self.sink,float(vp)/100.0)

  @property
  def muted(self):
    return bool(self.sink.mute)

  @muted.setter
  def muted(self, m):
    self.pulse.sink_mute(self.sink.index,int(bool(m)))

  def __str__(self):
    def_name = self.pulse.server_info().default_sink_name
    star = '*' if self.sink.name == def_name else ''
    return ' '.join([str(self.sink.index), ".", self.sink.name, str(self.volume)])

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.sink.index is other.sink.instance
    return NotImplemented

  def __ne__(self, other):
    if isinstance(other, self.__class__):
      return self.sink.index is not other.sink.instance
    return NotImplemented

#
## Brightness
#

# gets a brightness percent (integer)
def get_brightness(iface,klass):
  current = read_sys(klass, iface, "actual_brightness", "brightness")
  if current is None:
    return None
  maximum = read_sys(klass, iface, "max_brightness")
  if maximum is None:
    return None
  return int(round((float(current) / float(maximum)) * 100))

# sets the brightness to a percent (integer)
def set_brightness(iface, percent, klass):
  maximum = read_sys(klass, iface, "max_brightness")
  if maximum is None:
    return False
  percent_p = min(max(percent, 0), 100)
  new_brightness = round((percent_p / 100) * float(maximum))
  return write_sys(klass, iface, "brightness", new_brightness)

def adjust_brightness(iface, delta_perc, klass):
  brightness = get_brightness(iface, klass)
  if brightness is not None:
    return set_brightness(iface, brightness + delta_perc, klass)
  else:
    return False

def read_apple_als():
  return int(read_file("/sys/devices/platform/applesmc.768/light")[1:-4])

prev_als = None
def autoadjust_brightness(lowp, highp, iface, klass):
  global prev_als
  als = read_apple_als()
  if prev_als is not als:
    prev_als = als
    alsp = 0 if als is 0 else log(als, 10) / log(255 / 10)
    v = lowp + (alsp * (highp - lowp))
    set_brightness(iface, v, klass)

#
## Wifi
#

def is_conn_to(iface):
  return iface in read_file("/proc/net/if_inet6")

#
## Status Bar
#

# TODO: mouse clicks

normal_color = "#FFFFFF"
replenishing_color = "#BDC1DB"
degraded_color = "#B87A84"

audio = None

def status(args):
  global audio
  sys.stdout.write("{\"version\":1}\n[\n")
  statusline(args)
  sys.stdout.flush()
  time.sleep(args.refresh_interval) 
  while True:
    statusline(args,True) 
    sys.stdout.flush()
    time.sleep(args.refresh_interval)
  if audio is not None:
    audio.close()

# TODO: detect all network devices via /sys/class/net.
# then, device prefixes:
#  en - ethernet
#  wl - wlan
#  ww - wwan
#  sl - serial line IP
# each of these will need strings in arguments

def statusline(args,prepend_comma=False):
  items = [
    brightness(args.backlight),
    volume(args.color_full, args.color_half_empty),
    battery(args.power_supply),
    network("wifi", args.wifi_iface, "", args.color_full, args.color_empty),
    # TODO: ethernet
    # TODO: unified network section
    network("vpn", "tun0", "VPN", args.color_full, args.color_empty), # NetworkManager default
    date(args.color_full, args.date_format)
  ]
  prefix = ',' if prepend_comma else ''
  sys.stdout.write(prefix + '[' + ','.join(items) + ']\n')

def date(color, fmt):
  return statusd("time", "local", color, time.strftime(fmt))

# TODO: have this only read the file once
def network(klass, iface, text, color_on, color_off):
  return statusd(klass, iface, color_on if is_conn_to(iface) else color_off, text)

def battery(device):
  uevent = read_sys("power_supply", device, "uevent")
  if uevent is None:
    return statusd("battery", device, degraded_color, "")
  else:
    info = dict([l.split('=') for l in uevent.split('\n')])
    ischarging = info["POWER_SUPPLY_STATUS"] == "Charging"
    energy_now = float(info["POWER_SUPPLY_ENERGY_NOW"])
    energy_full = float(info["POWER_SUPPLY_ENERGY_FULL"])
    bat_perc = int(floor((energy_now / energy_full) * 100))
    
    if ischarging:
      bat_color = replenishing_color
    elif bat_perc <= 20:
      bat_color = degraded_color
    else:
      bat_color = normal_color

    return statusd("battery", device, bat_color, " " + str(bat_perc) + "%")

def volume(color, mutecolor):
  global audio
  if audio is None:
    audio = Audio("desktop.py i3bar")

  return statusd("volume",
                 "pulseaudio",
                 mutecolor if audio.output.muted else color,
                 " " + str(audio.output.volume) + "%")

def brightness(backlight):
  b = get_brightness(backlight, "backlight")
  return statusd("brightness",
                 backlight,
                 normal_color if b is not None else degraded_color,
                 "☀ " + str(b) + "%" if b is not None else "☀")

def statusd(name,instance,color,text,max_text=None):
  return ''.join([
    "{\"name\":\"",
    str(name),
    "\",\"instance\":\"",
    str(instance),
    "\",\"color\":\"",
    str(color),
    "\",\"full_text\":\"",
    str(text),
    "\"}"
  ])

# TODO: Screen brightness adjustment via ALS:
# /sys/devices/platform/applesmc.768/light

main_parser = ArgumentParser(description="Control a Linux desktop without a DE.")
subparsers = main_parser.add_subparsers(title="commands", dest="command")

screenshot_parser = subparsers.add_parser("screenshot", help="take a screenshot")
screenshot_parser.add_argument("--destination", help="Where to save the screenshot", default="~/Pictures/screenshots")

audio_parser = subparsers.add_parser("audio", help="control audio")
audio_parser.add_argument("--adjust-volume", metavar="INTEGER", help="Adjust audo volume", type=int)
audio_parser.add_argument("--toggle-mute", help="Toggle audo mute", action="store_true")
audio_parser.add_argument("--toggle-mic", help="Toggle microphone", action="store_true")
audio_parser.add_argument("--set-output", metavar="INTEGER", help="Set the active audio sink", type=int)
audio_parser.add_argument("--list-outputs", help="Print a listing of sinks", action='store_true')
audio_parser.add_argument("--sanitize", help="Ensure all sources of audio use the default sink", action='store_true')

brightness_parser = subparsers.add_parser("brightness", help="control brightness")
brightness_parser.add_argument("--backlight", metavar="NAME", help="The name of your backlight in /sys/class/<SYSCLASS>", default="intel_backlight")
brightness_parser.add_argument("--backlight-class", metavar="SYSCLASS", help="The class of your backlight in /sys/class/", default="backlight")
brightness_parser.add_argument("--adjust", metavar="INTEGER", help="Adjust the brightness by INTEGER")
brightness_parser.add_argument("--set", metavar="INTEGER", help="Set the brightness to INTEGER")
brightness_parser.add_argument("--auto", help="Use the built-in ALS to adjust brightness", action="store_true")
brightness_parser.add_argument("--lower-threshold", metavar="INTEGER", help="The minimum brightness to use", type=int, default=10)
brightness_parser.add_argument("--upper-threshold", metavar="INTEGER", help="The maximum brightness to use", type=int, default=90)

i3bar_parser = subparsers.add_parser("i3bar", help="i3bar-compliant status bar daemon")
i3bar_parser.add_argument("--date-format", metavar="FORMAT", help="Display a strftime in the statusbar using FORMAT", default="%-m.%-d.%y   %-I:%M %p")
i3bar_parser.add_argument("--refresh-interval", metavar="FLOAT", help="Set the refresh interval", type=float, default=0.5)
i3bar_parser.add_argument("--color-full", metavar="HEXCOLOR", help="The default color of text on the status bar", default="#FFFFFF")
i3bar_parser.add_argument("--color-half-full", metavar="HEXCOLOR", help="Text color used to indicate something is changing for the better", default="#BDC1DB")
i3bar_parser.add_argument("--color-empty", metavar="HEXCOLOR", help="Text color used to indicate a dire condition", default="#B87A84")
i3bar_parser.add_argument("--color-half-empty", metavar="HEXCOLOR", help="Text color used when something is changing (or changed) for the worse", default="#AAAAAA")
i3bar_parser.add_argument("--power-supply", metavar="POWER_SUPPLY", help="Power supply for which to report percentage", default="BAT0")
i3bar_parser.add_argument("--wifi-iface", metavar="INTERFACE", help="Wi-Fi interface for which to report status", default="wlp3s0")
i3bar_parser.add_argument("--backlight", metavar="NAME", help="The name of your backlight in /sys/class/backlight", default="intel_backlight")
i3bar_parser.add_argument("--enable-clicks", help="Enable clicks from i3bar", action="store_true")
main(main_parser.parse_args())
