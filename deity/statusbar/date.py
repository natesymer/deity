import time
from ..statusbar import StatusItem

class Date(StatusItem):
  def __init__(self, date_format="%-m.%-d.%y  %-I:%M %p"):
    super().__init__()
    self.format = date_format

  def full_text(self):
    return time.strftime(self.format)
