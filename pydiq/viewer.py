from __future__ import division

from qtpy import QtWidgets, QtCore

import dicom
import numpy as np
import os.path

from .dicom_data import DicomData
from .dicom_widget import DicomWidget
from .utils import dicom_files_in_dir


class TrackingLabel(QtWidgets.QLabel):
    def __init__(self, parent):
        super(TrackingLabel, self).__init__(parent)
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
            self.window.window_width += event.y() - self.last_move_y
            self.window.window_center += event.x() - self.last_move_x

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


class Viewer(QtWidgets.QMainWindow):
    def __init__(self, path = None):
        super(Viewer, self).__init__()
        self.setWindowTitle("pydiq - Python DICOM Viewer in Qt4")
        self.file = None

        self.high_hu = 2000
        self.low_hu = -1024
       
        # self.pix_label = TrackingLabel(self)
        self.pix_label = DicomWidget(None)

        # self.pix_label.setCursor(QtCore.Qt.CrossCursor)
        # self.color_table = [QtWidgets.qRgb(i, i, i) for i in range(256)]

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(self.pix_label)

        # self.setCentralWidget(self.pix_label)
        self.setCentralWidget(scroll_area)

        self.file_dock = QtWidgets.QDockWidget("Files", self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.file_dock)

        self.file_list = QtWidgets.QListWidget()
        self.file_list.itemSelectionChanged.connect(self.on_file_item_change)
        self.file_dock.setWidget(self.file_list)

        self.hu_label = QtWidgets.QLabel("No image")
        self.c_label = QtWidgets.QLabel("")
        self.cw_label = QtWidgets.QLabel("")        
        self.x_label = QtWidgets.QLabel("")
        self.y_label = QtWidgets.QLabel("")
        self.z_label = QtWidgets.QLabel("")
        self.use_fractional_coordinates = True
        self.ij_label = QtWidgets.QLabel("")

        self._zoom_level = 1
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
            self.load_files([path])
        elif os.path.isdir(path):
            self.load_files(dicom_files_in_dir(path))
        self.build_menu()

    def open_directory(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        dialog.setViewMode(QtWidgets.QFileDialog.List)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        if dialog.exec_():
            directory = str(dialog.selectedFiles()[0])
            self.load_files(dicom_files_in_dir(directory))

    def export_image(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save file",
            os.path.expanduser("~/dicom-export.png"),
            "PNG images (*.png)"
        )
        if file_name:
            self.pixmap_label._image.save(file_name)

    def build_menu(self): 
        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Open directory', self.open_directory, QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction('&Export image', self.export_image, QtCore.Qt.CTRL + QtCore.Qt.Key_S)
        self.file_menu.addAction('&Quit', self.close, QtCore.Qt.CTRL + QtCore.Qt.Key_Q)      

        self.view_menu = QtWidgets.QMenu('&View', self)
        self.view_menu.addAction('Zoom In', self.pix_label.increase_zoom, QtCore.Qt.CTRL + QtCore.Qt.Key_Plus)
        self.view_menu.addAction('Zoom Out', self.pix_label.decrease_zoom, QtCore.Qt.CTRL + QtCore.Qt.Key_Minus)
        self.view_menu.addAction('Zoom 1:1', self.pix_label.reset_zoom, QtCore.Qt.CTRL + QtCore.Qt.Key_0)
        fullscreen = QtWidgets.QAction('&Full Screen', self)
        fullscreen.setCheckable(True)
        fullscreen.setShortcut(QtCore.Qt.Key_F11)
        fullscreen.toggled.connect(self.toggle_full_screen)
        self.view_menu.addAction(fullscreen)

        self.tools_menu = QtWidgets.QMenu("&Tools", self)
        self.tools_menu.addAction('&Show DICOM structure', self.show_structure, QtCore.Qt.Key_F2)

        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.view_menu)
        self.menuBar().addMenu(self.tools_menu)

    def show_structure(self):
        if self.file_name:
            f = dicom.read_file(self.file_name)
            print(str(f))

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

    def load_files(self, files):
        self.file_list.clear()
        self.files = files
        for file_name in self.files:
            item = QtWidgets.QListWidgetItem(os.path.basename(file_name))
            item.setToolTip(file_name)
            self.file_list.addItem(item)
        self.file_list.setMinimumWidth(self.file_list.sizeHintForColumn(0) + 20)
        if self.files:
            self.file_name = self.files[0]

    def get_coordinates(self, i, j):
        x = self.image_position[0] + self.pixel_spacing[0] * i
        y = self.image_position[1] + self.pixel_spacing[1] * j
        z = self.image_position[2]
        return x, y, z

    @property
    def mouse_ij(self):
        '''Mouse position as voxel index in current DICOM slice.'''
        return self.mouse_y // self.zoom_factor, self.mouse_x // self.zoom_factor

    @property
    def mouse_xyz(self):
        '''Mouse position in DICOM coordinates.'''
        if self.use_fractional_coordinates:
            # TODO: Fix for zoom out
            correction = (self.zoom_factor - 1.) / (2. * self.zoom_factor) # To get center of left top pixel in a zoom grid
            return self.get_coordinates(self.mouse_x / self.zoom_factor - correction, self.mouse_y / self.zoom_factor - correction)
        else:
            return self.get_coordinates(self.mouse_x // self.zoom_factor, self.mouse_y // self.zoom_factor)

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

    def update_cw(self):
        # self.cw_label.setText("W: %d C: %d" % (int(self.pix_label.w), int(self.pix_label.c)))
        # self.update_image()
        pass

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, value):
        try:
            self._file_name = value
            data = DicomData.from_files([self._file_name])
            self.pix_label.data = data
            self.setWindowTitle("pydiq: " + self._file_name)
        except BaseException as exc:
            print(exc)
            self.pix_label.data = None
            self.setWindowTitle("pydiq: No image")

            # try:
            #     self.image_position = np.array([float(t) for t in self.file.ImagePositionPatient])
            # except:
            #     self.image_position = np.array([1., 1., 1.])
            # self.pixel_spacing = np.array([float(t) for t in self.file.PixelSpacing])


