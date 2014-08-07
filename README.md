pydiq
=====
Simple open-source DICOM browser/viewer in Python and Qt4.

Features
--------

* Easy (and fast) viewing of all images in a directory
* Mouse control of window center and width (as is Aeskulap Viewer)
* Proper measurement of Hounsfield units and position by mouse

To Do
-----

* Zooming
* MRI images support
* RT dose images support
* Integration of anonymizition features (see https://github.com/janpipek/anonymize_dicom )

Dependencies
------------

* PyQt4 / PySide
* pydicom

Limitations
-----------

Currently, the viewer supports only Computed Tomography (CT) images
with normal orientation (x, y, z) in one-slice-per-file format.