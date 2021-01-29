from pathlib import Path
import csv
import datetime as dt
import pickle
import shutil

from .categories import Categories, Null, Travel, get_categories
from .transactions import (
    Transaction,
    load_transactions,
    read_transactions,
    write_transactions,
)
from .parsers import parse_data


def get_filename(t: Transaction):
    return "{}_{}.csv".format(t.year, t.bank)


class PFState:
    def __init__(self, filename, *args, **kwargs):
        if Path(filename).is_file():
            raise FileExistsError("PFState already exists")

        self.filename = filename
        for d in args:
            for k in d:
                setattr(self, k, d[k])
        for k in kwargs:
            setattr(self, k, kwargs[k])

        self._save()

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


def backup(state: PFState):
    transactions = load_transactions(state.data_dir)
    filename = (
        ".pfbudget/backups/"
        + "transactions_"
        + dt.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
        + ".csv"
    )
    write_transactions(Path(filename), transactions)

    state.last_backup = filename


def full_backup(state: PFState):
    filename = ".pfbudget/backups/" + dt.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    shutil.copytree(state.data_dir, Path(filename))

    state.last_datadir_backup = filename


def restore(state: PFState):
    if not state.last_datadir_backup:
        print("No data directory backup exists")
        return

    if Path(state.data_dir).is_dir():
        option = input(
            "A data directory already exists at {}/ . Are you sure you want to restore the last backup? (Y/N) ".format(
                state.data_dir
            )
        )
        if option.lower() == "y" or option.lower() == "yes":
            shutil.rmtree(state.data_dir)
            shutil.copytree(state.last_datadir_backup, state.data_dir)
        elif option.lower() == "n" or option.lower() == "no":
            return
        else:
            print("Invalid choice")
            return


def parser(state: PFState, raw_dir=None, data_dir=None):
    raw = Path(state.raw_dir) if not raw_dir else Path(raw_dir)
    dat = Path(state.data_dir) if not data_dir else Path(data_dir)

    new_transactions = {}
    for rf in raw.iterdir():
        if rf.name not in state.raw_files:
            new_transactions[rf.name] = parse_data(rf)
            state.raw_files.append(rf.name)

    # really, really bad optimized file append
    for _, transactions in new_transactions.items():
        for transaction in transactions:
            filename = get_filename(transaction)
            old = read_transactions(dat / filename)
            old.append(transaction)
            old.sort()
            write_transactions(dat / filename, old)
            if filename not in state.data_files:
                state.data_files.append(filename)

    state._save()  # append to list doesn't trigger setter


def auto_categorization(state: PFState, transactions: list) -> bool:
    null = Null()
    nulls = null.search_all(transactions)
    travel = Travel()
    travels = []
    missing = False

    for vacation in state.vacations:
        t = travel.search_all(transactions, vacation[0], vacation[1])
        travels.extend(t)

    for transaction in transactions:
        if not transaction.category:
            for category in [category() for category in Categories.get_categories()]:
                if category.search(transaction):
                    transaction.category = category.name

            if (
                transaction in travels
                and transaction.category not in travel.not_in_travel
            ):
                if transaction.category != travel.name:
                    transaction.category = travel.name

            if transaction in nulls:
                if transaction.category != null.name:
                    transaction.category = null.name

            if not transaction.category:
                missing = True

    return missing


def manual_categorization(state: PFState, transactions: list):
    for transaction in transactions:
        while not transaction.category:
            category = input(f"{transaction.desc()} category: ")
            if category == "quit":
                return
            if category not in get_categories():
                print("category doesn't exist")
                continue
            else:
                transaction.category = category
