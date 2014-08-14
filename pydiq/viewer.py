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
        self.window = parent

    def mouseLeaveEvent(self, event):
        self.parent().mouse_x = -1
        self.parent().mouse_y = -1
        self.parent().update_coordinates()

    def mouseMoveEvent(self, event):
        self.window.mouse_x = event.x()
        self.window.mouse_y = event.y()
        self.window.update_coordinates()

        if event.buttons() == QtCore.Qt.LeftButton:
            self.window.w += event.y() - self.last_move_y
            self.window.c += event.x() - self.last_move_x

            self.last_move_x = event.x()
            self.last_move_y = event.y()

    def mousePressEvent(self, event):
        self.last_move_x = event.x()
        self.last_move_y = event.y()

    def mouseReleaseEvent(self, event):
        self.last_move_x = None
        self.last_move_y = None

    def wheelEvent(self, event):
        file_list = self.window.file_list
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
    def __init__(self, path = None):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("pydiq - Python DICOM Viewer in Qt4")
        self.file = None

        self.high_hu = 2000
        self.low_hu = -1024
       
        self.pix_label = TrackingLabel(self)
        self.pix_label.setCursor(QtCore.Qt.CrossCursor)
        self.color_table = [QtGui.qRgb(i, i, i) for i in range(256)]

        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidget(self.pix_label)

        # self.setCentralWidget(self.pix_label)
        self.setCentralWidget(scroll_area)

        self.file_dock = QtGui.QDockWidget("Files", self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.file_dock)

        self.file_list = QtGui.QListWidget()
        self.file_list.itemSelectionChanged.connect(self.on_file_item_change)
        self.file_dock.setWidget(self.file_list)

        self.hu_label = QtGui.QLabel("No image")
        self.c_label = QtGui.QLabel("")
        self.cw_label = QtGui.QLabel("")        
        self.x_label = QtGui.QLabel("")
        self.y_label = QtGui.QLabel("")
        self.z_label = QtGui.QLabel("")
        self.use_fractional_coordinates = True
        self.ij_label = QtGui.QLabel("")

        self._zoom = 1
        self.mouse_x = -1
        self.mouse_y = -1
       
        self.statusBar().addPermanentWidget(self.cw_label)
        self.statusBar().addPermanentWidget(self.ij_label)
        self.statusBar().addPermanentWidget(self.x_label)
        self.statusBar().addPermanentWidget(self.y_label)
        self.statusBar().addPermanentWidget(self.z_label)
        self.statusBar().addPermanentWidget(self.hu_label)

        self.data = np.ndarray((512, 512), np.int8)
        self.update_cw()

        if os.path.isfile(path):
            self.load_files(path)
        elif os.path.isdir(path):
            self.load_files(os.path.join(path, "*.dcm"))
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
        self.view_menu.addAction('Zoom In', self.increase_zoom, QtCore.Qt.CTRL + QtCore.Qt.Key_Plus)
        self.view_menu.addAction('Zoom Out', self.decrease_zoom, QtCore.Qt.CTRL + QtCore.Qt.Key_Minus)
        fullscreen = QtGui.QAction('&Full Screen', self)
        fullscreen.setCheckable(True)
        fullscreen.setShortcut(QtCore.Qt.Key_F11)
        fullscreen.toggled.connect(self.toggle_full_screen)
        self.view_menu.addAction(fullscreen)

        self.tools_menu = QtGui.QMenu("&Tools", self)
        self.tools_menu.addAction('&Show DICOM structure', self.show_structure, QtCore.Qt.Key_F2)

        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.view_menu)
        self.menuBar().addMenu(self.tools_menu)

    def show_structure(self):
        if self.file_name:
            f = dicom.read_file(self.file_name)
            print str(f)

    def toggle_full_screen(self, toggled):
        if toggled:
            self.setWindowState(QtCore.Qt.WindowFullScreen)
        else:
            self.setWindowState(QtCore.Qt.WindowNoState)

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
        if self.files:
            self.file_name = self.files[0]

    def create_qimage(self, low_hu = -1024, high_hu = 2000):
        data = (self.data - low_hu) / (high_hu - low_hu) * 256
        data[data < 0] = 0
        data[data > 255] = 255
        data = data.astype(np.int8)

        qimage = QtGui.QImage(data, data.shape[0], data.shape[1], QtGui.QImage.Format_Indexed8)
        return qimage  

    def get_coordinates(self, i, j):
        x = self.image_position[0] + self.pixel_spacing[0] * i
        y = self.image_position[1] + self.pixel_spacing[1] * j
        z = self.image_position[2]
        return x, y, z

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        self._zoom = value
        self.update_image()
        self.update_coordinates()

    def decrease_zoom(self):
        if self.zoom > 1:
            self.zoom -= 1

    def increase_zoom(self):
        self.zoom += 1

    @property
    def mouse_ij(self):
        '''Mouse position as voxel index in current DICOM slice.'''
        return self.mouse_y // self.zoom, self.mouse_x // self.zoom

    @property
    def mouse_xyz(self):
        '''Mouse position in DICOM coordinates.'''
        if self.use_fractional_coordinates:
            correction = (self.zoom - 1.) / (2. * self.zoom) # To get center of left top pixel in a zoom grid
            return self.get_coordinates(self.mouse_x / self.zoom - correction, self.mouse_y / self.zoom - correction)
        else:
            return self.get_coordinates(self.mouse_x // self.zoom, self.mouse_y // self.zoom)

    def update_coordinates(self):
        if self.file:
            x, y, z = self.mouse_xyz
            i, j = self.mouse_ij
            self.z_label.setText("z: %.2f" % z)
            if i >= 0 and j >= 0 and i < self.data.shape[0] and j < self.data.shape[1]:
                self.x_label.setText("x: %.2f" % x)
                self.y_label.setText("y: %.2f" % y)
                self.ij_label.setText("Pos: (%d, %d)" % self.mouse_ij)
                self.hu_label.setText("HU: %d" % int(self.data[i, j]))
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
        self.cw_label.setText("W: %d C: %d" % (int(self.w), int(self.c)))
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
        if self.zoom != 1:
            pixmap = pixmap.scaled(pixmap.width() * self.zoom,  pixmap.height() * self.zoom, QtCore.Qt.KeepAspectRatio)
        self.pix_label.setPixmap(pixmap)
        self.pix_label.resize(pixmap.width(), pixmap.height())

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

