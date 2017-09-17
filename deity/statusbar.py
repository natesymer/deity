import sys
import json
from enum import Enum
from uuid import uuid4
from thread import start_new_thread

class Color(Enum):
  POSITIVE = 1
  NEUTRAL = 2
  NEGATIVE = 3

class StatusBar(object):
  def __init__(self,
               clicks_enabled = True,
               refresh_interval = 0.5,
               positive_color = "#FFFFFF",
               neutral_color = "#AAAAAA",
               negative_color = "#B87A84"
               *args):
    super().__init__()
    self.items = args
    self.clicks_enabled = clicks_enabled

  def header(self):
    if self.clicks_enabled:
      return "{\"version\":1,\"click_events\":true}\n[\n"
    return "{\"version\":1}\n[\n"

  def to_dict(self, item):
    c = item.color()
    if c == Color.POSITIVE:
      ch = positive_color
    elif c == Color.NEUTRAL:
      ch = neutral_color
    elif c == Color.NEGATIVE:
      ch = negative_color

    return {
      "instance": item.guid,
      "color": ch or "#FFFFFF",
      "full_text": str(item.full_text),
      "markup": "pango" if item.is_markup() else "none"
    }

  def __str__(self):
    return json.dumps(list(map(self.to_dict, self.items))) + '\n'

  def print(self):
    sys.stdout.write(',' + str(self))
    sys.stdout.flush()

  def run(self):
    sys.stdout.write(self.header() + str(self))
    sys.stdout.flush()
    if self.clicks_enabled:
      start_new_thread(self.read_clicks)
    sleep(refresh_interval) 
    while True:
      sys.stdout.write(',' + str(self))
      sys.stdout.flush()
      sleep(refresh_interval)

  def read_clicks(self):
    s = sys.stdin.read()
    if s is not None and len(s) > 0:
      v = json.load(s)
      instance = str(v["instance"])
      button = int(v["button"])
      if button == 1:
        for i in self.items:
          if i.guid == instance:
            i.on_click()
    
class StatusItem(object):
  def __init__(self, **kwargs):
    super().__init__()
    self.guid = uuid4()

  def is_markup(self):
    return False

  def full_text(self):
    return ""

  def color(self):
    return Color.POSITIVE

  def on_click(self):
    pass
