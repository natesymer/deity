from ..statusbar import StatusItem, Color
from ..hardware.brightness import get_brightness, set_brightness
import sys

class Brightness(StatusItem):
  def __init__(self, backlight = "intel_backlight", backlight_class = "backlight", **kwargs):
    super().__init__(**kwargs)
    self.brightness = 0
    self.backlight = backlight
    self.backlight_class = backlight_class

  def refresh(self):
    brightness = get_brightness(self.backlight, self.backlight_class)
    self.has_changed = brightness != self.brightness
    sys.stderr.write("Brightness changed? " + str(self.has_changed) + "\n")
    sys.stderr.flush()
    self.brightness = brightness

  def full_text(self):
    if self.brightness is None:
      return "BRIGHT ERROR"
    return "BRIGHT " + str(self.brightness) + "%"

  def color(self):
    if self.brightness is None:
      return Color.NEGATIVE
    return Color.POSITIVE
