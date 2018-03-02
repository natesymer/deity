from ..statusbar import StatusItem, Color
import re

class CPU(StatusItem):
  WHITESPACE_RE = re.compile(r'\W+')

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.usage = -1;

  def refresh(self, periodic):
    with open('/proc/stat') as ps:
      first_line = ps.readline().rstrip("\n")

    _, user, nice, system, idle, iowait, irq, softirq, *xs = re.split(self.WHITESPACE_RE, first_line)
    
    usage = 100 - round((float(idle) * 100) / (int(user) + int(nice) + int(system) + int(idle) + int(iowait) + int(irq) + int(softirq)))
    has_changed = usage != self.usage
    self.usage = usage
    return has_changed

  def full_text(self):
    return "\uf2db " + str(self.usage) + "%"

  def color(self):
    if self.usage > 60:
      return Color.NEGATIVE
    return Color.POSITIVE
