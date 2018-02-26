from ..filesystem import read_sys
from ..statusbar import StatusItem, Color
import os

class Network(StatusItem):
  def __init__(self, text = "Network", interface = None, **kwargs):
    super().__init__(**kwargs)
    self.text = text
    if interface is None:
      raise ValueError("Network(): expected interface parameter.")
    self.interface = interface
    self.istuntap = self.interface.startswith("tun", 0, 3) or self.interface.startswith('tap', 0, 3)
    self.connected = False

  def refresh(self, periodic):
    if self.istuntap:
      connected = os.path.isdir("/sys/class/net/" + str(self.interface) + "/")
    else:
      connected = read_sys("net", self.interface, "operstate") == "up"

    has_changed = connected != self.connected
    self.connected = connected
    return has_changed

  def full_text(self):
    return self.text

  def color(self):
    if self.connected:
      return Color.POSITIVE
    else:
      return Color.NEGATIVE
