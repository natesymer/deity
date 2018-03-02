from ..statusbar import StatusItem, Color
from ..hardware.audio import Audio, AudioForStatusBar

class Volume(StatusItem):
  def __init__(self, **kwargs):
    super().__init__()
    self.audio = AudioForStatusBar("deity i3bar statusitem")
    self.muted = True
    self.volume = -1

  def refresh(self, periodic):
    if not periodic:
      s = self.audio.get_state()
      has_changed = s.muted != self.muted or s.volume != self.volume
      self.muted = s.muted
      self.volume = s.volume
      return has_changed
    return False

  def color(self):
    if self.muted:
      return Color.NEUTRAL
    return Color.POSITIVE

  def full_text(self):
    return "\uf028 " + str(self.volume) + "%"
