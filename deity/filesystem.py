import sys

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
