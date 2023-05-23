import datetime as dt

from pfbudget.db.client import Client
from pfbudget.db.model import Base, Nordigen


class MockClient(Client):
    now = dt.datetime.now()

    def __init__(self):
        url = "sqlite://"
        super().__init__(
            url, execution_options={"schema_translate_map": {"pfbudget": None}}
        )
        Base.metadata.create_all(self.engine)

        self.insert(
            [
                Nordigen("access", "token#1", self.now + dt.timedelta(days=1)),
                Nordigen("refresh", "token#2", self.now + dt.timedelta(days=30)),
            ]
        )
