from pathlib import Path
import pickle


class PFState:
    def __init__(self, filename: str, *args, **kwargs):
        if Path(filename).is_file():
            raise FileExistsError("PFState already exists")

        if not Path(filename).parent.is_dir():
            Path(filename).parent.mkdir(parents=True)
            (Path(filename).parent / "backup/").mkdir(parents=True)

        self.filename = filename
        for d in args:
            for k in d:
                setattr(self, k, d[k])
        for k in kwargs:
            setattr(self, k, kwargs[k])

        if not Path(self.raw_dir).is_dir():
            Path(self.raw_dir).mkdir(parents=True)

        if not Path(self.data_dir).is_dir():
            Path(self.data_dir).mkdir(parents=True)

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, v):
        if not isinstance(v, str):
            raise TypeError("Expected string")
        self._filename = v
        self._save()

    @property
    def raw_dir(self):
        return self._raw_dir

    @raw_dir.setter
    def raw_dir(self, v):
        if not isinstance(v, str):
            raise TypeError("Expected string")
        self._raw_dir = v
        self._save()

    @property
    def data_dir(self):
        return self._data_dir

    @data_dir.setter
    def data_dir(self, v):
        if not isinstance(v, str):
            raise TypeError("Expected string")
        self._data_dir = v
        self._save()

    @property
    def raw_files(self):
        return self._raw_files

    @raw_files.setter
    def raw_files(self, v):
        if not isinstance(v, list):
            raise TypeError("Expected list")
        self._raw_files = v
        self._save()

    @property
    def data_files(self):
        return self._data_files

    @data_files.setter
    def data_files(self, v):
        if not isinstance(v, list):
            raise TypeError("Expected list")
        self._data_files = v
        self._save()

    @property
    def vacations(self):
        return self._vacations

    @vacations.setter
    def vacations(self, v):
        if not isinstance(v, list):
            raise TypeError("Expected list")
        self._vacations = v
        self._save()

    @property
    def last_backup(self):
        return self._last_backup

    @last_backup.setter
    def last_backup(self, v):
        if not isinstance(v, str):
            raise TypeError("Expected string")
        self._last_backup = v
        self._save()

    @property
    def last_datadir_backup(self):
        return self._last_datadir_backup

    @last_datadir_backup.setter
    def last_datadir_backup(self, v):
        if not isinstance(v, str):
            raise TypeError("Expected string")
        self._last_datadir_backup = v
        self._save()

    def _save(self):
        pickle.dump(self, open(self.filename, "wb"))

    def __repr__(self):
        r = []
        for attr, value in self.__dict__.items():
            r.append(": ".join([str(attr), str(value)]))
        return ", ".join(r)


def pfstate(filename, *args, **kwargs):
    """pfstate function

    If it only receives a filename it return false or true depending if that file exists.
    If it receives anything else, it will return a PFState.
    """
    assert isinstance(filename, str), "filename is not string"

    if Path(filename).is_file():
        pfstate.state = pickle.load(open(filename, "rb"))
        if not isinstance(pfstate.state, PFState):
            raise TypeError("Unpickled object not of type PFState")
    elif args or kwargs:
        pfstate.state = PFState(filename, *args, **kwargs)
    else:
        pfstate.state = None

    return pfstate.state
