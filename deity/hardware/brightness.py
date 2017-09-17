from ..filesystem import write_sys, read_sys

# gets a brightness percent (integer)
def get_brightness(iface, klass):
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

