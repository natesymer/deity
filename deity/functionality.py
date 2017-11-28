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

class AudioFunctionality(object):
  def go(self,
         list_outputs = False, toggle_mute = False,
         output = None, input = None,
         adjust_volume = None):
    with Audio("deity") as a:
      if list_outputs:
        for o in a.outputs:
          print(str(o))

      if toggle_mute:
        a.output.muted = not a.output.muted

      if output != None:
        a.output = output
        a.output.enable()
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
            self.statusbar.print()
        finally:
          conn.close()
    finally:
      try:
        s.close()
      finally:
        if os.path.exists(socketfile):
          os.remove(socketfile)

  def go(self, **kwargs):
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
