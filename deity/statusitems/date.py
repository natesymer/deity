import time

import deity.statusbar
from deity.statusbar import StatusItem

class Date(StatusItem):
  def __init__(self, date_format="%-m.%-d.%y  %-I:%M %p", **kwargs):
    super().__init__()
    self.format = date_format
    self.date_string = ""

  def refresh(self):
    ds = time.strftime(self.format)
    self.has_changed = ds != self.date_string
    self.date_string = ds

  def full_text(self):
    return self.date_string
