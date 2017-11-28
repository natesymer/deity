from ..statusbar import StatusItem, Color
from ..hardware.audio import Audio

class Volume(StatusItem):
  def __init__(self, **kwargs):
    super().__init__()
    self.audio = Audio("deity i3bar statusitem")
    self.muted = False
    self.volume_perc = 100

  def refresh(self):
    o = self.audio.output
    self.muted = o.muted
    self.volume_perc = o.volume

  def color(self):
    if self.muted:
      return Color.NEUTRAL
    return Color.POSITIVE

  def full_text(self):
    return "VOL " + str(self.volume_perc) + "%"
