from ..statusbar import StatusItem, Color
from ..hardware.audio import Audio

class Volume(StatusItem):
  def __init__(self, **kwargs):
    super().__init__()
    self.audio = Audio("deity i3bar")

  def color(self):
    if self.audio.output.muted:
      return Color.NEUTRAL
    return Color.POSITIVE

  def full_text(self):
    return "VOL " + str(self.audio.output.volume) + "%"
