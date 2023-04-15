from dataclasses import dataclass


@dataclass
class Credentials:
    id: str
    key: str
    token: str = ""

    def valid(self) -> bool:
        return self.id and self.key
