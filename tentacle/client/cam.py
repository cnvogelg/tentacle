"""Camera Client for MJPEG streaming from mjpeg-streamer server."""

import io
import logging
import time

import requests
from PyQt5.QtCore import QObject, pyqtSignal, QThread


class IterStream(io.RawIOBase):
    """Convert a stream of byte blobs to an bytes io."""

    def __init__(self, iterable):
        """Create stream."""
        super().__init__()
        self.leftover = None
        self.iterable = iterable

    def readable(self):
        """Stream is readable."""
        return True

    def readinto(self, b):
        """Fill a buffer."""
        try:
            length = len(b)
            chunk = self.leftover or next(self.iterable)
            output, self.leftover = chunk[:length], chunk[length:]
            b[:len(output)] = output
            return len(output)
        except StopIteration:
            return 0


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
        url = self._client.get_url()
        retry_delay = self._client.get_retry_delay()
        while self._stay:
            logging.info("cam: request for '%s'", url)
            r = None
            try:
                r = requests.get(url, stream=True)
                if r.status_code != 200:
                    logging.error("cam: invalid status: %d", r.status)
                else:
                    ct = r.headers['Content-Type']
                    prefix = "multipart/x-mixed-replace;boundary="
                    if not ct.startswith(prefix):
                        logging.error("cam: wrong content type: %s", ct)
                    else:
                        boundary = "--" + ct[len(prefix):]
                        # data loop
                        istr = IterStream(r.iter_content())
                        reader = io.BufferedReader(istr, buffer_size=1024)
                        self._data_loop(reader, boundary)
                        logging.debug("cam: end request")
                        return
            except IOError as e:
                logging.error("cam: error: %s", str(e))
                self._client.raisedError.emit(e)
            finally:
                if r:
                    r.close()
            # retry
            logging.debug("cam: retry delay: %s", retry_delay)
            time.sleep(retry_delay)

    def _data_loop(self, reader, boundary):
        while self._stay:
            size = self._parse_header(reader, boundary)
            jpeg_data = reader.read(size)
            self._client.jpegData.emit(jpeg_data)

    def _parse_header(self, reader, boundary):
        # parse header
        def get():
            return reader.readline().strip().decode("utf-8")
        # expect boundary first
        while True:
            line = get()
            if line == "":
                pass
            elif line == boundary:
                break
            else:
                raise IOError("multi: boundary not found! got: %s" % line)
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


class CamClient(QObject):
    """Capture a stream of jpeg images from a camera using mjpeg-streamer."""

    jpegData = pyqtSignal(object)
    raisedError = pyqtSignal(object)

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

    cc.jpegData.connect(_data)
    cc.raisedError.connect(_error)
    cc.start()
    sys.exit(app.exec_())
