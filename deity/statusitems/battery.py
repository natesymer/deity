from ..filesystem import read_sys
from ..statusbar import StatusItem, Color

class Battery(StatusItem):
  def __init__(self, power_supply = "BAT0", **kwargs):
    super().__init__()
    self.power_supply = power_supply
    self.percent = -1
    self.is_charging = False

  def refresh(self):
    self.is_charging = self.read("status") == "Charging"
    n = self.read("charge_now")
    f = self.read("charge_full")
    if n is None or f is None:
      self.percent = -1
    else:
      self.percent = int((float(n) / float(f)) * 100.0)

  def read(self, fname):
    return read_sys("power_supply", self.power_supply, fname)

  def full_text(self):
    return "BAT " + str(self.percent) + "%"

  def color(self):
    if self.percent <= 20 and not self.is_charging:
      return Color.NEGATIVE
    return Color.POSITIVE

