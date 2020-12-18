from datetime import date
from pathlib import Path
import logging
import matplotlib.pyplot as plt
import pickle
import sys

from pfbudget.categories import Categories
from pfbudget.transactions import Transaction as Tr, TransactionError, Transactions
from pfbudget.parsers import Parser


def get_transactions(data_dir):
    dfs = dict()
    for df in Path(data_dir).iterdir():
        try:
            trs = Tr.read_transactions(df)
        except TransactionError as e:
            print(f"{e} -> datafile {df}")
            sys.exit(-2)
        dfs[df.name] = trs

    return dfs


def initialize(raw_dir, data_dir, restart=False):
    dfs = get_transactions(data_dir)
    if restart:
        rfs = dict()
        logging.debug("rewriting both .raw and .transactions pickles")
    else:
        try:
            rfs = pickle.load(open(".raw.pickle", "rb"))
            assert (
                type(rfs) is dict
            ), ".raw.pickle isn't a dictionary, so it could have been corrupted"
            logging.debug(".raw.pickle opened")
        except FileNotFoundError:
            rfs = dict()
            logging.debug("no .raw.pickle found")

    updated_trs, update = dict(), False
    prompt = " has been modified since last update. Do you want to update the data files? (Yes/Update/No)"
    for rf in Path(raw_dir).iterdir():
        if rf.name in rfs and rfs[rf.name][0] == rf.stat().st_mtime:
            logging.debug(f"{rf.name} hasn't been modified since last access")
        elif (
            rf.name not in rfs
            or (answer := input(f"{rf.name}" + prompt).lower()) == "yes"
        ):
            trs = Parser.parse_csv(rf)
            updated_trs[rf.name] = trs
            try:
                rfs[rf.name][0] = rf.stat().st_mtime
            except KeyError:
                rfs[rf.name] = [rf.stat().st_mtime, []]
            update = True
            logging.info(f"{rf.name} parsed")
        elif answer == "update":
            rfs[rf.name][0] = rf.stat().st_mtime
            update = True
        else:  # prompt = no
            update = True

    if update:
        for rf_name, updated_trs in updated_trs.items():
            filename_set = set(
                (t.date.year, f"{t.date.year}_{t.bank}.csv") for t in updated_trs
            )
            for year, filename in filename_set:
                trs = [t for t in updated_trs if t.date.year == year]
                if filename in dfs.keys():
                    new_trs = [tr for tr in trs if tr not in rfs[rf_name][1]]
                    rem_trs = [tr for tr in rfs[rf_name][1] if tr not in trs]

                    if new_trs:
                        dfs[filename].extend(new_trs)
                        dfs[filename].sort()

                    for rem in rem_trs:
                        dfs[filename].remove(rem)

                else:
                    dfs[filename] = trs

                Tr.write_transactions(Path(data_dir) / filename, dfs[filename])
                rfs[rf_name][1] = updated_trs
                logging.debug(f"{filename} written")

        pickle.dump(rfs, open(".raw.pickle", "wb"))
        logging.debug(".raw.pickle written to disk")

    if restart:
        for df in Path(data_dir).iterdir():
            if df.name not in dfs:
                dfs[df.name] = Tr.read_transactions(df)
                for t in dfs[df.name]:
                    t.category = ""

    return dfs
