from ..statusbar import StatusItem, Color

class Network(StatusItem):
  def __init__(self, text = "Network", interface = None, **kwargs):
    super().__init__(**kwargs)
    self.text = text
    if interface is None:
      raise ValueError("Network(): expected interface parameter.")
    self.interface = interface

  def refresh(self):
    self.connected = False
    try:
      with open("/proc/net/if_inet6", 'r') as f:
        self.connected = self.interface in f.read() # TODO: use faster reading technique
    except:
      self.connected = False

  def full_text(self):
    return self.text

  def color(self):
    if self.connected:
      return Color.POSITIVE
    else:
      return Color.NEGATIVE
