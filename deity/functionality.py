from .hardware.audio import Audio, Input, Output, Stream
from time import sleep

def Functionality(key):
  return {
    "audio": AudioFunctionality,
    "brightness": BrightnessFunctionality,
    "screenshot": ScreenshotFunctionality,
    "i3bar": i3barFunctionality
  }[key]()

class AudioFunctionality(object):
  def go(self,
         list_outputs = False, toggle_mute = False,
         output = None, input = None,
         adjust_volume = None, sanitize = False):
    with Audio("desktop.py") as a:
      if list_outputs:
        for o in a.outputs:
          print(str(o))

      if toggle_mute:
        a.output.muted = not a.output.muted

      if output != None:
        a.output = output

      if adjust_volume != None:
        a.output.volume = a.output.volume + int(adjust_volume)

      if args.sanitize:
        a.collect_streams()
        for o in a.outputs():
          if o != a.output:
            o.suspend()
        for i in a.inputs():
          if i != a.input:
            i.suspend()

class BrightnessFunctionality(object):
  def go(self, **args):
    if args.auto:
      while True:
        autoadjust_brightness(args.lower_threshold, args.upper_threshold, args.backlight, args.backlight_class)
        time.sleep(5)
    elif args.set is not None:
      set_brightness(args.backlight,int(args.set), args.backlight_class)
    elif args.adjust is not None:
      adjust_brightness(args.backlight, int(args.adjust), args.backlight_class)
    else:
      b = get_brightness(args.backlight, args.backlight_class)
      if b is not None:
        sys.stdout.write(str(b) + '%\n')
      else:
        sys.stdout.write("failed to read brightness: cannot read /sys/class/" + args.backlight_class + "/" + args.backlight + "/*brightness")

class ScreenshotFunctionality(object):
  def go(self, destination = "~/Pictures/screenshots"):
    os.system("mkdir -p " + destination)
    os.system("swaygrab " + destination.rstrip('/') + time.strftime("/%-m-%-d-%y_%-H:%M:%S.png"))

class i3barFunctionality(object):
  def __init__(self):
    super().__init__()

  def go(self, refresh_interval = 3, **kwargs):
    self.audio = Audio("deity i3bar")
    sys.stdout.write("{\"version\":1}\n[\n")
    self.statusline(**kwargs)
    sleep(refresh_interval) 
    while True:
      sys.stdout.write(',')
      self.statusline(**kwargs) 
      sleep(refresh_interval)
    self.audio.close()

  def statusline(self, **args):
    items = [
      brightness(args.backlight, args.color, args.color_dire),
      volume(args.color, args.color_degrading),
      battery(args.power_supply, args.color, args.color_improving, args.color_dire),
      network(args.wifi_iface, "WiFi", args.color, args.color_dire),
      network(args.vpn_iface, "VPN", args.color, args.color_dire),
      date(args.color, args.date_format)
    ]
    sys.stdout.write('[' + ','.join(items) + ']\n')
    sys.stdout.flush()

def date(color, fmt):
  return statusd(color, time.strftime(fmt))

def network(iface, text, color_on, color_off):
  return statusd(color_on if is_conn_to(iface) else color_off, text)

def battery(device, normal, charging, dire):
  uevent = read_sys("power_supply", device, "uevent")
  if uevent is None:
    return statusd(dire, "")
  else:
    info = dict([l.split('=') for l in uevent.split('\n')])
    ischarging = info["POWER_SUPPLY_STATUS"] == "Charging"
    energy_now = float(info["POWER_SUPPLY_ENERGY_NOW"])
    energy_full = float(info["POWER_SUPPLY_ENERGY_FULL"])
    bat_perc = int(floor((energy_now / energy_full) * 100))
    
    if ischarging:
      bat_color = charging
    elif bat_perc <= 20:
      bat_color = dire
    else:
      bat_color = normal

    return statusd(bat_color, " " + str(bat_perc) + "%")

def volume(color, mutecolor):
  global audio
  if audio is None:
    audio = Audio("desktop.py i3bar")

  return statusd(mutecolor if audio.output.muted else color,
                 " " + str(audio.output.volume) + "%")

def brightness(backlight, normal, degraded):
  b = get_brightness(backlight, "backlight")
  return statusd(normal if b is not None else degraded,
                 "☀ " + str(b) + "%" if b is not None else "☀")

def statusd(color, text):
  return ''.join([
    "{\"color\":\"",
    str(color),
    "\",\"full_text\":\"",
    str(text),
    "\"}"
  ])

# DRY

def read_file(path):
  try:
    f = open(path, 'r')
    v = f.read()
    f.close()
    return v
  except:
    return None

def read_sys(klass, iface, *props):
  bp = '/'.join(["", "sys", "class", str(klass), str(iface), ""])
  for prop in props:
    v = read_file(bp + prop)
    if v is not None:
      return v.rstrip('\n')
  return None

def write_sys(klass, iface, prop, value):
  pth = '/'.join(["", "sys", "class", str(klass), str(iface), str(prop)])
  try:
    fp = open(pth, 'w')
    fp.write(str(value) + '\n')
    fp.flush()
    fp.close()
    return True
  except:
    return False

# gets a brightness percent (integer)
def get_brightness(iface,klass):
  current = read_sys(klass, iface, "actual_brightness", "brightness")
  if current is None:
    return None
  maximum = read_sys(klass, iface, "max_brightness")
  if maximum is None:
    return None
  return int(round((float(current) / float(maximum)) * 100))

# sets the brightness to a percent (integer)
def set_brightness(iface, percent, klass):
  maximum = read_sys(klass, iface, "max_brightness")
  if maximum is None:
    return False
  percent_p = min(max(percent, 0), 100)
  new_brightness = round((percent_p / 100) * float(maximum))
  return write_sys(klass, iface, "brightness", new_brightness)

def adjust_brightness(iface, delta_perc, klass):
  brightness = get_brightness(iface, klass)
  if brightness is not None:
    return set_brightness(iface, brightness + delta_perc, klass)
  else:
    return False

#
## Wifi
#

def is_conn_to(iface):
  return iface in read_file("/proc/net/if_inet6")
