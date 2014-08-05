#!/usr/bin/env python

import sys
import pydiq
from PyQt4 import QtGui, QtCore

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No file specified.")
        sys.exit(-1)
    file_name = sys.argv[1]

    app = QtGui.QApplication(sys.argv)

    viewer = pydiq.Viewer(file_name)
    viewer.show()

    sys.exit(app.exec_())
