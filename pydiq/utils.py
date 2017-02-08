import dicom
import os


def get_id(path):
    f = dicom.read_file(path, stop_before_pixels=True)
    return f.StudyInstanceUID, f.SeriesInstanceUID


def is_dicom_file(path):
    """Fast way to check whether file is DICOM."""
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as f:
            return f.read(132).decode("ASCII")[-4:] == "DICM"
    except:
        return False


def dicom_files_in_dir(directory="."):
    """Full paths of all DICOM files in the directory."""
    directory = os.path.expanduser(directory)
    candidates = [os.path.join(directory, f) for f in sorted(os.listdir(directory))]
    return [f for f in candidates if is_dicom_file(f)]