from ..filesystem import read_sys
from ..statusbar import StatusItem, Color

class Battery(StatusItem):
  LOW_BAT_THRESHOLD = 20

  def __init__(self, power_supply = "BAT0", **kwargs):
    super().__init__()
    self.power_supply = power_supply
    self.percent = -1
    self.is_charging = None

  def refresh(self, periodic):
    capacity = int(self.read("capacity") or -1)

    # There is no reason to update the charging status is battery is not low.
    if capacity <= self.LOW_BAT_THRESHOLD and capacity != -1:
      is_charging = self.read("status") == "Charging"
    else:
      is_charging = None

    has_changed = capacity != self.percent or is_charging != self.is_charging
    self.percent = capacity
    self.is_charging = is_charging
    return has_changed

  def read(self, fname):
    return read_sys("power_supply", self.power_supply, fname)

  def full_text(self):
    return "\uf240 " + str(self.percent) + "%"

  def color(self):
    if self.percent <= self.LOW_BAT_THRESHOLD and not self.is_charging:
      return Color.NEGATIVE
    return Color.POSITIVE

