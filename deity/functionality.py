from time import sleep, strftime
import json
import sys
import os
import pwd
import re
from uuid import uuid4
from socket import socket, AF_UNIX, SOCK_STREAM
from threading import Thread
from deity.hardware.audio import Audio, Input, Output, Stream
from deity.statusbar import StatusBar
from deity.hardware.brightness import get_brightness, set_brightness

from pulsectl import Pulse

__pulse = None
def pulse():
  global __pulse
  if __pulse is None:
    __pulse = Pulse("deity")
  return __pulse

__sink = None
def default_sink():
  global __sink
  if __sink is None:
    __sink = pulse().get_sink_by_name("@DEFAULT_SINK@")
  return __sink

__source = None
def default_source():
  global __source
  if __source is None:
    __source = pulse().get_source_by_name("@DEFAULT_SOURCE@")
  return __source

class AudioFunctionality(object):
  def go(self,
         list_outputs = False, toggle_mute = False,
         output = None, input = None,
         adjust_volume = None):
    if output != None:
      pulse().sink_default_set(output)
      __sink = None

    if input != None:
      pulse().source_default_set(input)
      __source = None

    if toggle_mute:
      pulse().sink_mute(default_sink().index, int(not bool(default_sink().mute)))

    if adjust_volume != None:
      new_vol = int(round(default_sink().volume.value_flat * 100)) + int(adjust_volume)
      new_vol_perc = float(min(100, max(0, new_vol))) / 100.0
      pulse().volume_set_all_chans(default_sink(), new_vol_perc)

    # Move all sink inputs to the default sink
    for si in pulse.sink_input_list():
      pulse().sink_input_move(si.index, default_sink().index)

    # Move all source outputs to the default source.
    for so in self.pulse.source_output_list():
      pulse().source_output_move(so.index, default_source().index)

    # Ensure the default sink is the only non-suspended sink
    for sink in pulse().sink_list():
      if list_outputs:
        print(sink.name)
      pulse().sink_suspend(sink.index, int(sink.name != default_sink().name))
    
    # Ensure the default source is the only non-suspended source
    for source in pulse().source_list():
      pulse().source_suspend(source.index, int(sink.name != default_sink().name))

    pulse().close()

    i3barFunctionality.tickle()

class BrightnessFunctionality(object):
  def go(self,
         backlight = "intel_backlight",
         backlight_class = "backlight",
         set = None, adjust = None
         ):
    if set is not None:
      set_brightness(backlight, set, backlight_class)
    else:
      b = get_brightness(backlight, backlight_class)
      if b is not None:
        if adjust is not None:
          set_brightness(backlight, b + adjust, backlight_class)
        else:
          sys.stdout.write(str(b) + '%\n')
      else:
        sys.stdout.write("failed to read brightness.\n")
      sys.stdout.flush()

    i3barFunctionality.tickle()

class ScreenshotFunctionality(object):
  def go(self, destination = "~/Pictures/screenshots"):
    os.system("mkdir -p " + destination)
    os.system("swaygrab " + destination.rstrip('/') + strftime("/%-m-%-d-%y_%-H:%M:%S.png"))

class i3barFunctionality(object):
  sockregex = re.compile(r'deity\.([^.]*)\.([^.]*)\.sock')
  tickle_msg = b'1'

  @classmethod
  def tickle(self):
    uname = pwd.getpwuid(os.getuid())[0]
    for fn in os.listdir('/tmp'):
      res = self.sockregex.match(fn)    
      if res is not None:
        name, guid = res.groups()
        if name == uname:
          try:
            s = socket(AF_UNIX, SOCK_STREAM)
            s.connect('/tmp/' + fn)
            s.send(self.tickle_msg)
          except Exception as e:
            pass
          finally:
            s.close()

  def runipc(self):
    socketfile = "/tmp/deity." + pwd.getpwuid(os.getuid())[0] + "."+ str(uuid4()) + ".sock"

    try:
      s = socket(AF_UNIX, SOCK_STREAM)
      s.bind(socketfile)
      s.listen(5)

      while True:
        conn, addr = s.accept()
        try:
          if conn.recv(len(self.__class__.tickle_msg)) is not None:
            self.statusbar.print(periodic=False)
        finally:
          conn.close()
    finally:
      try:
        s.close()
      finally:
        if os.path.exists(socketfile):
          os.remove(socketfile)

  def go(self, **kwargs)
    eth_iface = kwargs.get("eth_iface", None)
    if eth_iface is not None:
      del kwargs["eth_iface"];
    
    wifi_iface = kwargs.get("wifi_iface", None)
    if wifi_iface is not None:
      del kwargs["wifi_iface"]
    
    vpn_iface = kwargs.get("vpn_iface", None)
    if vpn_iface is not None:
      del kwargs["vpn_iface"]
    
    date_format = kwargs.get("date_format", None)
    if date_format is not None:
      del kwargs["date_format"]
    
    time_format = kwargs.get("time_format", None)
    if time_format is not None:
      del kwargs["time_format"]
    
    kwargs["items"] = [
      Memory,
      CPU,
      Brightness,
      Volume,
      Battery,
      lambda **kwargs: Network(**{**{"text": "\uf0e8", "interface": eth_iface}, **kwargs}),
      lambda **kwargs: Network(**{**{"text": "\uf1eb", "interface": wifi_iface}, **kwargs}),
      lambda **kwargs: Network(**{**{"text": "\uf21b", "interface": vpn_iface}, **kwargs}),
      lambda **kwargs: Date(**{**{"date_format": date_format}, **kwargs}),
      lambda **kwargs: Date(**{**{"date_format": time_format}, **kwargs})
    ]

    self.statusbar = StatusBar(**kwargs)
    t = Thread(target=self.runipc)
    t.daemon = True
    t.start()

    self.statusbar.run()

func_map = {
  "audio": AudioFunctionality,
  "brightness": BrightnessFunctionality,
  "screenshot": ScreenshotFunctionality,
  "i3bar": i3barFunctionality
}

def Functionality(key):
  return func_map.get(key, i3barFunctionality)()
