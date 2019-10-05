from dicom.filereader import read_file


class FileSet:
    def __init__(self, filenames):
        self.filenames = filenames
        self._files = None
        self._studies = None

    @property
    def studies(self):
        if not self._studies:
            self._parse_tree()
        return self._studies

    @property
    def files(self):
        if not self._files:
            self._files = [File(f) for f in self.filenames]
        return self._files

    def _parse_tree(self):
        self._studies = {}

        for f in self.files:
            series = Series.from_file(f)
            study = Study.from_file(f)

            if study.instance_uid not in self._studies:
                self._studies[study.instance_uid] = study
            study = self._studies[study.instance_uid]

            if series.instance_uid not in study.series:
                study.series[series.instance_uid] = series
            series = study.series[series.instance_uid]

            series.add_file(f)

    def __iter__(self):
        return iter(self.studies.values())


class _MetaBase:
    def __init__(self, instance_uid):
        self.instance_uid = instance_uid

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        else:
            return self.instance_uid == other.instance_uid

    def __hash__(self):
        return hash(self.instance_uid)

    @staticmethod
    def safe(f, name):
        return getattr(f.data, name, None)


class Study(_MetaBase):
    def __init__(self, instance_uid, description=None, number=None, date=None, time=None, comments=None):
        super(Study, self).__init__(instance_uid)
        self.description = description
        self.number = number
        self.date = date
        self.time = time
        self.comments = comments

        self.series = {}

    def __str__(self):
        return "Study(\"{0}\", \"{1}\", {2} series)".format(self.instance_uid, self.description, len(self.series))

    def __iter__(self):
        return iter(self.series.values())

    @classmethod
    def from_file(cls, f):
        def g(name):
            return _MetaBase.safe(f, name)

        return Study(
            instance_uid=g("StudyInstanceUID"),
            description=g("StudyDescription"),
            number=g("StudyNumber"),
            date=g("StudyDate"),
            time=g("StudyTime"),
            comments=g("StudyComments")
        )

    def add_series(self, series):
        self.series[series.instance_uid] = series


class Series(_MetaBase):
    def __init__(self, instance_uid, description=None, number=None, date=None, time=None, study_instance_uid=None):
        super(Series, self).__init__(instance_uid)
        self.description = description
        self.number = number
        self.date = date
        self.time = time
        self.study_instance_uid = study_instance_uid

        self.files = {}

    @classmethod
    def from_file(cls, f):
        def g(name):
            return _MetaBase.safe(f, name)

        return Series(
            instance_uid=g("SeriesInstanceUID"),
            description=g("SeriesDescription"),
            number=g("SeriesNumber"),
            date=g("SeriesDate"),
            time=g("SeriesTime"),
            study_instance_uid=g("StudyInstanceUID")
        )

    def add_file(self, f: "File"):
        self.files[f.path] = f

    def __str__(self):
        return "Series(\"{0}\", \"{1}\", {2} files)".format(self.instance_uid, self.description, len(self.files))

    def __iter__(self):
        return iter(self.files.values())


class File:
    def __init__(self, path: str):
        self.path = path
        self._data = None

    @property
    def data(self):
        """Lazy evaluated DICOM file data."""
        if not self._data:
            self._data = read_file(self.path)
        return self._data

    def __str__(self):
        return f"File({self.path})".format(self.path)

    @property
    def study_instance_uid(self):
        return _MetaBase.safe(self, "StudyInstanceUID")

    @property
    def series_instance_uid(self):
        return _MetaBase.safe(self, "SeriesInstanceUID")
