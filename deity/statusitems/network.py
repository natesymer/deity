from ..statusbar import StatusItem, Color

class Network(StatusItem):
  def __init__(self, text = "Network", interface = None):
    super().__init__()
    self.text = text
    if interface is None:
      raise ValueError("Network(): expected interface parameter.")
    self.interface = interface

  def is_connected(self):
    conn = False
    with open("/proc/net/if_inet6", 'r') as f:
      conn = self.interface in f.read() # TODO: use faster reading technique
    return conn

  def full_text(self):
    return self.text

  def color(self):
    if self.is_connected():
      return Color.POSITIVE
    else:
      return Color.NEGATIVE
