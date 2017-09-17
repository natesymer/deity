from pulsectl import Pulse

class Audio(object):
  """
  An abstraction over PulseAudio.
  """
  pulses = {}

  # WITH syntax implementation

  def __init__(self, name):
    self.name = name

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

  def close(self):
    """
    Turns off the connection to PulseAudio.
    """
    if self.pulse is not None:
      self.pulse.close()
      self.pulse = None

  # INTERNAL
  def _create_pulse(self):
    p = Pulse(self.name)
    self.__class__.pulses[self.name] = p
    return p

  @property
  def pulse(self):
    """
    The underlying pulse object.
    """
    return self.__class__.pulses.get(self.name, _create_pulse())

  @pulse.setter
  def pulse(self, p):
    if not p:
      del self.__class__.pulses[self.name]
    else:
      self.__class__.pulses[self.name] = p

  @property
  def outputs(self):
    """
    The outputs PulseAudio can play to.
    """
    return list(self.pulse.sink_list().map(lambda s: Output(s, self.pulse)))

  @property
  def output(self):
    """
    Current output. This functionality is mediated by
    PulseAudio's notion of a 'default sink'.
    """
    default_name = self.pulse.server_info().default_sink_name
    for s in self.outputs():
      if s.name == default_name:
        return s
    return None

  @output.setter
  def output(self, o):
    self.pulse.sink_default_set(o.name)

  @property
  def inputs(self):
    """
    The inputs PulseAudio can receive input from.
    """
    return list(map(lambda s: Input(s, self.pulse), self.pulse.source_list()))

  @property
  def input(self):
    """
    Current input. Otherwise identical to self.output.
    """
    default_name = self.pulse.server_info().default_source_name
    for s in self.inputs():
      if s.name == default_name:
        return s
    return None

  @property.setter
  def input(self, i):
    self.pulse.source_default_set(i.name)

  def input_streams(self):
    return list(map(lambda x: Stream(x, self.pulse, "input"), self.pulse.source_output_list()))

  def output_streams(self):
    return list(map(lambda x: Stream(x, self.pulse, "output"), self.pulse.sink_input_list()))

  def collect_streams(self):
    """
    Gather all audio streams into the default sinks/sources
    """
    o = self.output
    i = self.input
    for s in self.input_streams():
      s.move_to(i)
    
    for s in self.output_streams():
      s.move_to(o)

class Primitive(object):
  def __init__(self, prim, pulse):
    super().__init__()
    self.prim = prim
    self.pulse = pulse

  def __str__(self):
    return self.name

  @property
  def name(self):
    return str(self.prim.name)

  @property
  def index(self):
    return int(self.prim.index)

  @property
  def muted(self):
    return bool(self.prim.mute)

  @property.setter
  def muted(self, v):
    self._mute_func()(self.prim.index, int(bool(m)))

  @property
  def volume(self):
    return int(round(self.prim.volume.value_flat * 100))

  @volume.setter
  def volume(self, v):
    perc = float(min(100, max(0, v))) / 100.0
    self.pulse.volume_set_all_chans(self.prim, perc)

  def enable(self):
    self._suspend_func()(self.index, 0)

  def suspend(self):
    self._suspend_func()(self.index, 1)

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.name is other.name
    return NotImplemented

  def __ne__(self, other):
    v = self.__eq__(other)
    if v == NotImplemented:
      return v
    else:
      return not v

  def _suspend_func(self):
    return NotImplemented

  def _mute_func(self):
    return NotImplemented

class Input(Primitive):
  """
  Represents a PulseAudio source.
  """
  def _mute_func(self):
    return self.pulse.source_mute

  def _suspend_func(self):
    return self.pulse.source_suspend

class Output(Primitive):
  """
  An abstraction over a PulseAudio sink.
  """
  def _mute_func(self):
    return self.pulse.sink_mute

  def _suspend_func(self):
    return self.pulse.sink_suspend

class Stream(Primitive):
  """
  Represents either a sink input or a source output.
  This is designated by setting the type of this object
  to either `output' or `input', respectively. Those are
  named from a user's point of view (i.e. sinks output sound)
  """
  def __init__(self, prim, pulse, typ):
    super().__init__(prim, pulse)
    self.type = typ

  def _mute_func(self):
    if self.type == "input":
      return self.pulse.source_output_mute
    elsif self.type == "output":
      return self.pulse.sink_input_list
    return NotImplemented

  def _suspend_func(self):
    if self.type == "input":
      return self.pulse.source_output_suspend
    elsif self.type == "output":
      return self.pulse.sink_input_suspend
    return NotImplemented

  def move_to(self, target):
    if self.type == "input":
      self.pulse.sink_input_move(self.index, target.index)
    elsif self.type == "output":
      self.pulse.source_output_move(self.index, target.index)

