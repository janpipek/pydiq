import dicom
from collections import OrderedDict


def get_id(path):
    f = dicom.read_file(path, stop_before_pixels=True)
    return f.StudyInstanceUID, f.SeriesInstanceUID

# def
