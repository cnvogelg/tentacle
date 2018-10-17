import sys
from PyQt5.QtWidgets import QApplication
import qdarkstyle
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


def run():
  logging.basicConfig(level=logging.DEBUG,
                      format=LOG_format, datefmt=LOG_datefmt)
  logging.info("Welcome to tentacle!")
  # read config
  cfg = read_config('tentacle.cfg')
  oc = OctoClient(cfg['url'], cfg['api_key'])
  # setup app
  app = QApplication(sys.argv)
  ex = App(oc)
  ex.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
  ex.show()
  ret = app.exec_()
  logging.shutdown()
  sys.exit(ret)


run()
