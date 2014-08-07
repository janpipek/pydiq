from __future__ import division

try:
    from PyQt4 import QtGui, QtCore
except:
    from PySide import QtGui, QtCore

import dicom
import numpy as np
import glob
import os.path

class TrackingLabel(QtGui.QLabel):
    def __init__(self, parent):
        QtGui.QLabel.__init__(self, parent)
        self.setMouseTracking(True)
        self.last_move_x = None
        self.last_move_y = None

    def mouseLeaveEvent(self, event):
        self.parent().mouse_x = -1
        self.parent().mouse_y = -1
        self.parent().update_coordinates()

    def mouseMoveEvent(self, event):
        self.parent().mouse_x = event.x()
        self.parent().mouse_y = event.y()
        self.parent().update_coordinates()

        if event.buttons() == QtCore.Qt.LeftButton:
            self.parent().w += event.y() - self.last_move_y
            self.parent().c += event.x() - self.last_move_x

            self.last_move_x = event.x()
            self.last_move_y = event.y()

    def mousePressEvent(self, event):
        self.last_move_x = event.x()
        self.last_move_y = event.y()

    def mouseReleaseEvent(self, event):
        self.last_move_x = None
        self.last_move_y = None

    def wheelEvent(self, event):
        file_list = self.parent().file_list
        if len(file_list.selectedItems()):
            index = file_list.row(file_list.selectedItems()[0])
        else:
            index = -1
        if event.delta() > 0:
            index -= 1
        else:
            index += 1

        if index >= file_list.count() or index == -2:
            index = file_list.count() - 1
        elif index < 0:
            index = 0

        file_list.setCurrentItem(file_list.item(index))

class Viewer(QtGui.QMainWindow):
    def __init__(self, file_name = None):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("pydiq - Python DICOM Viewer in Qt4")
        self.file = None

        self.high_hu = 2000
        self.low_hu = -1024
       
        self.pix_label = TrackingLabel(self)
        self.color_table = [QtGui.qRgb(i, i, i) for i in range(256)]
        self.setCentralWidget(self.pix_label)

        self.file_dock = QtGui.QDockWidget("Files", self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.file_dock)

        self.file_list = QtGui.QListWidget()
        self.file_list.itemSelectionChanged.connect(self.on_file_item_change)
        self.file_dock.setWidget(self.file_list)

        self.hu_label = QtGui.QLabel("No image")
        self.c_label = QtGui.QLabel("")
        self.w_label = QtGui.QLabel("")        
        self.x_label = QtGui.QLabel("")
        self.y_label = QtGui.QLabel("")
        self.z_label = QtGui.QLabel("")
        self.ij_label = QtGui.QLabel("")

        self.mouse_x = -1
        self.mouse_y = -1
       
        self.statusBar().addPermanentWidget(self.c_label)
        self.statusBar().addPermanentWidget(self.w_label)
        self.statusBar().addPermanentWidget(self.ij_label)
        self.statusBar().addPermanentWidget(self.x_label)
        self.statusBar().addPermanentWidget(self.y_label)
        self.statusBar().addPermanentWidget(self.z_label)
        self.statusBar().addPermanentWidget(self.hu_label)

        self.data = np.ndarray((512, 512), np.int8)
        self.update_cw()

        self.load_files(file_name)
        self.file_name = None

        self.build_menu()

    def open_directory(self):
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
        dialog.setViewMode(QtGui.QFileDialog.List)
        dialog.setOption(QtGui.QFileDialog.ShowDirsOnly, True)
        if dialog.exec_():
            self.load_files(os.path.join(str(dialog.selectedFiles()[0]), "*.dcm"))

    def build_menu(self): 

        self.file_menu = QtGui.QMenu('&File', self)
        self.file_menu.addAction('&Open directory', self.open_directory, QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction('&Quit', self.close, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)      

        self.view_menu = QtGui.QMenu('&View', self)
        # self.

        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.view_menu)

    def on_file_item_change(self):
        if not len(self.file_list.selectedItems()):
            self.file_name = None
        else:
            item = self.file_list.selectedItems()[0]
            # print item.text()
            self.file_name = str(item.toolTip())

    def load_files(self, glob_string):
        self.file_list.clear()
        if glob_string:
            self.files = sorted(glob.glob(glob_string))
        else:
            self.files = ()
        for file_name in self.files:
            item = QtGui.QListWidgetItem(os.path.basename(file_name))
            item.setToolTip(file_name)
            self.file_list.addItem(item)
        self.file_list.setMinimumWidth(self.file_list.sizeHintForColumn(0) + 20)
        self.file_name = None

    def create_qimage(self, low_hu = -1024, high_hu = 2000):
        data = (self.data - low_hu) / (high_hu - low_hu) * 256
        data[data < 0] = 0
        data[data > 255] = 255
        data = data.astype(np.int8)

        qimage = QtGui.QImage(data, data.shape[0], data.shape[1], QtGui.QImage.Format_Indexed8)
        return qimage  

    def get_coordinates(self, x, y):
        x = self.image_position[0] + self.pixel_spacing[0] * x
        y = self.image_position[1] + self.pixel_spacing[1] * y
        z = self.image_position[2]
        return x, y, z

    def update_coordinates(self):
        if self.file:
            x, y, z = self.get_coordinates(self.mouse_x, self.mouse_y)
            self.z_label.setText("z: %.2f" % z)
            if self.mouse_x >= 0 and self.mouse_y >= 0 and self.mouse_x < self.data.shape[0] and self.mouse_y < self.data.shape[1]:
                self.x_label.setText("x: %.2f" % x)
                self.y_label.setText("y: %.2f" % y)
                self.ij_label.setText("Pos: (%d,%d)" % (self.mouse_x, self.mouse_y))
                self.hu_label.setText("HU: %d" % int(self.data[self.mouse_y, self.mouse_x]))
                return
            else:
                self.hu_label.setText("HU: ???")     
        else:
            self.hu_label.setText("No image")
        self.ij_label.setText("")
        self.x_label.setText("")
        self.y_label.setText("")    

    @property
    def c(self):
        return (self.high_hu + self.low_hu) / 2

    @c.setter
    def c(self, value):
        original = self.c
        self.low_hu = self.low_hu + (value - original)
        self.high_hu = self.high_hu + (value - original)
        self.update_cw()

    @property
    def w(self):
        return self.high_hu - self.low_hu

    @w.setter
    def w(self, value):
        if value < 0:
            value = 0
        original = self.w
        self.low_hu = self.low_hu - (value - original) / 2
        self.high_hu = self.low_hu + value
        self.update_cw() 

    def update_cw(self):
        self.w_label.setText("W: %d" % int(self.w))
        self.c_label.setText("C: %d" % int(self.c))
        self.update_image()

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
        self.image = self.create_qimage(self.low_hu, self.high_hu)

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
            self.image_position = np.array([float(t) for t in self.file.ImagePositionPatient])
            self.pixel_spacing = np.array([float(t) for t in self.file.PixelSpacing])
            self.setWindowTitle("pydiq: " + self._file_name)
        except:
            self.file = None
            self.data = np.ndarray((512, 512), np.int8)
            self.update_image()
            self.setWindowTitle("pydiq: No image")
        self.update_coordinates()
        self.update_image()

