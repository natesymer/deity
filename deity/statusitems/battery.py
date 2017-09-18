from ..filesystem import read_sys
from ..statusbar import StatusItem, Color

class Battery(StatusItem):
  def __init__(self, power_supply = "BAT0", **kwargs):
    super().__init__()
    self.power_supply = power_supply

  def read(self, fname):
    return read_sys("power_supply", self.power_supply, fname)

  def is_charging(self):
    return self.read("status") == "Charging"

  def percent(self):
    n = self.read("charge_now")
    f = self.read("charge_full")
    if n is None or f is None:
      return -1
    return int((float(n) / float(f)) * 100.0)

  def full_text(self):
    return "BAT " + str(self.percent()) + "%"

  def color(self):
    p = self.percent()
    c = self.is_charging()
    
    if not p or (p <= 20 and not c):
      return Color.NEGATIVE
    return Color.POSITIVE
  
