from __future__ import division

from PyQt4 import QtGui
import dicom
import numpy as np

class TrackingLabel(QtGui.QLabel):
    def __init__(self, parent, handler):
        QtGui.QLabel.__init__(self, parent)
        self.handler = handler

    def mouseMoveEvent(self, event):
        # print event.x, event.y()
        self.handler(event.x(), event.y())

class Viewer(QtGui.QMainWindow):
    def __init__(self, file_name = None):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("pydiq - Python DICOM Viewer in Qt4")
        self.file = None
        self.high_hu = 2000
        self.low_hu = -1024
        self.pix_label = TrackingLabel(self, self.on_mouse_move)
        self.color_table = [QtGui.qRgb(i, i, i) for i in range(256)]
        self.setCentralWidget(self.pix_label)

        self.pix_label.setMouseTracking(True)

        self.hu_label = QtGui.QLabel("No image")
        self.x_label = QtGui.QLabel("")
        self.y_label = QtGui.QLabel("")
        
        self.statusBar().addPermanentWidget(self.x_label)
        self.statusBar().addPermanentWidget(self.y_label)
        self.statusBar().addPermanentWidget(self.hu_label)

        self.file_name = file_name

    def create_qimage(self, input_file, low_hu = -1024, high_hu = 2000):
        data = (self.data - low_hu) / (high_hu - low_hu) * 256
        data[data < 0] = 0
        data[data > 255] = 255
        data = data.astype(np.int8)

        qimage = QtGui.QImage(data, data.shape[0], data.shape[1], QtGui.QImage.Format_Indexed8)
        return qimage        

    def on_mouse_move(self, x, y):
        if self.file:
            self.x_label.setText("x: %d" % x)
            self.y_label.setText("y: %d" % y)
            self.hu_label.setText("HU: %d" % int(self.data[y, x]))
        else:
            self.x_label.setText("")
            self.y_label.setText("")
            self.hu_label.setText("No image")

    @property
    def file_name(self):
        return self._file_name

    @property
    def image(self):
        try:
            return self._image
        except:
            return None

    def update_image(self):
        self.image = self.create_qimage(self.file, self.low_hu, self.high_hu)

    @image.setter
    def image(self, value):
        self._image = value
        self._image.setColorTable(self.color_table)
        pixmap = QtGui.QPixmap.fromImage(self._image)
        self.pix_label.setPixmap(pixmap)

    @file_name.setter
    def file_name(self, value):
        self._file_name = value
        try:
            self.file = dicom.read_file(self._file_name)
            self.data = self.file.RescaleSlope * self.file.pixel_array + self.file.RescaleIntercept
            self.setWindowTitle("pydiq: " + self._file_name)
        except:
            self.file = None
            self.data = np.ndarray((512, 512), np.int8)
            self.update_image()
            self.setWindowTitle("pydiq: No image")
        self.update_image()

