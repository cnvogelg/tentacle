"""OctoRest wrapper in PyQt."""

import logging
import time
import json
import gzip

import octorest

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread


class OctoSimGenerator:
    """A simulation of the OctoRest event API using record files."""

    def __init__(self, file_name, scale=1.0):
        """Create new simulator."""
        self.file_name = file_name
        self.scale = scale

    def read_loop(self):
        """Yield the messages recorded in a file."""
        last_time = None
        if self.file_name.endswith("gz"):
            op = gzip.open
        else:
            op = open
        with op(self.file_name, mode="rt", encoding="utf8") as fh:
            for line in fh:
                pos = line.find(" ")
                ts_str = line[:pos]
                obj_str = line[pos + 1:]
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
    """Helper Thread that handles OctoPrint Rest API calls."""

    msg_types = (
        "connected",
        "current",
        "history",
        "event",
        "slicingProgress",
        "plugin",
    )

    def __init__(self, client, gen_factory, client_factory, retry_delay=5):
        """Create a helper thread."""
        super().__init__()
        self.client = client
        self.gen_factory = gen_factory
        self.client_factory = client_factory
        self.retry_delay = retry_delay
        self.stay = True

    @pyqtSlot()
    def stop(self):
        """Stop the helper thread loop."""
        self.stay = False

    def run(self):
        """Run main loop of helper thread."""
        logging.debug("start event emitter")
        while self.stay:
            # setup client
            logging.debug("create gen, client")
            gen = self.gen_factory()
            client = self.client_factory()
            self.client.setClient.emit(client)
            # initially read files
            if client:
                logging.debug("get files()")
                files = client.files()
                self.client.file_set.emit(files)
            # setup event reader
            logging.debug("enter gen.read_loop()")
            try:
                read_loop = gen.read_loop()
                for msg in read_loop:
                    if not self.stay:
                        break
                    for t in self.msg_types:
                        if t in msg:
                            signal = getattr(self.client, t)
                            signal.emit(msg[t])
                # end of sim. never reached on 'real' OctoPrint link
                self.client.error.emit("EOF reached")
                self.client.setClient.emit(None)
                break
            except IOError as e:
                logging.error("emitter exeception: %s", e)
                self.client.error.emit(str(e))
                self.client.setClient.emit(None)
                # retry
                time.sleep(self.retry_delay)
                logging.info("retry event emitter")
        logging.debug("stop event emitter")


class OctoClient(QObject):
    """The OctoClient Qt wrapper for the OctoPrint Rest API."""

    # internal signals
    stopEmitter = pyqtSignal()
    setClient = pyqtSignal(object)

    # octo events
    error = pyqtSignal(str)
    connected = pyqtSignal(dict)
    current = pyqtSignal(dict)
    history = pyqtSignal(dict)
    event = pyqtSignal(dict)
    slicingProgress = pyqtSignal(dict)
    plugin = pyqtSignal(dict)
    # octo files
    file_set = pyqtSignal(dict)

    def __init__(self, url=None, api_key=None, sim_file=None, sim_scale=1.0):
        """Create a new OctoClient."""
        super().__init__()
        if sim_file:
            self.gen_factory = lambda: OctoSimGenerator(sim_file, sim_scale)
            self.client_factory = lambda: None
        else:
            self.gen_factory = octorest.XHRStreamingGenerator(url)
            if api_key:
                self.client_factory = lambda: octorest.OctoRest(
                    url=url, apikey=api_key)
            else:
                self.client_factory = lambda: None
        self._thread = None

    def start(self):
        """Start worker thread."""
        self._thread = OctoEventEmitter(
            self, self.gen_factory, self.client_factory)
        self.stopEmitter.connect(self._thread.stop)
        self._thread.start()

    def stop(self):
        """Cooperatively stop worker thread."""
        self.stopEmitter.emit()
        self._thread.wait()
        self._thread = None

    def job_cancel(self):
        """Cancel current job."""
        if self.client:
            try:
                self.client.cancel()
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim job cancel")

    def job_pause(self):
        """Toggle pause/resume job."""
        if self.client:
            try:
                self.client.pause()
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim job pause")

    def home(self, x, y, z):
        """Home printer on selected axes."""
        axes = []
        if x:
            axes.append("x")
        if y:
            axes.append("y")
        if z:
            axes.append("z")
        if self.client:
            try:
                self.client.home(axes)
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim home: axes=%r", axes)

    def jog(self, x, y, z):
        """Jog printer (relative) along axes."""
        if x == 0.0:
            x = None
        if y == 0.0:
            y = None
        if z == 0.0:
            z = None
        if self.client:
            try:
                self.client.jog(x, y, z)
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim jog: x=%s, y=%s, z=%s", x, y, z)


if __name__ == "__main__":
    from PyQt5.QtCore import QCoreApplication
    import sys
    import pprint

    app = QCoreApplication(sys.argv)
    if len(sys.argv) > 1:
        _sim_file = sys.argv[1]
        print("sim_file", _sim_file)
        if len(sys.argv) > 2:
            _sim_scale = float(sys.argv[2])
            print("sim_scale", _sim_scale)
        else:
            _sim_scale = 1.0
        oc = OctoClient(sim_file=_sim_file, sim_scale=_sim_scale)
    else:
        oc = OctoClient(url="http://octopi.local")

    @pyqtSlot(dict)
    def _current(d):
        for _ in range(5):
            pprint.pprint(d)
            yield
        app.quit()

    oc.current.connect(_current)
    oc.start()
    sys.exit(app.exec_())
