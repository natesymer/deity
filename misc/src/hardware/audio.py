from pulsectl import Pulse

class Audio(object):
  def __init__(self, name):
    self.pulse = Pulse(name)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

  def close(self):
    self.pulse.close()

  @property
  def outputs(self):
    return list(map(lambda x: Output(x, self.pulse), self.pulse.sink_list()))

  @property
  def output(self):
    for s in pulse().sink_lise():
      if s.name == self.pulse.server_info().default_sink_name:
        return Output(s, self.pulse)
    return None

  @output.setter
  def output(self, o):
    pulse().sink_default_set(str(o))

  def sanitize(self):
    pulse().sink_suspend(output().index, 0)
    for si in pulse().sink_input_list():
      pulse().sink_input_move(si.index, output().index)
    for s in pulse().sink_list():
      if s.name != output().name:
        pulse().sink_suspend(s.index, 1)

# An output is an abstraction over a sink.
class Output(object):
  def __init__(self, sink, pulse):
    self.sink = sink
    self.pulse = pulse

  @property
  def volume(self):
    return int(round(self.sink.volume.value_flat * 100))

  @volume.setter
  def volume(self, v):
    vp = v
    if vp < 0:
      vp = 0
    elif vp > 100:
      vp = 100
    self.pulse.volume_set_all_chans(self.sink,float(vp)/100.0)

  @property
  def muted(self):
    return bool(self.sink.mute)

  @muted.setter
  def muted(self, m):
    self.pulse.sink_mute(self.sink.index,int(bool(m)))

  def __str__(self):
    def_name = self.pulse.server_info().default_sink_name
    star = '*' if self.sink.name == def_name else ''
    return ' '.join([int(self.sink.index), ".", self.sink.name, self.volume])

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.sink.index is other.sink.instance
    return NotImplemented

  def __ne__(self, other):
    if isinstance(other, self.__class__):
      return self.sink.index is not other.sink.instance
    return NotImplemented

