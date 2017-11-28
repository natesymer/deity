import sys

def read_file(path):
  try:
    with open(path, 'r') as f:
      return f.read()
  except:
    return None

def read_sys(klass, iface, *props):
  bp = "/sys/class/" + str(klass) + "/" + str(iface) + "/"
  iterable = map(read_file, map(lambda prop: bp + prop, props))
  v = next((x for x in iterable if x is not None), None)
  if v is not None:
    return v.rstrip('\n')
  return None
#  for prop in props:
#    v = read_file(bp + prop)
#    if v is not None:
#      return v.rstrip('\n')
#  return None

def write_sys(klass, iface, prop, value):
  pth = '/'.join(["", "sys", "class", str(klass), str(iface), str(prop)])
  try:
    with open(pth, 'w') as fp:
      fp.write(str(value) + '\n')
    return True
  except:
    return False
