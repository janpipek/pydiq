[![Latest Version](https://img.shields.io/pypi/v/pydiq.svg)](https://pypi.python.org/pypi/pydiq/)
[![License](https://img.shields.io/pypi/l/pydiq.svg)](https://pypi.python.org/pypi/pydiq/)
[![DOI](https://zenodo.org/badge/3862/janpipek/pydiq.png)](http://dx.doi.org/10.5281/zenodo.11480)

pydiq
=====
Simple open-source multi-platform DICOM browser/viewer in Python and Qt.

**NOTE** This project has not been much updated for a long time. Currently, I just vibe-coded some updates to travel from 2019 to 2026 with hopefully more stable app and more formats understood.

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

* Python 3.10+
* qtpy + PySide6
* pydicom (3+)
* pillow, pylibjpeg-openjpeg and python-gdcm to read compressed images
  (JPEG, JPEG-LS, JPEG 2000)

Tested on Linux and Windows.

Installation
------------
The easiest way is `pip install pydiq`.

Usage
-----
```
Usage: pydiq [OPTIONS] [PATH]

Options:
  --help  Show this message and exit.
```

Supported images
----------------
The viewer does not ask what modality an image comes from; it tries to show
whatever pixel data it can read, and says why when it cannot. Grayscale and
colour (RGB, YBR, palette) images are shown, single-frame and multi-frame
alike - every image of a file is listed and can be picked.

**Shown, and tested on real files:**

| Modality | | Notes |
| --- | --- | --- |
| CT | Computed tomography | Values in Hounsfield units |
| MR | Magnetic resonance | |
| CR | Computed radiography | |
| NM | Nuclear medicine | Frames may be times or detectors, not slices |
| US | Ultrasound | Colour and cine loops; no position, see below |
| OT | Other, mostly secondary captures | Screenshots, scanned film, test patterns |
| SEG | Segmentation | Shown as the bare mask |
| RTDOSE | Radiotherapy dose | Raw values, see below |

**Probably shown, but untested:** DX, MG, IO, PX (projection X-ray), XA, RF
(angiography, fluoroscopy), PT (PET), ES (endoscopy), XC, OP (photography),
IVUS, OCT. These use the same kind of pixel data as the above, so there is
no reason for them not to work.

**Not shown, and never will be:** SR (reports), RTSTRUCT (contours), RTPLAN,
RTRECORD, PR, KO, REG, FID, DOC, and the waveform modalities (ECG, EPS, HD,
AU). These files hold no image at all. SM (whole-slide microscopy) is an
image, but a tiled gigapixel one that this viewer will not attempt.

Limitations
-----------
Images are assumed to have normal orientation (x, y, z);
ImageOrientationPatient is ignored. Multi-frame files are shown one image at
a time, and unless the file says where its individual frames are, they all
share the position of the file itself.

Ultrasound is measured in its own image regions rather than in patient
coordinates, so its images have no position and no physical size to report;
the viewer leaves those readouts empty rather than inventing them. Colour
images are shown as they are and cannot be windowed.

Dose grids are shown as stored values, not in Gray - DoseGridScaling is not
applied - and all of their frames report the position of the file, because
GridFrameOffsetVector is not read. Modality and VOI LUT sequences are
ignored; only WindowCenter/WindowWidth are used.

JPEG Extended with 12-bit samples cannot be decoded, as the only decoder
that handles it is GPL-licensed.
