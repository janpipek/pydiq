try:
    from PyQt4 import QtGui, QtCore
    from PyQt4.QtCore import pyqtSignal, pyqtSlot
except:
    from PySide import QtGui, QtCore
    from PySide.QtCore import Signal as pyqtSignal, Slot as pyqtSlot