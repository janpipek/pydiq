try:
    import qtpy
except ImportError:
    print("Cannot load package qtpy. Please install it to run pydiq.")
    exit(-1)


# Import harakiri in the attempt to support both v0.9.x and v1.0.x of pydicom
# (the package changes name from dicom to pydicom)
try:
    import pydicom
except ImportError as e1:
    try:
        import dicom as pydicom
    except Exception as e:
        print("Cannot load package pydicom. Please install it to run pydiq.")
        exit(-1)