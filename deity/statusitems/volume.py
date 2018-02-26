from ..statusbar import StatusItem, Color
from ..hardware.audio import Audio, AudioForStatusBar

class Volume(StatusItem):
  def __init__(self, **kwargs):
    super().__init__()
    self.audio = AudioForStatusBar("deity i3bar statusitem")
    self.muted = True
    self.volume = -1

  def refresh(self):
    s = self.audio.get_state()
    self.has_changed = s.muted != self.muted or s.volume != self.volume
    self.muted = s.muted
    self.volume = s.volume

  def color(self):
    if self.muted:
      return Color.NEUTRAL
    return Color.POSITIVE

  def full_text(self):
    return "VOL " + str(self.volume) + "%"
