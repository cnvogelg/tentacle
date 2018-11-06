# Install missing PyQtChart on Raspberry Pi

Raspbian: Raspbian GNU/Linux 9.4 (stretch) (October 2018)

While recent versions of Raspbian ship Qt5 and PyQt5 packages, some extensions
namely PyQtChart are missing. You can't simply install them with `pip3 install`
since PyPi does currently not host Raspbian builds...

So for now you have to build the package manually...

## Manual Build of PyQtChart

This instruction here is based on this [discussion][1]

First install the required dev tools

```
$ sudo apt-get install python3-pyqt5 pyqt5-dev pyqt5-dev-tools qt5-qmake
```

Build and install the native QtCharts module

```
$ git clone git://code.qt.io/qt/qtcharts.git -b 5.7
$ cd qtcharts
$ qmake -r
$ make
$ sudo make install
```

Build and install the PyQtCharts module

```
$ wget https://datapacket.dl.sourceforge.net/project/pyqt/PyQtChart/PyQtChart-5.7/PyQtChart_gpl-5.7.tar.gz
$ tar zxvf PyQtChart_gpl-5.7.tar.gz
$ cd PyQtChart_gpl-5.7
$ python3 configure.py --qtchart-version=2.1.2 --verbose
$ make
$ sudo make install
```

Done!

[1]: https://github.com/mu-editor/mu/issues/441
