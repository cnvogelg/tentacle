"""Camera Client for MJPEG streaming from mjpeg-streamer server."""

import logging
import time
import http.client
import urllib.parse

from PyQt5.QtCore import QObject, pyqtSignal, QThread


class CamWorker(QThread):
    """Worker Thread of camera capture."""

    def __init__(self, client):
        """Init worker thread."""
        super().__init__()
        self._client = client
        self._stay = True

    def stop(self):
        """Try to stop thread."""
        self._stay = False

    def run(self):
        """Enter main run loop of thread."""
        org_url = self._client.get_url()
        url = urllib.parse.urlparse(org_url)
        retry_delay = self._client.get_retry_delay()
        # combine req URL
        req = url.path
        if url.query:
            req += "?" + url.query
        while self._stay:
            logging.info("cam: request for %s @ %s", req, url.netloc)
            con = None
            try:
                con = http.client.HTTPConnection(url.netloc)
                con.request('GET', req)
                resp = con.getresponse()
                if resp.status != 200:
                    logging.error("cam: invalid status: %d", resp.status)
                    self._client.raisedError.emit(resp.reason)
                else:
                    # data loop
                    self._data_loop(resp)
                    logging.debug("cam: end request")
                    return
            except IOError as e:
                logging.error("cam: error: %s", str(e))
                self._client.raisedError.emit(e)
            finally:
                if con:
                    con.close()
            # retry
            logging.debug("cam: retry delay: %s", retry_delay)
            time.sleep(retry_delay)

    def _data_loop(self, reader):
        self._reset_frame_time()
        while self._stay:
            # read header
            size = self._parse_header(reader)
            # data
            jpeg_data = reader.read(size)
            # read line after data
            reader.readline()
            self._client.jpegData.emit(jpeg_data)
            self._update_frame_time()

    def _parse_header(self, reader):
        # parse header
        def get():
            return reader.readline().strip().decode("utf-8")
        # now the header entries. size needs to be found.
        size = None
        while True:
            line = get()
            if line == "":
                break
            elif line.startswith("Content-Length:"):
                pair = line.split()
                size = int(pair[1])
        # got a size?
        if not size:
            raise IOError("multi: no size found!")
        else:
            return size

    def _reset_frame_time(self):
        self._sum_frame_time = 0.0
        self._num_frame_time = 0
        self._last_get = time.time()

    def _update_frame_time(self):
        t = time.time()
        frame_time = t - self._last_get
        self._last_get = t
        self._sum_frame_time += frame_time
        self._num_frame_time += 1
        if self._num_frame_time > 10:
            fps = self._num_frame_time / self._sum_frame_time
            self._client.updateFPS.emit(fps)
            self._reset_frame_time()


class CamClient(QObject):
    """Capture a stream of jpeg images from a camera using mjpeg-streamer."""

    jpegData = pyqtSignal(object)
    raisedError = pyqtSignal(object)
    updateFPS = pyqtSignal(float)

    def __init__(self, url, retry_delay=5.0):
        """Access camera with given streaming URL."""
        super().__init__()
        self._url = url
        self._retry_delay = retry_delay
        self._thread = None

    def get_url(self):
        """Return streaming URL."""
        return self._url

    def get_retry_delay(self):
        """Return number of seconds to delay a retry."""
        return self._retry_delay

    def start(self):
        """Start capturing data."""
        self._thread = CamWorker(self)
        self._thread.start()

    def stop(self):
        """Cooperatively stop worker thread."""
        self._thread.stop()
        self._thread.wait()
        self._thread = None


if __name__ == "__main__":
    from PyQt5.QtCore import QCoreApplication
    import sys

    app = QCoreApplication(sys.argv)
    cc = CamClient(url="http://octopi.local:8080/?action=stream")
    start = time.time()

    def _check_end():
        if time.time() - start > 10:
            print("STOP")
            cc.stop()
            print("QUIT")
            app.quit()

    def _error(msg):
        print("FAILED:", msg)
        _check_end()

    def _data(jpeg):
        print("DATA:", len(jpeg))
        _check_end()

    def _fps(fps):
        print("FPS: %8.3f" % fps)

    cc.jpegData.connect(_data)
    cc.raisedError.connect(_error)
    cc.updateFPS.connect(_fps)
    cc.start()
    sys.exit(app.exec_())
