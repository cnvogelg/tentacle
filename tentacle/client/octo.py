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
            try:
                # setup client
                logging.debug("create gen, client")
                gen = self.gen_factory()
                client = self.client_factory()
                self.client.set_client(client)
                # check state
                if client:
                    state = self.client.state()
                    logging.info("initial state: %s", state)
                    if state in ('Offline', 'Closed'):
                        logging.info("auto connect")
                        self.client.connect()
                # initially read files
                if client:
                    logging.debug("get files()")
                    files = client.files()
                    self.client.file_set.emit(files)
                # setup event reader
                logging.debug("enter gen.read_loop()")
                read_loop = gen.read_loop()
                for msg in read_loop:
                    logging.debug("msg: %r", msg)
                    if not self.stay:
                        break
                    for t in self.msg_types:
                        if t in msg:
                            logging.debug("post signal: %s", t)
                            signal = getattr(self.client, t)
                            signal.emit(msg[t])
                            logging.debug("done")
                # end of sim. never reached on 'real' OctoPrint link
                self.client.error.emit("EOF reached")
                self.client.set_client(None)
                break
            except IOError as e:
                logging.error("emitter exeception: %s", e)
                self.client.error.emit(str(e))
                self.client.set_client(None)
                # retry
                time.sleep(self.retry_delay)
                logging.info("retry event emitter")
        logging.debug("stop event emitter")


class OctoClient(QObject):
    """The OctoClient Qt wrapper for the OctoPrint Rest API."""

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
            self.gen_factory = lambda: octorest.XHRStreamingGenerator(url)
            if api_key:
                self.client_factory = lambda: octorest.OctoRest(
                    url=url, apikey=api_key)
            else:
                self.client_factory = lambda: None
        self._thread = None
        self.client = None

    def start(self):
        """Start worker thread."""
        self._thread = OctoEventEmitter(
            self, self.gen_factory, self.client_factory)
        self._thread.start()

    def stop(self):
        """Cooperatively stop worker thread."""
        self._thread.stop()
        self._thread.wait()
        self._thread = None

    def set_client(self, client):
        """Report the valid client instance of the worker thread."""
        self.client = client

    def files_info(self, location, file_name):
        """Get info on file."""
        if self.client:
            try:
                logging.info("files_info(%s, %s)", location, file_name)
                res = self.files_info(location, file_name)
                logging.info("result: %r", res)
                return res
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim get files info")
            return {}

    def connect(self):
        """Connect to printer."""
        if self.client:
            try:
                self.client.connect()
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim connect")

    def disconnect(self):
        """Disconnect from printer."""
        if self.client:
            try:
                self.client.disconnect()
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim disconnect")

    def state(self):
        """Return printer state."""
        if self.client:
            try:
                return self.client.state()
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim state")
            return "Operational"

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

    def select(self, name, start_print=False):
        """Select a file for printing."""
        if self.client:
            try:
                self.client.select(name, print=start_print)
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim select: %s print=%s", name, print)

    def print(self):
        """Print currently selected file."""
        if self.client:
            try:
                self.client.print()
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim print")

    def delete(self, name):
        """Delete given file."""
        if self.client:
            try:
                self.client.delete(name)
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim delete: %s", name)

    def file_info(self, name):
        """Return info on given file."""
        if self.client:
            try:
                return self.client.files_info("local", name)
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim files info: %s", name)

    def feedrate(self, rate):
        """Set the feedrate."""
        if self.client:
            try:
                return self.client.feedrate(rate)
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim feedrate: %r", rate)

    def send_gcode(self, commands):
        """Send GCode Commands."""
        if self.client:
            try:
                return self.client.gcode(commands)
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim commands: %r", commands)

    def tool_target(self, tool_no, temp):
        """Set target temperature of tool."""
        if self.client:
            try:
                self.client.tool_target({'tool%d' % tool_no: temp})
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim tool_target: %d: %r", tool_no, temp)

    def bed_target(self, temp):
        """Set target temperature of bed."""
        if self.client:
            try:
                self.client.bed_target(temp)
            except RuntimeError as e:
                self.error.emit(str(e))
        else:
            logging.info("sim bed_target: %r", temp)


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
