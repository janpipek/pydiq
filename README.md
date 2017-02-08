[![Latest Version](https://pypip.in/version/pydiq/badge.svg)](https://pypi.python.org/pypi/pydiq/)
[![License](https://pypip.in/license/pydiq/badge.svg)](https://pypi.python.org/pypi/pydiq/)
[![DOI](https://zenodo.org/badge/3862/janpipek/pydiq.png)](http://dx.doi.org/10.5281/zenodo.11480)

pydiq
=====
Simple open-source multi-platform DICOM browser/viewer in Python and Qt4.

![Vertebrae](https://raw.githubusercontent.com/janpipek/pydiq/master/doc/vertebra.png "Vertebrae")

Features
--------

* Easy (and fast) viewing of all images in a directory
* Zooming (1:N and N:1)
* Mouse control of window center and width (as in Aeskulap Viewer)
* Proper measurement of Hounsfield units and position by mouse
* PNG image export

To Do
-----

* Better zooming
* Better MRI images support
* RT dose images support
* View in different planes (rectangular + others)
* Coordinate mapping (using translation and rotation matrix)
* Integration of anonymization features (see https://github.com/janpipek/anonymize_dicom )
* Information from the DICOM file in user-friendly display

Dependencies
------------

* qtpy (and therefore PyQt4 / PyQt5 / PySide)
* pydicom

Tested on Linux and Windows.

Installation
------------
The easiest way is `pip install pydiq`.

Limitations
-----------

Currently, the viewer supports only Computed Radiography (CR), Computed Tomography (CT) and
Magnetic Resonance Imaging (MRI) images with normal orientation (x, y, z)
in one-slice-per-file format.
