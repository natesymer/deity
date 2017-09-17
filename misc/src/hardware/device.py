# sysfs.py
# functions to read from the Linux sysfs (/sys/)

class Device(object):
  def __init__(self, path, unpack=lambda x: x, pack=lambda x: x):
    self.unpack = unpack
    self.pack = pack
    self.mapping = {}
    self.path = path

  @property
  def path(self):
    return self.path

  def _read(self, props):
    for p in props:
      try:
        f = open(path, 'r')
        v = f.read()
        f.close()
        if v is not None and len(v) > 0:
          return v
      except:
        pass
    return None

  def _write(self, prop, v):
    try:
      fp = open(self.path + prop, 'w')
      fp.write(str(v) + '\n')
      fp.flush()
      fp.close()
      return True
    except:
      return False

  # MAPPING

  def map(self, name, *props):
    self.mapping[name] = props

  def __getattr__(self, name):
    m = self.mapping.get(name, None)
    if m is not None and len(m) is not 0:
      return self.unpack(self._read(m))
    else:
      super.__getattr__(name)

  def __setattr__(self, name, v):
    m = self.mapping.get(name, None)
    if m is not None and len(m) > 0:
      self._write(name, self.pack(v))
    else:
      super().__setattr__(name, v)

class SysDevice(Device):
  def __init__(self, klass, iface, f=lambda x: x):
    super().init(None, f)

  @property
  def path(self):
    return '/'.join(["", "sys", "class", self.klass, self.iface, ""])

  @property
  def klass(self):
    return klass

  @klass.setter
  def klass(self, v):
    self.klass = v

  @property
  def iface(self):
    return self.iface

  @iface.setter
  def iface(self, v):
    self.iface = v:

  def _read(self, props):
    s = super()._read(props)
    if s is None:
      return None
    return s.rstrip('\n')

  def _write(self, prop, v):
    super()._write(prop, v + '\n')

