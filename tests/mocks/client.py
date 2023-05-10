from pfbudget.db.client import Client
from pfbudget.db.model import Base


class MockClient(Client):
    def __init__(self):
        url = "sqlite://"
        super().__init__(
            url, execution_options={"schema_translate_map": {"pfbudget": None}}
        )
        Base.metadata.create_all(self.engine)
