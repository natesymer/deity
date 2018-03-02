from ..statusbar import StatusItem, Color
import re

class Memory(StatusItem):
  MEMLINE_RE = re.compile(r'[^0-9]*([0-9]*)\W+(k|m|g)')

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.avail_bytes = -1;
    self.mem_size = -1;

  def to_bytes(self, str):
    num, unit = re.search(self.MEMLINE_RE, str).group(1, 2)
    if unit == "k":
      divisor = 1024
    elif unit == 'm':
      divisor = 1024 * 1024
    elif unit == 'g':
      divisor = 1024 * 1024 * 1024
    else:
      divisor = 1
    return round(int(num) * divisor)

  def refresh(self, periodic):
    with open('/proc/meminfo') as mi:
      total_line = mi.readline()
      next(mi)
      avail_line = mi.readline()

    mem_size = self.to_bytes(total_line)
    avail_bytes = self.to_bytes(avail_line)

    has_changed = mem_size != self.mem_size or avail_bytes != self.avail_bytes
    self.mem_size = mem_size
    self.avail_bytes = avail_bytes
    return has_changed

  def full_text(self):
    return "\uf2db " + str(round(((self.mem_size - self.avail_bytes) / (1024 * 1024)))) + "MB"

  def color(self):
    if self.avail_bytes < (self.mem_size / 2):
      return Color.NEGATIVE
    return Color.POSITIVE
