from time import sleep
import json
import sys
import os
import pwd
import re
from uuid import uuid4
from socket import socket, AF_UNIX, SOCK_STREAM
from threading import Thread
from deity.hardware.audio import Audio, Input, Output, Stream
from deity.statusitems.date import Date
from deity.statusitems.volume import Volume
from deity.statusitems.network import Network
from deity.statusitems.brightness import Brightness
from deity.statusitems.battery import Battery
from deity.statusbar import StatusBar
from deity.hardware.brightness import get_brightness, set_brightness

def Functionality(key):
  return {
    "audio": AudioFunctionality,
    "brightness": BrightnessFunctionality,
    "screenshot": ScreenshotFunctionality,
    "i3bar": i3barFunctionality
  }.get(key, i3barFunctionality)()

class AudioFunctionality(object):
  def go(self,
         list_outputs = False, toggle_mute = False,
         output = None, input = None,
         adjust_volume = None):
    with Audio("desktop.py") as a:
      if list_outputs:
        for o in a.outputs:
          print(str(o))

      if toggle_mute:
        a.output.muted = not a.output.muted

      if output != None:
        a.output = output
        a.collect_streams()
        for o in a.outputs:
          if o.name != output:
            o.suspend()

      if input != None:
        i = a.named_input(input)
        if i is not None:
          a.input = i
          a.collect_streams()
          for i in a.inputs:
            if i != a.input:
              i.suspend()

      if adjust_volume != None:
        a.output.volume = a.output.volume + int(adjust_volume)
      
      tickle_i3bar()

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

    tickle_i3bar()

class ScreenshotFunctionality(object):
  def go(self, destination = "~/Pictures/screenshots"):
    os.system("mkdir -p " + destination)
    os.system("swaygrab " + destination.rstrip('/') + time.strftime("/%-m-%-d-%y_%-H:%M:%S.png"))

sockregex = re.compile(r'deity\.([^.]*)\.([^.]*)\.sock')
def tickle_i3bar():
  print("TICKLE", file=sys.stderr)
  for fn in os.listdir('/tmp'):
    res = sockregex.match(fn)
    
    if res is not None:
      name, guid = res.groups()
      print(name, file=sys.stderr)
      if name == pwd.getpwuid(os.getuid())[0]:
        s = socket(AF_UNIX, SOCK_STREAM)
        s.connect('/tmp/' + fn)
        s.send(b'foo')
        s.close()

class i3barFunctionality(object):
  def runipc(self):
    socketfile = "/tmp/deity." + pwd.getpwuid(os.getuid())[0] + "."+ str(uuid4()) + ".sock"

    s = socket(AF_UNIX, SOCK_STREAM)
    try:
      s.bind(socketfile)
      s.listen(5)

      while True:
        conn, addr = s.accept()
        data = b''
        while True:
          bs = conn.recv(4096)
          if not bs:
            break
          else:
            data += bs

        if len(data) > 0:
          self.statusbar.print()
    finally:
      if os.path.exists(socketfile):
        os.remove(socketfile)

  def go(self, **kwargs):
    self.statusbar = StatusBar(items = [
      Brightness(backlight = kwargs.get("backlight", "intel_backlight"),
                   backlight_class = kwargs.get("backlight_class", "backlight")),
      Volume(**kwargs),
      Battery(**kwargs),
      Network(text = "WiFi", interface = kwargs.get("wifi_iface", "wlp3s0")),
      Network(text = "VPN", interface = kwargs.get("vpn_iface", "tun0")),
      Date(**kwargs)
    ], **kwargs)
    t = Thread(target=self.runipc)
    t.daemon = True
    t.start()

    self.statusbar.run()

