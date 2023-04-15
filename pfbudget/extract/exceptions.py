class ExtractError(Exception):
    pass


class BankError(ExtractError):
    pass


class CredentialsError(ExtractError):
    pass
