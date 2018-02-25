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
      del self.__class__.pulses[self.name]

  # INTERNAL

  def _create_pulse(self):
    """
    Create a PulseAudio client with self.name.
    Insert it into the instance cache
    """
    p = Pulse(self.name)
    self.__class__.pulses[self.name] = p
    return p

  @property
  def pulse(self):
    """
    The underlying pulse object.
    """
    return self.__class__.pulses.get(self.name, None) or self._create_pulse()

  @property
  def outputs(self):
    """
    The outputs PulseAudio can play to.
    """
    return list(map(lambda s: Output(s, self.pulse), self.pulse.sink_list()))

  @property
  def output(self):
    """
    Current output. This functionality is mediated by
    PulseAudio's notion of a 'default sink'.
    """
    try:
      return Output(self.pulse.get_sink_by_name("@DEFAULT_SINK@"), self.pulse)
    except:
      return None

  @output.setter
  def output(self, o):
    """
    Set the current output. `o' is an instance with __str__() (like an `Output').
    """
    self.pulse.sink_default_set(str(o))

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
    try:
      return Input(self.pulse.get_source_by_name("@DEFAULT_SOURCE@"), self.pulse)
    except:
      return None

  @input.setter
  def input(self, i):
    self.pulse.source_default_set(i)

  def input_streams(self):
    return list(map(lambda x: InputStream(x, self.pulse), self.pulse.source_output_list()))

  def output_streams(self):
    return list(map(lambda x: OutputStream(x, self.pulse), self.pulse.sink_input_list()))

  def collect_streams(self):
    """
    Gather all audio streams into the default sinks/sources
    """
    o = self.output
    i = self.input

    if i is not None:
      for s in self.input_streams():
        s.move_to(i)
    
    if o is not None:
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

  @muted.setter
  def muted(self, v):
    self._mute_func()(self.prim.index, int(bool(v)))

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

class GenericStream(Primitive):
  def move_to(self, target):
    raise NotImplemented

class OutputStream(GenericStream):
  def _mute_func(self):
    return self.pulse.sink_input_mute

  def _suspend_func(self):
    return self.pulse.sink_input_suspend

  def move_to(self, target):
    self.pulse.sink_input_move(self.index, target.index)

class InputStream(GenericStream):
  def _mute_func(self):
    return self.pulse.source_output_mute

  def _suspend_func(self):
    return self.pulse.source_output_suspend

  def move_to(self, target):
    self.pulse.source_output_move(self.index, target.index)

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
    elif self.type == "output":
      return self.pulse.sink_input_mute
    return NotImplemented

  def _suspend_func(self):
    if self.type == "input":
      return self.pulse.source_output_suspend
    elif self.type == "output":
      return self.pulse.sink_input_suspend
    return NotImplemented

  def move_to(self, target):
    if self.type == "output":
      self.pulse.sink_input_move(self.index, target.index)
    elif self.type == "input":
      self.pulse.source_output_move(self.index, target.index)

