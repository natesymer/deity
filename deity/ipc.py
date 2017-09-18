import os
import sys
import socket
from socket import socket, AF_UNIX, SOCK_STREAM
import json
import deity.functionality

class IPCClient(object):
  def __init__(self, sockfile):
    super().__init__()
    self.socket = socket(AF_UNIX, SOCK_STREAM)
    self.sockfile = sockfile

  def connect(self):
    self.socket.connect(self.sockfile)

  def send(self, cmd):
    self.socket.send(json.dumps(cmd).encode('utf-8'))

  def close(self):
    self.socket.close()

class IPCServer(object):
  def __init__(self, sockfile):
    super().__init__()
    self.socket = socket(AF_UNIX, SOCK_STREAM)
    self.sockfile = sockfile

  def start(self):
    if os.path.exists(self.sockfile):
      os.remove(self.sockfile)

    self.socket.bind(sockfile)
    self.socket.bind(5)

    while True:
      conn, addr = self.socket.accept()

      data = b''
      while True:
        bs = conn.recv(4096)
        if not bs:
          break
        else:
          data += bs
  
      cmd = json.loads(str(data, encoding='utf-8'))
      if isinstance(cmd, list):
        for c in cmd:
          self.handle_command(c)
      else:
        self.handle_command(cmd)

    os.remove(self.sockfile)

  def handle_command(self, cmd):
    kwargs = cmd["kwargs"]
    Functionality(cmd["name"]).go(**kwargs)

