#!/usr/bin/env python3

"""
desktop.py
Control common desktop functionality without a DE.

Please note that brightness functionality requires access to
/sys/class/backlight/intel_backlight/brightness. Other tools
use setuid (eek) for this functionality.

TODO: backlight setup

Dependencies:
pulseaudio (pacman)
"""

from argparse import ArgumentParser
from subprocess import Popen,PIPE
from json import dumps
import time
import os.path
from re import split
from math import floor,log
import sys

from .hardware.audio import Audio, Input, Output, Stream

def main(args):
  if args.command == "audio":
    with Audio("desktop.py") as a:
      if args.list_outputs:
        for o in a.outputs:
          print(str(o))

      if args.toggle_mute:
        a.output.muted = not a.output.muted

      if args.toggle_mic:
        a.input.muted = not a.input.muted

      o = args.set_output
      if o != None:
        a.output = o

      vol_adj = args.adjust_volume
      if vol_adj != None:
        a.output.volume = a.output.volume + int(vol_adj)

      if args.sanitize:
        a.collect_streams()
        for o in a.outputs():
          if o != a.output:
            o.suspend()
        for i in a.inputs():
          if i != a.input:
            i.suspend()

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
## Brightness
#

# DRY

def read_file(path):
  try:
    f = open(path, 'r')
    v = f.read()
    f.close()
    return v
  except:
    return None

def read_sys(klass, iface, *props):
  bp = '/'.join(["", "sys", "class", str(klass), str(iface), ""])
  for prop in props:
    v = read_file(bp + prop)
    if v is not None:
      return v.rstrip('\n')
  return None

def write_sys(klass, iface, prop, value):
  pth = '/'.join(["", "sys", "class", str(klass), str(iface), str(prop)])
  try:
    fp = open(pth, 'w')
    fp.write(str(value) + '\n')
    fp.flush()
    fp.close()
    return True
  except:
    return False

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

#
## Wifi
#

def is_conn_to(iface):
  return iface in read_file("/proc/net/if_inet6")

#
## Status Bar
#

audio = None

def status(args):
  global audio
  sys.stdout.write("{\"version\":1}\n[\n")
  statusline(args, False)
  time.sleep(args.refresh_interval) 
  while True:
    statusline(args, True) 
    time.sleep(args.refresh_interval)
  if audio is not None:
    audio.close()

def statusline(args, prepend_comma):
  items = [
    brightness(args.backlight, args.color, args.color_dire),
    volume(args.color, args.color_degrading),
    battery(args.power_supply, args.color, args.color_improving, args.color_dire),
    network(args.wifi_iface, "", args.color, args.color_dire),
    network(args.vpn_iface, "VPN", args.color, args.color_dire),
    date(args.color, args.date_format)
  ]
  prefix = ',' if prepend_comma else ''
  sys.stdout.write(prefix + '[' + ','.join(items) + ']\n')
  sys.stdout.flush()

def date(color, fmt):
  return statusd(color, time.strftime(fmt))

def network(iface, text, color_on, color_off):
  return statusd(color_on if is_conn_to(iface) else color_off, text)

def battery(device, normal, charging, dire):
  uevent = read_sys("power_supply", device, "uevent")
  if uevent is None:
    return statusd(dire, "")
  else:
    info = dict([l.split('=') for l in uevent.split('\n')])
    ischarging = info["POWER_SUPPLY_STATUS"] == "Charging"
    energy_now = float(info["POWER_SUPPLY_ENERGY_NOW"])
    energy_full = float(info["POWER_SUPPLY_ENERGY_FULL"])
    bat_perc = int(floor((energy_now / energy_full) * 100))
    
    if ischarging:
      bat_color = charging
    elif bat_perc <= 20:
      bat_color = dire
    else:
      bat_color = normal

    return statusd(bat_color, " " + str(bat_perc) + "%")

def volume(color, mutecolor):
  global audio
  if audio is None:
    audio = Audio("desktop.py i3bar")

  return statusd(mutecolor if audio.output.muted else color,
                 " " + str(audio.output.volume) + "%")

def brightness(backlight, normal, degraded):
  b = get_brightness(backlight, "backlight")
  return statusd(normal if b is not None else degraded,
                 "☀ " + str(b) + "%" if b is not None else "☀")

def statusd(color, text):
  return ''.join([
    "{\"color\":\"",
    str(color),
    "\",\"full_text\":\"",
    str(text),
    "\"}"
  ])

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
i3bar_parser.add_argument("--color", metavar="HEXCOLOR", help="Default text color", default="#FFFFFF")
i3bar_parser.add_argument("--color-improving", metavar="HEXCOLOR", help="Text color used to indicate something is improving", default="#BDC1DB")
i3bar_parser.add_argument("--color-dire", metavar="HEXCOLOR", help="Text color used to indicate a dire condition", default="#B87A84")
i3bar_parser.add_argument("--color-degrading", metavar="HEXCOLOR", help="Text color used when something is changing (or changed) for the worse", default="#AAAAAA")
i3bar_parser.add_argument("--power-supply", metavar="POWER_SUPPLY", help="Power supply for which to report percentage", default="BAT0")
i3bar_parser.add_argument("--wifi-iface", metavar="INTERFACE", help="Wi-Fi interface for which to report status", default="wlp3s0")
i3bar_parser.add_argument("--vpn-iface", metavar="INTERFACE", help="VPN/tunnel interface for which to report status", default="tun0") # NetworkManager defaults VPN connections to tun0
i3bar_parser.add_argument("--backlight", metavar="NAME", help="The name of your backlight in /sys/class/backlight", default="intel_backlight")
main(main_parser.parse_args())
