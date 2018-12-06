import logging
import time
import json
import gzip

import octorest

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread


class OctoSimGenerator:
  def __init__(self, file_name, scale=1.0):
    self.file_name = file_name
    self.scale = scale

  def read_loop(self):
    """a generator yieling the messages recorded in a file"""
    last_time = None
    if self.file_name.endswith("gz"):
      op = gzip.open
    else:
      op = open
    with op(self.file_name, mode="rt", encoding="utf8") as fh:
      for line in fh:
        pos = line.find(' ')
        ts_str = line[:pos]
        obj_str = line[pos+1:]
        ts = float(ts_str)
        obj = json.loads(obj_str)
        # time handling
        if last_time:
          delta = (ts - last_time) * self.scale
          if delta > 0:
            time.sleep(delta)
        last_time = ts
        # yield data
        yield obj


class OctoEventEmitter(QThread):

  msg_types = ('connected', 'current', 'history', 'event',
               'slicingProgress', 'plugin')

  def __init__(self, client, gen, retry_delay=5):
    super().__init__()
    self.client = client
    self.gen = gen
    self.retry_delay = retry_delay
    self.stay = True

  @pyqtSlot()
  def stop(self):
    self.stay = False

  def run(self):
    logging.debug("start event emitter")
    while self.stay:
      try:
        read_loop = self.gen.read_loop()
        for msg in read_loop:
          if not self.stay:
            break
          for t in self.msg_types:
            if t in msg:
              signal = getattr(self.client, t)
              signal.emit(msg[t])
        self.client.error.emit("EOF reached")
        break
      except IOError as e:
        logging.error("emitter exeception: %s", e)
        self.client.error.emit(str(e))
        # retry
        time.sleep(self.retry_delay)
        logging.info("retry event emitter")
    logging.debug("stop event emitter")


class OctoClient(QObject):

  stopEmitter = pyqtSignal()
  error = pyqtSignal(str)
  # octo events
  connected = pyqtSignal(dict)
  current = pyqtSignal(dict)
  history = pyqtSignal(dict)
  event = pyqtSignal(dict)
  slicingProgress = pyqtSignal(dict)
  plugin = pyqtSignal(dict)

  def __init__(self, url=None, api_key=None, sim_file=None, sim_scale=1.0):
    super().__init__()
    if sim_file:
      self.gen = OctoSimGenerator(sim_file, sim_scale)
      self.client = None
    else:
      self.gen = octorest.XHRStreamingGenerator(url)
      if api_key:
        self.client = octorest.OctoRest(url=url, apikey=api_key)
      else:
        self.client = None
    self._thread = None

  def start(self):
    self._thread = OctoEventEmitter(self, self.gen)
    self.stopEmitter.connect(self._thread.stop)
    self._thread.start()

  def stop(self):
    self.stopEmitter.emit()
    self._thread.wait()
    self._thread = None

  def job_cancel(self):
    if self.client:
      try:
        self.client.cancel()
      except RuntimeError as e:
        self.error.emit(str(e))
    else:
      logging.info("sim job cancel")

  def job_pause(self):
    if self.client:
      try:
        self.client.pause()
      except RuntimeError as e:
        self.error.emit(str(e))
    else:
      logging.info("sim job pause")

if __name__ == '__main__':
  from PyQt5.QtCore import QCoreApplication
  import sys
  import pprint

  app = QCoreApplication(sys.argv)
  if len(sys.argv) > 1:
    sim_file = sys.argv[1]
    print("sim_file", sim_file)
    if len(sys.argv) > 2:
      sim_scale = float(sys.argv[2])
      print("sim_scale", sim_scale)
    else:
      sim_scale = 1.0
    oc = OctoClient(sim_file=sim_file, sim_scale=sim_scale)
  else:
    oc = OctoClient(url="http://octopi.local")

  num = 0
  @pyqtSlot(dict)
  def current(d):
    global num
    pprint.pprint(d)
    num += 1
    if num == 5:
      app.quit()

  oc.current.connect(current)
  oc.start()
  sys.exit(app.exec_())
