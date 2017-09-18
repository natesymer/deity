from ..statusbar import StatusItem, Color
from ..hardware.brightness import get_brightness, set_brightness

class Brightness(StatusItem):
  def __init__(self, backlight = "intel_backlight", backlight_class = "backlight", **kwargs):
    super().__init__()
    self.backlight = backlight
    self.backlight_class = backlight_class

  def refresh(self):
    self.brightness = get_brightness(self.backlight,
                                     self.backlight_class)    

  def full_text(self):
    if self.brightness is None:
      return "BRIGHT"
    return "BRIGHT " + str(self.brightness) + "%"

  def color(self):
    if self.brightness is None:
      return Color.NEGATIVE
    return Color.POSITIVE
