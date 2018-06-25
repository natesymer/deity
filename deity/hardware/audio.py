from pulsectl import Pulse, PulseSinkInfo, PulseSourceInfo

class AudioForStatusBar(object):
  instances = {}
  def __init__(self, name):
    self.instance = self.__class__.instances.get(name) or Pulse(name)
    self.__class__.instances[name] = self.instance

  def get_state(self):
    sink = self.instance.get_sink_by_name("@DEFAULT_SINK@")
    muted = bool(sink.mute)
    volume = int(round(sink.volume.value_flat * 100))
    return AudioState(volume, muted)

class AudioState(object):
  def __init__(self, volume, muted):
    self.volume = volume
    self.muted = muted


