import logging
import octorest
import pprint
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread


class OctoEventEmitter(QThread):

  msg_types = ('connected', 'current', 'history', 'event',
               'slicingProgress', 'plugin')

  def __init__(self, url, client):
    super(QThread, self).__init__()
    self.url = url
    self.client = client
    self.stay = True
    self.gen = None

  @pyqtSlot()
  def stop(self):
    self.stay = False

  def run(self):
    logging.debug("start event emitter")
    self.gen = octorest.XHRStreamingGenerator(self.url)
    read_loop = self.gen.read_loop()
    while self.stay:
      msg = next(read_loop)
      if not self.stay:
        break
      for t in self.msg_types:
        if t in msg:
          signal = getattr(self.client, t)
          signal.emit(msg[t])
    logging.debug("stop event emitter")


class OctoClient(QObject):

  stopEmitter = pyqtSignal()
  connected = pyqtSignal(dict)
  current = pyqtSignal(dict)
  history = pyqtSignal(dict)
  event = pyqtSignal(dict)
  slicingProgress = pyqtSignal(dict)
  plugin = pyqtSignal(dict)

  def __init__(self, url, api_key):
    super(QObject, self).__init__()
    self.url = url
    self.client = octorest.OctoRest(url=url, apikey=api_key)
    self.version = self.client.version
    self._thread = None

  def start(self):
    self._thread = OctoEventEmitter(self.url, self)
    self.stopEmitter.connect(self._thread.stop)
    self._thread.start()

  def stop(self):
    self.stopEmitter.emit()
    self._thread.wait()
    self._thread = None

  def fetch_connection(self):
    return self.client.connection_info()

  def fetch_printer(self):
    return self.client.printer()

  def fetch_files(self):
    return self.client.files()

  def fetch_job(self):
    return self.client.job_info()

  def get_version(self):
    return self.version

  def dump(self):
    p = pprint.pprint
    print("version", self.get_version())
    print("--- connection ---")
    p(self.fetch_connection())
    print("--- printer ---")
    p(self.fetch_printer())
    print("--- files ---")
    p(self.fetch_files())
    print("--- job ---")
    p(self.fetch_job())


if __name__ == '__main__':
  api_key = "10173304C8594E55AF944BEBBE67AB3D"
  url = "http://octopi.local"
  c = OctoClient(url, api_key)
  c.dump()
