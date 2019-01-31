"""Main module of Tentacle."""

import os
import sys
import argparse
import configparser
import logging

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QStyleFactory

from tentacle.client import OctoClient
from .app import App


LOG_FORMAT = '%(asctime)s %(levelname)-8s %(message)s'
LOG_DATEFMT = '%d.%m.%Y %H:%M:%S'


def read_config(cfg_paths, dump_config=None):
    """Read the config file."""
    cpa = configparser.ConfigParser()
    read_files = cpa.read(cfg_paths)
    logging.info("parsed config files: %r", read_files)
    if not read_files:
        logging.error("No config files found in: %r", cfg_paths)
        return None
    if dump_config:
        logging.info("writing config file: %s", dump_config)
        with open(dump_config, "w") as fobj:
            cpa.write(fobj)
    return cpa


def parse_args():
    """Parse the command line arguments."""
    apr = argparse.ArgumentParser()
    apr.add_argument("-d", "--debug", default=False, action='store_true',
                     help="enable debug output")
    apr.add_argument("-v", "--verbose", default=False, action='store_true',
                     help="enable more verbose output")
    apr.add_argument("-f", "--sim-file", default=None,
                     help="enable server simulation from file")
    apr.add_argument("-s", "--sim-scale", default=1.0, type=float,
                     help="set scale of simulation playback (1.0=realtime)")
    apr.add_argument("-D", "--fb-dev", default=None,
                     help="setup frame buffer device for Qt output")
    apr.add_argument("--dump-config", default=False,
                     help="save the current configuration into given file")
    return apr.parse_args()


def setup_logging(args):
    """Init logging output."""
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARN
    logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=LOG_DATEFMT)
    logging.info("Welcome to tentacle!")


def setup_qt(args, cfg):
    """Init PyQt output."""
    # set framebuffer output
    if args.fb_dev:
        fb_dev = args.fb_dev
    elif 'fb_dev' in cfg:
        fb_dev = cfg['fb_dev']
    else:
        fb_dev = '/dev/fb1'
    if not os.path.exists(fb_dev):
        logging.warning(
            "frame buffer device '%s' does not exist... ignoring!", fb_dev)
        return False
    os.environ['QT_QPA_PLATFORM'] = "linuxfb:fb=" + fb_dev
    return True


def setup_app(app, win, cfg):
    """Init App parameters."""
    # app
    font_family = cfg['font_family']
    font_size = int(cfg['font_size'])
    font = QFont(font_family, font_size)
    app.setFont(font)
    # window
    width = int(cfg['width'])
    height = int(cfg['height'])
    win.setFixedSize(width, height)
    # set style
    if 'style' in cfg:
        new_style_name = cfg['style']
        old_style = QApplication.style()
        old_style_name = old_style.objectName()
        logging.debug("old style: %s", old_style_name)
        if old_style_name != new_style_name:
            new_style = QStyleFactory.create(new_style_name)
            if new_style:
                QApplication.setStyle(new_style)
            else:
                logging.error("invalid style: %s. available: %s",
                              new_style_name,
                              QStyleFactory.keys())
    # dark mode?
    if 'dark' in cfg:
        dark = cfg['dark'].lower() in ('true', 'on')
    else:
        dark = False
    if dark:
        try:
            import qdarkstyle
            win.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        except ImportError:
            logging.error(
                "module 'qdarkstyle' not found! can't enable dark mode!")


def setup_octo_client(args, cfg):
    """Create OctoClient."""
    url = cfg['url']
    api_key = cfg['api_key']
    sim_file = args.sim_file
    sim_scale = args.sim_scale
    return OctoClient(url, api_key, sim_file, sim_scale)


def main():
    """Enter Main of Tentacle."""
    args = parse_args()
    # setup logging
    setup_logging(args)
    # read config
    cfg_paths = ['tentacle.cfg',
                 os.path.expanduser('~/.tentacle.cfg'),
                 '/etc/tentacle.cfg',
                 os.path.join(os.path.dirname(__file__), 'tentacle.cfg')]
    cfg = read_config(cfg_paths, args.dump_config)
    if not cfg:
        sys.exit(1)
    # setup octo client
    oc = setup_octo_client(args, cfg['octoprint'])
    # select qt frontend
    setup_qt(args, cfg['qt'])
    # setup app
    app = QApplication(sys.argv)
    ex = App(oc, cfg)
    setup_app(app, ex, cfg['app'])
    ex.show()
    ret = app.exec_()
    # shut down
    logging.shutdown()
    sys.exit(ret)


if __name__ == '__main__':
    main()
