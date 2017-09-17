#!/usr/bin/env python3

from pyudev import Context, Monitor, MonitorObserver

c = Context()
m = Monitor.from_netlink(c)
m.filter_by(subsystem='backlight')

def prt(device):
  print(device)

o = MonitorObserver(m, callback=prt, name="monitor-observer")
o.daemon = False
print(o.daemon)
o.start()
