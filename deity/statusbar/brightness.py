from ..statusbar import StatusItem
from ..hardware.brightness import get_brightness, set_brightness

class Brightness(StatusItem):
  def __init__(self, backlight = "intel_backlight", backlight_class = "backlight"):
    super().__init__()
    self.backlight = backlight
    self.backlight_class = backlight_class

  def full_text(self):
    b = get_brightness(self.backlight, self.backlight_class)
    if b is None:
      return "BRIGHT"
    return "BRIGHT " + str(b) + "%"    

  def color(self):
    b = get_brightness(self.backlight, self.backlight_class)
    if b is None:
      return Color.NEGATIVE
    return Color.POSITIVE
