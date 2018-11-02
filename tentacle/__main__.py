import sys
from PyQt5.QtWidgets import QApplication
import qdarkstyle
import argparse
import configparser
import logging

from .app import App
from .octo import OctoClient


LOG_format = '%(asctime)s %(levelname)-8s %(message)s'
LOG_datefmt = '%d.%m.%Y %H:%M:%S'


def read_config(cfg_file):
  p = configparser.ConfigParser()
  p.read(cfg_file)
  cfg = {}
  cfg['url'] = p['tentacle']['url']
  cfg['api_key'] = p['tentacle']['api_key']
  return cfg


def parse_args():
  ap = argparse.ArgumentParser()
  ap.add_argument("-d", "--debug", default=False, action='store_true',
                  help="enable debug output")
  ap.add_argument("-v", "--verbose", default=False, action='store_true',
                  help="enable more verbose output")
  ap.add_argument("-f", "--sim-file", default=None,
                  help="enable server simulation from file")
  ap.add_argument("-s", "--sim-scale", default=1.0, type=float,
                  help="set scale of simulation playback (1.0=realtime)")
  return ap.parse_args()


def setup_logging(args):
  if args.debug:
    level = logging.DEBUG
  elif args.verbose:
    level = logging.INFO
  else:
    level = logging.WARN
  logging.basicConfig(level=level, format=LOG_format, datefmt=LOG_datefmt)
  logging.info("Welcome to tentacle!")


def main():
  args = parse_args()
  # setup logging
  setup_logging(args)
  # read config
  cfg = read_config('tentacle.cfg')
  # setup octo client
  url = cfg['url']
  api_key = cfg['api_key']
  sim_file = args.sim_file
  sim_scale = args.sim_scale
  oc = OctoClient(url, api_key, sim_file, sim_scale)
  # setup app
  app = QApplication(sys.argv)
  ex = App(oc)
  ex.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
  ex.show()
  ret = app.exec_()
  # shut down
  logging.shutdown()
  sys.exit(ret)


if __name__ == '__main__':
  main()
