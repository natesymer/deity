from ..statusbar import StatusItem, Color
from ..hardware.brightness import get_brightness, set_brightness
import sys

class Brightness(StatusItem):
  def __init__(self, backlight = "intel_backlight", backlight_class = "backlight", **kwargs):
    super().__init__(**kwargs)
    self.brightness = -1
    self.backlight = backlight
    self.backlight_class = backlight_class

  def refresh(self, periodic):
    brightness = get_brightness(self.backlight, self.backlight_class)
    has_changed = brightness != self.brightness
    self.brightness = brightness
    return has_changed

  def full_text(self):
    if self.brightness is None:
      return "BRIGHT ERROR"
    return "BRIGHT " + str(self.brightness) + "%"

  def color(self):
    if self.brightness is None:
      return Color.NEGATIVE
    return Color.POSITIVE
