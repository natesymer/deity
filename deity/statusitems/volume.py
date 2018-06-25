from ..statusbar import StatusItem, Color

from pulsectl import Pulse

class Volume(StatusItem):
  def __init__(self, **kwargs):
    super().__init__()
    self.pulse = Pulse("deity i3bar statusitem")
    self.muted = True
    self.volume = -1

  def refresh(self, periodic):
    if not periodic:
      sink = self.pulse.get_sink_by_name("@DEFAULT_SINK@")
      muted = bool(sink.mute)
      volume = int(round(sink.volume.value_flat * 100))
      has_changed = muted != self.muted or volume != self.volume
      self.muted = muted
      self.volume = volume
      return has_changed
    return False

  def color(self):
    if self.muted:
      return Color.NEUTRAL
    return Color.POSITIVE

  def full_text(self):
    return "\uf028 " + str(self.volume) + "%"
