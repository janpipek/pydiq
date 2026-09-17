from typing import Any, Iterator

from pydicom import Dataset, dcmread


class FileSet:
    def __init__(self, filenames: list[str]):
        self.filenames = filenames
        self._files: list["File"] | None = None
        self._studies: dict[str, "Study"] | None = None

    @property
    def studies(self) -> dict[str, "Study"]:
        if not self._studies:
            self._parse_tree()
        assert self._studies is not None
        return self._studies

    @property
    def files(self) -> list["File"]:
        if not self._files:
            self._files = [File(f) for f in self.filenames]
        return self._files

    def _parse_tree(self) -> None:
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

    def __iter__(self) -> Iterator["Study"]:
        return iter(self.studies.values())


class _MetaBase:
    def __init__(self, instance_uid: str):
        self.instance_uid = instance_uid

    def __eq__(self, other: object) -> bool:
        if type(other) != type(self):
            return False
        else:
            return self.instance_uid == other.instance_uid  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        return hash(self.instance_uid)

    @staticmethod
    def safe(f: "File", name: str) -> Any:
        return getattr(f.data, name, None)


class Study(_MetaBase):
    def __init__(
        self,
        instance_uid: str,
        description: str | None = None,
        number: int | None = None,
        date: str | None = None,
        time: str | None = None,
        comments: str | None = None,
    ):
        super(Study, self).__init__(instance_uid)
        self.description = description
        self.number = number
        self.date = date
        self.time = time
        self.comments = comments

        self.series: dict[str, "Series"] = {}

    def __str__(self) -> str:
        return "Study(\"{0}\", \"{1}\", {2} series)".format(self.instance_uid, self.description, len(self.series))

    def __iter__(self) -> Iterator["Series"]:
        return iter(self.series.values())

    @classmethod
    def from_file(cls, f: "File") -> "Study":
        def g(name: str) -> Any:
            return _MetaBase.safe(f, name)

        return Study(
            instance_uid=g("StudyInstanceUID"),
            description=g("StudyDescription"),
            number=g("StudyNumber"),
            date=g("StudyDate"),
            time=g("StudyTime"),
            comments=g("StudyComments")
        )

    def add_series(self, series: "Series") -> None:
        self.series[series.instance_uid] = series


class Series(_MetaBase):
    def __init__(
        self,
        instance_uid: str,
        description: str | None = None,
        number: int | None = None,
        date: str | None = None,
        time: str | None = None,
        study_instance_uid: str | None = None,
    ):
        super(Series, self).__init__(instance_uid)
        self.description = description
        self.number = number
        self.date = date
        self.time = time
        self.study_instance_uid = study_instance_uid

        self.files: dict[str, "File"] = {}

    @classmethod
    def from_file(cls, f: "File") -> "Series":
        def g(name: str) -> Any:
            return _MetaBase.safe(f, name)

        return Series(
            instance_uid=g("SeriesInstanceUID"),
            description=g("SeriesDescription"),
            number=g("SeriesNumber"),
            date=g("SeriesDate"),
            time=g("SeriesTime"),
            study_instance_uid=g("StudyInstanceUID")
        )

    def add_file(self, f: "File") -> None:
        self.files[f.path] = f

    def __str__(self) -> str:
        return "Series(\"{0}\", \"{1}\", {2} files)".format(self.instance_uid, self.description, len(self.files))

    def __iter__(self) -> Iterator["File"]:
        return iter(self.files.values())


class File:
    def __init__(self, path: str):
        self.path = path
        self._data: Dataset | None = None

    @property
    def data(self) -> Dataset:
        """Lazy evaluated DICOM file data."""
        if not self._data:
            self._data = dcmread(self.path)
        return self._data

    def __str__(self) -> str:
        return f"File({self.path})".format(self.path)

    @property
    def study_instance_uid(self) -> str | None:
        return _MetaBase.safe(self, "StudyInstanceUID")

    @property
    def series_instance_uid(self) -> str | None:
        return _MetaBase.safe(self, "SeriesInstanceUID")
